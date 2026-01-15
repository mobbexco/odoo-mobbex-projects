# -*- coding: utf-8 -*-

import logging
from werkzeug.exceptions import Forbidden
from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from .. import utils
from .. import const

_logger = logging.getLogger(__name__)
_logger.info('[Mobbex] Controller instance')


class MobbexController(http.Controller):
    """Mobbex Controller Class

    Attributes:
        _return_url : return endpoint.
        _webhook_url : webhook endpoint.
    """
    # Controller init
    _return_url = const.RETURN_URL
    _webhook_url = const.WEBHOOK_URL

    @http.route(
        _return_url,
        type='http',
        auth="public",
        methods=['GET'],
        csrf=False,
        website=True
    )
    def mobbex_return_from_checkout(self, **data):
        """Mobbex return controller
        Process Mobbex Checkout payment data and
        redirects to order status or error page

        Args:
            params (dict): endpoint query params

        Returns:
            werkzeug.wrappers.Response: redirect response
        """
        _logger.info(f"[Mobbex] Return payment data: {data}")

        # Get status and reference from payment data
        status = int(data.get('status', ''))
        mobbex_token = data.get('mobbex_token', '')

        utils.debug_log(
            "Return query params",
            [status, mobbex_token]
        )

        # Validate data
        if not status or not mobbex_token:
            _logger.error("[Mobbex] Required data from Mobbex not found")
            return self._redirect_to_error(
                error_msg="Required data from Mobbex not found."
            )

        if not utils.validate_mobbex_token(mobbex_token):
            _logger.error("[Mobbex] Invalid Token")
            return self._redirect_to_error(
                error_msg="Invalid Security Token."
            )

        _logger.info("[Mobbex] Processing Return with status %s", status)
        if status > 1 and status < 400:
            return request.redirect('/payment/status')
        else:
            return self._redirect_to_error(
                error_msg="Transaction fail. Payment could not be processed."
            )

    def _redirect_to_error(self, error_msg=None):
        """Redirect to payment page with error message

        Args:
            error_msg (str, optional): Error message to display

        Returns:
            werkzeug.wrappers.Response: redirect response
        """
        if error_msg:
            request.session['payment_error'] = error_msg

        return request.redirect('/shop/payment')

    @http.route(
        _webhook_url,
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        website=True
    )
    def mobbex_webhook(self, **params: dict) -> str:
        """Process the payment data sent by Mobbex webhook

        Info: We have some methods that override the _process() flow.
        For more information about the process, see that methods in our
        models/payment_transaction or in the Odoo model located in
        odoo/addons/payment/models/payment_transaction.

        Args:
            params (dict): query params.

        Returns:
            (str): An empty string to acknowledge the notification.
        """
        # get transaction data sent by mobbex
        tx_data = request.get_json_data()
        _logger.info(f"[Mobbex] Controller Webhook data: {tx_data}")
        utils.debug_log("Webhook transaction", tx_data)

        # get webhook's uri params
        mobbex_token = params.get('mobbex_token', '')

        if not mobbex_token:
            _logger.error("[Mobbex] Token not found. Process aborted")
            return ''

        if not utils.validate_mobbex_token(mobbex_token):
            _logger.error("[Mobbex] Invalid Token. Process aborted")
            return ''

        # get payment data
        payment = tx_data.get('data', '').get('payment', '')
        if not payment:
            _logger.error("[Mobbex] Payment data not found. Process aborted")
            return ''

        _logger.info("[Mobbex] Processing Webhook > payment data: %s", payment)

        # get transaction
        request.env['payment.transaction'].sudo()._process('mobbex', payment)

        return ''  # Acknowledge the notification.
