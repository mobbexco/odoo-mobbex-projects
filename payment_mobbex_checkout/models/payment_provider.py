import logging
import json

from odoo import fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from .. import const


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """Mobbex Payment Acquierer class

    Mobbex Checkout Module configuration panel class

    Attributes:
        provider : provider selection
        mobbex_api_key (str) : Mobbex API key
        mobbex_access_token (str): Mobbex access token
        mobbex_enable_debug (str): debug mode
    """
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('mobbex', 'Mobbex')],
        ondelete={'mobbex': 'set default'}
    )

    # TO DO: embed
    # mobbex_payment_method = fields.Selection([
    #     ('Redirección', 'mobbex'),
    #     ('Modal', 'embed')
    # ], string='Modalidad', default='Redirección')

    mobbex_api_key = fields.Char(
        string='Clave API',
        required_if_provider='mobbex',
        groups='base.group_system',
        help='La clave API debe ser la misma que Mobbex provee en tu aplicacion en el portal de desarrolladores'
    )
    mobbex_access_token = fields.Char(
        string='Token de Acceso',
        required_if_provider='mobbex',
        groups='base.group_system',
        help='El Token de Acceso debe ser el mismo que Mobbex provee en tu aplicacion en el portal de desarrolladores'
    )

    mobbex_enable_debug = fields.Boolean(
        string="Modo Debug",
        help="Activa logs detallados para desarrollo y mantenimiento.\n"
             "No usar en producción: puede exponer información sensible.",
        groups='base.group_system',
        default=False
    )

    def _build_request_url(self, endpoint, *, is_proxy_request=False, **kwargs):
        """Override of `payment` to build the request URL."""
        _logger.info("[Mobbex] _build_request_url > Getting Checkout URL")
        if self.code != 'mobbex':
            return super()._build_request_url(
                endpoint, is_proxy_request=is_proxy_request, **kwargs
            )

        return const.MOBBEX_CHECKOUT

    def _build_request_headers(
        self,
        method,
        *args,
        idempotency_key=None,
        is_proxy_request=False,
        **kwargs,
    ):
        """Override of `payment` to build the request headers."""
        if self.code != 'mobbex':
            return super()._build_request_headers(
                method,
                *args,
                idempotency_key=idempotency_key,
                is_proxy_request=is_proxy_request,
                **kwargs,
            )

        headers = {
            'x-api-key': self.mobbex_api_key,
            'x-access-token': self.mobbex_access_token,
            'content-type': 'application/json'
        }

        return headers

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "mobbex":
            _logger.info(
                f'[Mobbex] Supported Currencies:{const.SUPPORTED_CURRENCIES}')
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes.
        """
        self.ensure_one()
        _logger.info(
            f'[Mobbex] Payment Methods:{const.DEFAULT_PAYMENT_METHOD_CODES}')
        if self.code != 'mobbex':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES
