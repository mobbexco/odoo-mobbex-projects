# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mobbex Checkout',
    'version': '1.1.1',
    'author': 'Mobbex',
    'website': 'https://www.mobbex.com/',
    'category': 'Accounting/Payment',
    'summary': 'A module that provides Odoo Mobbex integration.',
    'description': """The Mobbex Payment Gateway redirects customers to Mobbex to enter their payment information.""",
    'depends': ['payment'],
    'installable': True,
    'data': [
        'views/mobbex_checkout_views.xml',
        'views/mobbex_checkout_template.xml',
        'data/payment_acquirer_data.xml',
    ],
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/checkout_banner.png'],
    'license': 'AGPL-3'
}
