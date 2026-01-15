# -*- coding: utf-8 -*-

from . import models
from . import controllers

import odoo.addons.payment as payment


def post_init_hook(env):
    payment.setup_provider(env, 'mobbex')
    payment_mobbex = env["payment.provider"].search(
        [("code", "=", "mobbex")], limit=1)
    # Search for the "mobbex" method in the "payment.method" model
    payment_method_mobbex = env["payment.method"].search(
        [("code", "=", "mobbex")], limit=1
    )
    # Link the found payment method to the found payment provider
    if payment_method_mobbex.id is not False:
        payment_mobbex.write(
            {
                "payment_method_ids": [(6, 0, [payment_method_mobbex.id])],
            }
        )


def uninstall_hook(env):
    payment.reset_payment_provider(env, 'mobbex')
