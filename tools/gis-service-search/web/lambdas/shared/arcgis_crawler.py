"""ArcGIS REST catalog discovery, local search, and source classification."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time
from typing import Any

import arcgis_client

ROOT_ERROR_TYPES_AS_UNREACHABLE = ("unreachable", "connection_error", "timeout")
FOLDER_CAP = 50

MESSAGES = {
    "tls_error": "This server security certificate could not be verified.",
    "unreachable": "This server could not be reached.",
    "directory_forbidden": "This server has directory browsing disabled.",
    "waf_or_nonjson": "This server returned an unexpected response, possibly blocking automated requests.",
    "token_required": "This service requires an access token we do not have.",
    "malformed_root": "This URL does not look like an ArcGIS REST services catalog.",
    "self_throttled": "This server is rate-limiting our requests.",
    "time_budget": "This catalog is large and was not fully searched in the time available.",
}


@dataclass
class DiscoveryResult:
    documents: list[dict]
    services_scanned: int
    services_total: int
    truncated: bool
    terminal_error: str | None


def tokenize(query: str) -> list[str]:
    """Return lowercase whitespace-delimited query tokens."""
    return query.lower().split()


def matches_document(doc: dict, tokens: list[str], full_query: str, match_mode: str) -> bool:
    """Return whether an ArcGIS service or layer document matches the query."""
    haystack = f"{doc.get('title', '')} {doc.get('description') or ''}".lower()

    if match_mode == "phrase":
        return full_query.lower() in haystack
    if match_mode == "all":
        return all(token in haystack for token in tokens)
    return any(token in haystack for token in tokens)


def search_documents(documents: list[dict], query: str, match_mode: str) -> list[dict]:
    """Search crawled documents and return frontend-ready result dictionaries."""
    tokens = tokenize(query)
    return [
        {
            "title": doc["title"],
            "link": doc["url"],
            "snippet": doc.get("description"),
        }
        for doc in documents
        if matches_document(doc, tokens, query, match_mode)
    ]


def discover_tree(root_url: str, budget_seconds: float, per_host_concurrency: int = 4) -> DiscoveryResult:
    """Walk an ArcGIS REST service catalog one folder level deep."""
    started_at = time.monotonic()
    root_result = arcgis_client.fetch_json(arcgis_client.build_url(root_url))
    terminal_error = _classify_root_result(root_result)
    if terminal_error:
        return DiscoveryResult(
            documents=[],
            services_scanned=0,
            services_total=0,
            truncated=False,
            terminal_error=terminal_error,
        )

    root_body = root_result.json_body or {}
    target_list = _build_target_list(root_url, root_body)
    services_total = len(target_list)
    documents: list[dict] = []
    services_scanned = 0
    attempted_count = 0
    self_throttled_count = 0
    truncated = False
    batch_size = max(1, per_host_concurrency)

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        for index in range(0, services_total, batch_size):
            if time.monotonic() - started_at >= budget_seconds:
                truncated = True
                break

            batch = target_list[index : index + batch_size]
            for result in executor.map(lambda target: _fetch_service_documents(root_url, target), batch):
                services_scanned += 1
                attempted_count += 1
                if result["error_type"] == "self_throttled":
                    self_throttled_count += 1
                documents.extend(result["documents"])

    final_error = None
    # Escalate source-level throttling only when a clear majority of attempted
    # service fetches were exhausted 429/503 retries, avoiding overreacting to
    # one or two transient busy responses in a large catalog.
    if attempted_count >= 3 and self_throttled_count / attempted_count > 0.5:
        final_error = "self_throttled"

    return DiscoveryResult(
        documents=documents,
        services_scanned=services_scanned,
        services_total=services_total,
        truncated=truncated,
        terminal_error=final_error,
    )


def crawl_and_classify(source_url: str, query: str, match_mode: str, budget_seconds: float) -> dict:
    """Discover, search, and classify one ArcGIS source result."""
    started_at = time.monotonic()
    discovery_result = discover_tree(source_url, budget_seconds)
    results = search_documents(discovery_result.documents, query, match_mode)
    state, reason_code = _classify_source(discovery_result, len(results))
    visible_results = results if state in ("success", "success_empty", "partial") else []

    return {
        "source": source_url,
        "state": state,
        "reasonCode": reason_code,
        "message": MESSAGES.get(reason_code),
        "results": visible_results,
        "totalResults": len(visible_results),
        "servicesScanned": discovery_result.services_scanned,
        "servicesTotal": discovery_result.services_total,
        "truncated": discovery_result.truncated,
        "retrying": False,
        "elapsedSeconds": round(time.monotonic() - started_at, 1),
    }


def _classify_root_result(root_result: arcgis_client.FetchResult) -> str | None:
    body = root_result.json_body
    if body is not None:
        error_body = body.get("error", {})
        error_code = error_body.get("code") if isinstance(error_body, dict) else None
        if error_code is not None:
            return "token_required" if error_code in (498, 499) else "unreachable"

    if root_result.error_type == "tls_error":
        return "tls_error"
    if root_result.error_type in ROOT_ERROR_TYPES_AS_UNREACHABLE:
        return "unreachable"
    if root_result.error_type == "self_throttled":
        return "self_throttled"
    if root_result.error_type == "non_json":
        return "non_json"
    if root_result.error_type == "http_error":
        return "directory_forbidden" if root_result.status_code == 403 else "unreachable"
    if "folders" not in (body or {}) and "services" not in (body or {}):
        return "malformed_root"
    return None


def _build_target_list(root_url: str, root_body: dict) -> list[tuple[str | None, str, str]]:
    # dict.get(key, default) only substitutes default for a MISSING key -- some
    # real ArcGIS servers (e.g. tiles.arcgis.com) return an explicit JSON null
    # for "folders"/"services" rather than omitting the key or using [], so
    # `.get(key) or []` is required here, not `.get(key, [])`.
    targets = _service_targets(None, root_body.get("services") or [])

    for folder in (root_body.get("folders") or [])[:FOLDER_CAP]:
        folder_result = arcgis_client.fetch_json(arcgis_client.build_url(root_url, folder))
        if folder_result.error_type != "ok":
            continue
        targets.extend(_service_targets(str(folder), (folder_result.json_body or {}).get("services") or []))

    return targets


def _service_targets(folder: str | None, services: Any) -> list[tuple[str | None, str, str]]:
    targets = []
    if not isinstance(services, list):
        return targets

    for service in services:
        if not isinstance(service, dict):
            continue
        name = service.get("name")
        service_type = service.get("type")
        if name is None or service_type is None:
            continue
        targets.append((folder, str(name), str(service_type)))
    return targets


def _fetch_service_documents(root_url: str, target: tuple[str | None, str, str]) -> dict:
    folder, name, service_type = target
    if folder:
        service_url = arcgis_client.build_url(root_url, folder, name, service_type)
    else:
        service_url = arcgis_client.build_url(root_url, name, service_type)

    service_url_without_query = service_url.split("?", 1)[0]
    result = arcgis_client.fetch_json(service_url)
    if result.error_type != "ok":
        return {"error_type": result.error_type, "documents": []}

    body = result.json_body or {}
    display_name = f"{folder}/{name}" if folder else name
    documents = [
        {
            "title": f"{service_type}: {display_name}",
            "url": service_url_without_query,
            "kind": "service",
            "description": body.get("description") or body.get("serviceDescription"),
        }
    ]

    for layer in body.get("layers") or []:
        if not isinstance(layer, dict):
            continue
        layer_id = layer.get("id")
        layer_name = layer.get("name")
        documents.append(
            {
                "title": f"Layer: {layer_name} (ID: {layer_id})",
                "url": f"{service_url_without_query}/{layer_id}",
                "kind": "layer",
                "description": layer.get("description"),
            }
        )

    return {"error_type": result.error_type, "documents": documents}


def _classify_source(discovery_result: DiscoveryResult, result_count: int) -> tuple[str, str | None]:
    terminal_error = discovery_result.terminal_error
    if terminal_error == "tls_error":
        return "try_google", "tls_error"
    if terminal_error == "unreachable":
        return "try_google", "unreachable"
    if terminal_error == "directory_forbidden":
        return "try_google", "directory_forbidden"
    if terminal_error == "non_json":
        return "try_google", "waf_or_nonjson"
    if terminal_error == "token_required":
        return "contact_admin", "token_required"
    if terminal_error == "malformed_root":
        return "check_url", "malformed_root"
    if terminal_error == "self_throttled" and discovery_result.documents:
        return "partial", "self_throttled"
    if terminal_error == "self_throttled":
        return "try_google", "self_throttled"
    if discovery_result.truncated:
        return "partial", "time_budget"
    if result_count > 0:
        return "success", None
    return "success_empty", None
