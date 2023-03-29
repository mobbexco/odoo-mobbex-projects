import logging
import json
import requests
from ..controllers.main import MobbexController
from odoo import api, fields, models, _
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError


_logger = logging.getLogger(__name__)

MOBBEX_URL = 'https://api.mobbex.com'

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    _logger.info('Model PaymentAcquirer Mobbex')

    provider = fields.Selection(selection_add=[('mobbex', 'Mobbex')])
    mobbex_payment_method = fields.Selection([
        ('mobbex_checkout', 'Mobbex Checkout')
    ], string='Modalidad', default='mobbex_checkout')
    mobbex_api_key = fields.Char(
        string='Clave API', required_if_provider='mobbex', groups='base.group_user',
        help='La clave API debe ser la misma que Mobbex provee en tu aplicacion en el portal de desarrolladores')
    mobbex_access_token = fields.Char(
        string='Token de Acceso', required_if_provider='mobbex', groups='base.group_user',
        help='El Token de Acceso debe ser el mismo que Mobbex provee en tu aplicacion en el portal de desarrolladores')

    @api.model
    def _get_mobbex_urls(self, environment):
        """ Mobbex URLS """
        if environment == 'prod':
            return {
                'mobbex_rest_url': '/payment/mobbex/notify_url/',
            }
        else:
            return {
                'mobbex_rest_url': '/payment/mobbex/notify_url/',
            }

    def _get_mobbex_tx_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')

        partner_id = values.get('partner_id')
        partner = request.env['res.partner'].sudo().browse(partner_id)


        mobbex_tx_values = ({
            '_input_charset': 'utf-8',
            'reference': values.get('reference'),
            'amount': values.get('amount'),
            'currency_id': values.get('currency_id'),
            'currency_name': values.get('currency_name'),
            'billing_partner_email': values.get('billing_partner_email'),
            'billing_partner_phone': values.get('billing_partner_phone'),
            'billing_partner_name': values.get('billing_partner_name'),
            'partner_dni_mobbex': partner.vat,
            'partner': values.get('partner'),
            'return_url': values.get('return_url'),
        })
        return mobbex_tx_values

    def mobbex_form_generate_values(self, values):
        values.update(self._get_mobbex_tx_values(values))
        return values

    def mobbex_get_form_action_url(self):
        _logger.info('Mobbex action url')
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_mobbex_urls(environment)['mobbex_rest_url']


class TxMobbex(models.Model):
    _inherit = 'payment.transaction'



    def _mobbex_form_get_tx_from_data(self, data):
        _logger.info('llega from data')
        _logger.info(data)
        reference = data['reference']
        if not reference:
            error_msg = _('Mobbex: received data with missing reference (%s)') % (
                reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].search(
            [('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Mobbex: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    def _mobbex_form_validate(self, data):
        status = int(data['data']['payment']['status']['code'] or 0)
        return_val = ''

        pending = [0, 1, 2, 3, 100, 201]
        cancel = [401, 402, 601, 602, 603, 610]
        data = {
            'acquirer_reference': data['data']['payment']['id'],
        }
        self.write(data)
        if status == 200:
            self._set_transaction_done()
            return_val = 'paid'
        elif status == '500':
            self._set_transaction_error(data['data']['payment']['message'])
            return_val = 'error'
        elif status in pending:
            self._set_transaction_pending()
            return_val = 'pending'
        elif status in cancel:
            self._set_transaction_cancel()
            return_val = 'cancelled'
        return return_val

    def _mobbex_validate_by_id(self):
        self.ensure_one()
        headers = {"x-api-key": self.acquirer_id.mobbex_api_key,
                   "x-access-token": self.acquirer_id.mobbex_access_token,
                   "x-lang": "es",
                   "Content-Type": "application/json",
                   "cache-control": "no-cache"}
        data = json.dumps({'id': self.acquirer_reference[4:], 'test':True})

        url = MOBBEX_URL + '/2.0/transactions/status'
        req = requests.post(url, data=data, headers=headers)

        result = req.json()
        _logger.info(result)

