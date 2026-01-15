# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mobbex Checkout',
    'version': '1.0.2',
    'author': 'Mobbex',
    'website': 'https://www.mobbex.com/',
    'category': 'Accounting/Payment Providers',
    'summary': 'Module to integrate Mobbex Checkout payment gateway with Odoo.',
    'description': """The Mobbex Payment Gateway redirects customers to Mobbex to enter their payment information.""",
    'depends': ['base', 'payment'],
    'installable': True,
    'application': True,
    "auto_install": False,
    'data': [
        'views/mobbex_checkout_template.xml',
        'views/mobbex_checkout_views.xml',

        'data/payment_provider_data.xml',
        'data/payment_method_data.xml'
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/checkout_banner.png'],
    'license': 'AGPL-3'
}
