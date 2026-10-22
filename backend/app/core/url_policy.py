import ipaddress
import socket
from urllib.parse import urlparse

from app.core.errors import AccessPilotError


def validate_url(url: str, allow_loopback: bool = False) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise AccessPilotError("invalid_url", "Use an absolute http or https URL without credentials.", 400)
    try:
        addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as error:
        raise AccessPilotError("blocked_target", "The target host could not be resolved.", 403) from error
    for address in addresses:
        if address.is_loopback:
            if not allow_loopback:
                raise AccessPilotError("blocked_target", "Loopback targets are blocked.", 403)
            continue
        if address.is_private or address.is_link_local or address.is_reserved or address.is_unspecified:
            raise AccessPilotError("blocked_target", "Private or reserved targets are blocked.", 403)
