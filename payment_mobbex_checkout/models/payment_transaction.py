from odoo import models, _
from odoo.exceptions import ValidationError
from werkzeug.urls import url_decode, url_parse

from .. import const
from .. import utils

import logging
from odoo.http import request as r
from werkzeug import urls

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Mobbex Transaction Model"""

    _inherit = 'payment.transaction'
    _description = 'Mobbex for Odoo Transaction'
    mobbex = "https://res.mobbex.com/js/sdk/mobbex@1.1.0.js"
    _logger.info('[Mobbex] PaymentTransaction Model')

    def _get_specific_rendering_values(self, processing_values: dict) -> dict:
        """Override payment to return Mobbex-specific rendering redirect form.
        (a.k.a create_checkout)
        Note: part of _get_processing_values()
        """

        utils.debug_log(
            "_get_specific_processing_values", processing_values)
        self.ensure_one()

        if self.provider_code != "mobbex" or self.provider_id.state == 'disabled':
            return super()._get_specific_processing_values(processing_values)

        # Set transaction data in a new dictionary
        payload = self.mobbex_build_payload()

        utils.debug_log("checkout payload", payload)

        # Create Checkout via API
        _logger.info("[Mobbex] Creating Checkout")
        try:
            response_content = self._send_api_request(
                'POST', '/checkout/preferences', json=payload)
        except ValidationError as error:
            self._set_error(str(error))
            return {}

        utils.debug_log("response_content", response_content)

        payment_link = response_content.get('data', '').get('url', '')
        if not payment_link:
            _logger.error("[Mobbex] Missing Payment Link. Redirect Aborted")
            return {}
        utils.debug_log("payment_link", payment_link)

        parsed_url = url_parse(payment_link)
        url_params = url_decode(parsed_url.query)

        return {
            'api_url': payment_link,
            'url_params': url_params
        }

    # === PROCESS METHODS === #
    # the next methods are part of _process() flow #

    def _extract_reference(self, provider_code: str, payment_data: dict) -> str:
        """Override of `payment` to extract the reference from the payment data.

        Args:
            provider_code (str): provider code
            payment_data (dict): payment data

        Returns:
            str: reference
        """
        if provider_code != 'mobbex':
            return super()._extract_reference(provider_code, payment_data)

        utils.debug_log("_extract_reference payment data", payment_data)
        reference = payment_data.get('reference')
        utils.debug_log(" _extract_reference", reference)
        return reference

    def _extract_amount_data(self, payment_data: dict) -> dict:
        """Override of payment to extract the amount and currency from the payment data.

        Args:
            payment_data (dict): payment data

        Returns:
            dict: amount data
        """
        if self.provider_code != 'mobbex':
            return super()._extract_amount_data(payment_data)

        amount = payment_data.get('total')
        payload_currency = payment_data.get('currency', '').get('code', '')
        # Just for test mode use
        currency = self.currency_id.name if payload_currency == 'TEST' else payload_currency

        utils.debug_log(
            " _extract_amount_data", {
                'amount': amount, 'currency': currency}
        )

        return {
            'amount': float(amount),
            'currency_code': currency,
        }

    def _apply_updates(self, payment_data: dict):
        """Override of `payment` to update the transaction based on the payment data.

        Args:
            payment_data (dict): payment data
        """

        if self.provider_code != 'mobbex':
            return super()._apply_updates(payment_data)

        utils.debug_log(
            "_apply_updates > updating payment data",
            payment_data
        )

        # Update the provider reference.
        payment_id = payment_data.get('id')
        if not payment_id:
            self._set_error(
                _("[Mobbex] Received payment data with missing payment id."))
            return
        self.provider_reference = payment_id

        # Update the payment state.
        payment_status = int(payment_data.get('status').get('code'))
        utils.debug_log(
            "_apply_updates > updating payment state",
            payment_status
        )

        if not payment_status:
            self._set_error(
                _("[Mobbex] Received payment data with missing status."))
            return

        if payment_status in const.TRANSACTION_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['approved']:
            self._set_done()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['canceled']:
            self._set_canceled()
        else:
            _logger.warning(
                "Received payment data for transaction %s with invalid payment status: %s.",
                self.reference, payment_status
            )
            self._set_error(
                _("Received payment data with invalid status: %s.", payment_status))

        _logger.info("[Mobbex] Payment state updated to %s", self.state)

    # === MOBBEX METHODS === #

    def mobbex_build_payload(self) -> dict:
        """Create the Mobbex payload/checkout body based on the transaction values.

        Returns:
            dict: The preference request payload.
        """
        # prepare controller routes
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(
            base_url, utils.get_api_endpoint('return_url'))
        webhook_url = urls.url_join(
            base_url, utils.get_api_endpoint('webhook'))

        amount = float(self.amount)
        test = self.provider_id.state == 'test'

        # Set transaction data in a new dictionary
        payload = {
            "total": amount,
            "description": self._description,
            "currency": self.currency_id.name,
            "reference": self.reference,
            "test": test,
            "webhook": webhook_url,
            "return_url": return_url,
            "customer": self.mobbex_prepare_customer_data(),
            "items": self.mobbex_prepare_items_data()
        }
        utils.debug_log(
            "mobbex_prepare_preference_request_payload payload", payload)

        return payload

    def mobbex_prepare_customer_data(self) -> dict:
        """Create the customer data for the preference request based on the transaction values.

        Returns:
            dict: The customer data.
        """
        return {
            "email": self.partner_id.email,
            "name": self.partner_id.name,
            "identification": self.partner_id.vat,
        }

    def mobbex_prepare_items_data(self) -> list[dict]:
        """Create the items list for the Mobbex checkout based on the transaction.

        Returns:
            list: The items list. Each item is a dict
        """

        self.ensure_one()
        items = []

        _logger.info("[Mobbex] Preparing items data")
        for order in self.sale_order_ids:
            for line in order.order_line:
                if line.display_type:
                    continue

                product = line.product_id
                if not product:
                    continue

                items.append({
                    "description": product.display_name,
                    "quantity": int(line.product_uom_qty),
                    "total": float(line.price_total),
                    "image": product.image_1920
                    and f"/web/image/product.product/{product.id}/image_1920"
                    or None,
                })

        utils.debug_log("mobbex_prepare_items_data items", items)

        if not items:
            _logger.warning("[Mobbex] Warning: No items found")
        return items
