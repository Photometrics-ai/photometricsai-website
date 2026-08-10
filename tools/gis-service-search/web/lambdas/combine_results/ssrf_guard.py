"""Host safety checks for crawler outbound requests.

This resolve-then-check approach has a small DNS-rebinding TOCTOU gap: a host
could resolve to a safe public IP here, then re-resolve to a different IP when
the actual connection is made. Pinned-IP connection logic is not worth the
complexity for this tool's threat model. Redirect targets are re-validated
separately in arcgis_client.py because each redirect is a second, later
hostname resolution with the same gap.
"""

import ipaddress
import socket


def is_safe_host(hostname) -> bool:
    """Return True only if every resolved address is public routable space."""
    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except Exception:  # noqa: BLE001 -- weird host input or DNS failure is unsafe
        return False

    if not addrinfos:
        return False

    try:
        return all(_is_safe_address(info[4][0]) for info in addrinfos)
    except Exception:  # noqa: BLE001 -- malformed getaddrinfo data is unsafe
        return False


def _is_safe_address(raw_address: str) -> bool:
    address = ipaddress.ip_address(raw_address)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped

    blocked = (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )
    return not blocked
