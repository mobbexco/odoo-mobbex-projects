import loggin
from odoo.addons.payment.tests.common import PaymentAcquirerCommon


class MobbexCommon(PaymentAcquirerCommon):
    def setUp(self):
        super(MobbexCommon, self).setUp()

        self.mobbex = self.env.ref('payment.payment_acquirer_mobbex')
        self.mobbex.write({
            'mobbex_api_key': '9u2ZVG2Jyj3WHdboDGWrM5IJRmk1kZt8eVcDWMf0',
            'mobbex_access_token': 'a1eee705-86be-45d9-8280-864914a1f63e'
        })

        # some CC
        self.visa = (('4507990000000010', '200'),
                     ('4507990000000010', '400'), ('4507990000000010', '003'))
        self.mastercard = (('5323629993121008', '200'),
                           ('5323629993121008', '400'), ('5323629993121008', '003'))
        self.amex = (('376411234531007', '0200'),
                     ('376411234531007', '0400'), ('376411234531007', '0003'))


@tagged('post_install', '-at_install', 'external', '-standard')
class MobbexForm(MobbexCommon):

    def test_10_mobbex_form_render(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # be sure not to do stupid things
        self.assertEqual(self.mobbex.state, 'test',
                         'test without test environment')

        # ----------------------------------------
        # Test: button direct rendering
        # ----------------------------------------

        # render the button
        res = self.mobbex.render(
            'test_ref0', 0.01, self.currency_euro.id,
            values=self.buyer_values)

        form_values = {
            'cmd': '_xclick',
            'acquirer': 'payment.acquirer(17,)'
            'reference': 'test_ref_2'
        }

