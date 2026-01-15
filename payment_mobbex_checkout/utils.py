from . import const
import urllib.parse
import hashlib
from .models.payment_provider import PaymentProvider as pp
from typing import Any, Optional
import logging

_logger = logging.getLogger(__name__)


def get_api_endpoint(endpoint: str):
    """Create a url passing the endpoint and order_id

        Args:
            endpoint (str): controller

        Returns:
            str: controller url
        """
    params = {
        'platform': 'odoo',
        'version': const.MOBBEX_ODOO_VERSION,
        'mobbex_token': generate_mobbex_token(),
    }

    query = urllib.parse.urlencode(params)
    route = const.RETURN_URL if endpoint == 'return_url' else const.WEBHOOK_URL

    return f"{route}?{query}"


def generate_mobbex_token() -> str:
    """Generate a token using current credentials configured

        Returns:
            str: hashed token
        """
    secret = f"{pp.mobbex_api_key}|{pp.mobbex_access_token}"
    return hashlib.sha256(secret.encode()).hexdigest()


def validate_mobbex_token(token: str) -> bool:
    """Validate a token generated from credentials configured

    Args:
        token (str): received token

    Returns:
        bool: token validation
    """
    return token == generate_mobbex_token()


def debug_log(message: str, data: Optional[Any] = None) -> None:
    """Debug mode only logs.

    Args:
        message (str): message to log
        data (Optional[Any], optional): data to log. Defaults to None.

    """
    if not pp.mobbex_enable_debug:
        return

    if data is not None:
        _logger.info("[Mobbex Debug] %s | data=%r", message, data)
    else:
        _logger.info("[Mobbex Debug] %s", message)
