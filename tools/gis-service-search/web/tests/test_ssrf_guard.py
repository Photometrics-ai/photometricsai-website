"""Tests for SSRF host validation using fake DNS only."""

import socket

import pytest

import ssrf_guard


def _addrinfo(address):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sockaddr = (address, 0, 0, 0) if family == socket.AF_INET6 else (address, 0)
    return (family, socket.SOCK_STREAM, 6, "", sockaddr)


def _patch_resolution(monkeypatch, addresses):
    monkeypatch.setattr(socket, "getaddrinfo", lambda hostname, port: [_addrinfo(addr) for addr in addresses])


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.1.2.3",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.10",
        "169.254.1.1",
        "169.254.169.254",
        "::1",
        "fc00::1",
        "fe80::1",
        "::ffff:169.254.169.254",
        "0.0.0.0",
    ],
)
def test_blocks_non_public_addresses(monkeypatch, address):
    _patch_resolution(monkeypatch, [address])
    assert ssrf_guard.is_safe_host("example.test") is False


def test_allows_public_address(monkeypatch):
    _patch_resolution(monkeypatch, ["8.8.8.8"])
    assert ssrf_guard.is_safe_host("dns.google") is True


def test_resolution_failure_is_denied(monkeypatch):
    def fail_resolution(hostname, port):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fail_resolution)
    assert ssrf_guard.is_safe_host("missing.example") is False


def test_empty_resolution_is_denied(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda hostname, port: [])
    assert ssrf_guard.is_safe_host("empty.example") is False


def test_any_unsafe_address_denies_whole_host(monkeypatch):
    _patch_resolution(monkeypatch, ["8.8.8.8", "10.0.0.5"])
    assert ssrf_guard.is_safe_host("mixed.example") is False
