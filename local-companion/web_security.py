import ipaddress
from urllib.parse import urlsplit


def normalize_origin(origin):
    if not isinstance(origin, str) or not origin or origin == "null":
        return None
    try:
        parsed = urlsplit(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            return None
        host = parsed.hostname.lower()
        port = ":{}".format(parsed.port) if parsed.port is not None else ""
        return "{}://{}{}".format(parsed.scheme.lower(), host, port)
    except ValueError:
        return None


def origin_is_allowed(origin, allowed_origins):
    if not origin:
        return True
    normalized = normalize_origin(origin)
    return normalized is not None and normalized in allowed_origins


def allowed_origin(origin, allowed_origins):
    if not origin:
        return None
    normalized = normalize_origin(origin)
    return normalized if normalized in allowed_origins else None


def is_loopback_host(host_header):
    if not isinstance(host_header, str) or not host_header:
        return False
    try:
        hostname = urlsplit("//" + host_header).hostname
        if not hostname:
            return False
        if hostname.lower() == "localhost":
            return True
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False
