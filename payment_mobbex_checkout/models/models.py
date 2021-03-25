import logging
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    _logger.info('Model PaymentAcquirer Mobbex')

    provider = fields.Selection(selection_add=[('mobbex', 'Mobbex')], ondelete={
                                'mobbex': 'set default'})
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

    def mobbex_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_mobbex_urls(environment)['mobbex_rest_url']


class TxMobbex(models.Model):
    _inherit = 'payment.transaction'
    _logger.info('Model TXMobbex')

    def _mobbex_form_get_tx_from_data(self, data):
        _logger.info('llega from data')
        _logger.info(data)
        _logger.info(self)
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
        _logger.info('llega model')
        status = data['status']

        pending = [0, 1, 2, 3, 100, 201]
        cancel = [401, 402, 601, 602, 603, 610]
        if status == 200:
            self.sudo()._set_transaction_pending()
        elif status in cancel:
            self.sudo()._set_transaction_done()


class MobbexResPartner(models.Model):
    _inherit = 'res.partner'
    _logger.info('Model ResPartner Mobbex')

    dni_mobbex = fields.Char(
        string='DNI', help='Numero de DNI requerido para el checkout con Mobbex')
    # dni2 = fields.Char(
    #     string='DNI', help='Numero de DNI requerido para el checkout con Mobbex')
