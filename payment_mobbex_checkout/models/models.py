import logging
from ..controllers.main import MobbexController
from odoo import api, fields, models, _
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError
_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    """Mobbex Payment Acquierer class

    Mobbex Checkout Module configuration panel class

    Attributes:
        provider : provider selection
        mobbex_api_key : Mobbex API key
        mobbex_access_token : Mobbex access token
        mobbex_payment_method : payment method mode
    """
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
        """Get the appropriate Mobbex url depending on the environment

        :param str environment: environment mode

        :return str mobbex_rest_url: mobbex url
        """
        if environment == 'prod':
            return {
                'mobbex_rest_url': '/payment/mobbex/checkout/',
            }
        else:
            return {
                'mobbex_rest_url': '/payment/mobbex/checkout/',
            }

    def _get_mobbex_tx_values(self, values):
        """Get Mobbex transaction values

        :param dict values: transaction values

        :return dict mobbex_tx_values: mobbex transaction values
        """
        # Get base url
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')

        # Get partner
        partner_id = values.get('partner_id')
        partner = request.env['res.partner'].sudo().browse(partner_id)

        _logger.info('tx values')
        _logger.info(values)
        _logger.info(self)

        # Set transaction data in a new dictionary
        mobbex_tx_values = ({
            '_input_charset': 'utf-8',
            'amount': values.get('amount'),
            'partner': values.get('partner'),
            'acquirer': values.get('acquirer'),
            'reference': values.get('reference'),
            'return_url': values.get('return_url'),
            'currency_id': values.get('currency_id'),
            'partner_dni_mobbex': partner.dni_mobbex,
            'currency_name': values.get('currency_name'),
            'acquirer_provider': values.get('acquirer_provider'),
            'billing_partner_name': values.get('billing_partner_name'),
            'billing_partner_phone': values.get('billing_partner_phone'),
            'billing_partner_email': values.get('billing_partner_email'),
        })

        return mobbex_tx_values

    def mobbex_form_generate_values(self, values):
        """Update mobbex transaction form values

        :param dict values: transaction values

        :return dict values: updated transaction values
        """
        values.update(self._get_mobbex_tx_values(values))
        return values

    def mobbex_get_form_action_url(self):
        """Get Mobbex form action url considering environmnet

        :return str: mobbex action url
        """
        _logger.info('Mobbex action url')
        self.ensure_one()
        # Checks environment mode
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_mobbex_urls(environment)['mobbex_rest_url']


class TxMobbex(models.Model):
    """Mobbex Transaction Model"""

    _inherit = 'payment.transaction'
    _logger.info('Model TXMobbex')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------
    def _mobbex_form_get_tx_from_data(self, data):
        """Obtains transaction data from data reference

        :param dict data: transaction data

        :return dict txs: transaction data corresponding to the reference
        """
        _logger.info('received data')
        _logger.info(data)
        # Get transaction reference
        reference = data['reference']
        if not reference:
            # Inform error
            error_msg = _('Mobbex: received data with missing reference (%s)') % (
                reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        # Search for the transaction data corresponding to the reference
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
        """Get transaction status value from status code

        :param dict data: transaction data

        :return str return_val: status value
        """
        _logger.info('llega model')
        # Get data status code
        status = data['status']
        return_val = ''
        # Set statuses codes
        pending = [0, 1, 2, 3, 100, 201]
        cancel = [401, 402, 601, 602, 603, 610]
        # Set status value according to status code
        if status == 200:
            self.sudo()._set_transaction_done()
            return_val = 'paid'
        if status in pending:
            self.sudo()._set_transaction_pending()
            return_val = 'pending'
        elif status in cancel:
            self.sudo()._set_transaction_cancel()
            return_val = 'cancelled'
        return return_val
    # --------------------------------------------------


class MobbexResPartner(models.Model):
    """Mobbex Resource Partner class

    Adds additional DNI field to Odoo resource partner
        * Odoo partner means vendor, customer or employee
        * In this case, affect Odoo customer payment checkout
    
    Attributes
        dni_mobbex : add dni field
    """
    _inherit = 'res.partner'
    _logger.info('Model ResPartner Mobbex')

    # Add dni field in odoo payment checkout
    dni_mobbex = fields.Char(
        string='DNI', help='Numero de DNI requerido para el checkout con Mobbex')
    # dni2 = fields.Char(
    #     string='DNI', help='Numero de DNI requerido para el checkout con Mobbex')