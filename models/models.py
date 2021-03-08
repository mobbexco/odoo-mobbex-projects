import logging
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
_logger = logging.getLogger(__name__)


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

    # def mobbex_form_generate_values(self, values):
    #     base_url = self.get_base_url()
    #     mobbex_tx_values = dict(values)
    #     param_plus = {
    #         'return_url': mobbex_tx_values.pop('return_url', False)
    #     }
    #     temp_ogone_tx_values = {
    #         'ORDERID': values['reference'],
    #         'AMOUNT': float_repr(float_round(values['amount'], 2) * 100, 0),
    #         'CURRENCY': values['currency'] and values['currency'].name or '',
    #         'LANGUAGE': values.get('partner_lang'),
    #         'CN': values.get('partner_name'),
    #         'EMAIL': values.get('partner_email'),
    #         'OWNERZIP': values.get('partner_zip'),
    #         'OWNERADDRESS': values.get('partner_address'),
    #         'OWNERTOWN': values.get('partner_city'),
    #         'OWNERCTY': values.get('partner_country') and values.get('partner_country').code or '',
    #         'OWNERTELNO': values.get('partner_phone'),
    #         'ACCEPTURL': urls.url_join(base_url, OgoneController._accept_url),
    #         'DECLINEURL': urls.url_join(base_url, OgoneController._decline_url),
    #         'EXCEPTIONURL': urls.url_join(base_url, OgoneController._exception_url),
    #         'CANCELURL': urls.url_join(base_url, OgoneController._cancel_url),
    #         'PARAMPLUS': url_encode(param_plus),
    #     }
    #     if self.save_token in ['ask', 'always']:
    #         temp_ogone_tx_values.update({
    #             'ALIAS': 'ODOO-NEW-ALIAS-%s' % time.time(),    # something unique,
    #             'ALIASUSAGE': values.get('alias_usage') or self.ogone_alias_usage,
    #         })
    #     shasign = self._ogone_generate_shasign('in', temp_ogone_tx_values)
    #     temp_ogone_tx_values['SHASIGN'] = shasign
    #     ogone_tx_values.update(temp_ogone_tx_values)
    #     return ogone_tx_values

    def mobbex_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_mobbex_urls(environment)['mobbex_rest_url']


class TxMobbex(models.Model):
    _inherit = 'payment.transaction'
    _logger.info('Model TXMobbex')

    @api.model
    def _mobbex_form_get_tx_from_data(self, data):
        reference, txn_id = data.get('item_number'), data.get('txn_id')
        if not reference or not txn_id:
            error_msg = _('Mobbex: received data with missing reference (%s) or txn_id (%s)') % (
                reference, txn_id)
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
