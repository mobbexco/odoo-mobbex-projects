# -*- coding: utf-8 -*-

# Copyright 2015 Eezee-It
import logging
import json
import pprint
import werkzeug
import requests
from odoo import http
from odoo.http import request
# from urllib import parse

_logger = logging.getLogger(__name__)
_logger.info('Controller instance')


class MobbexController(http.Controller):
    _notify_url = '/payment/mobbex/notify_url/'
    _return_url = '/payment/mobbex/return_url/'
    _logger.info('Controller Init')

    @http.route([
        '/payment/mobbex/notify_url/'],
        type='http', auth='public', methods=['POST'], csrf=False)
    def mobbex_notify(self, **post):
        _logger.info('Controller Notify')
        _logger.info(post)

        # Get al post data
        # ==================================================================
        # Get name sale order
        reference = post['reference'].split('-')
        ref = reference[0]

        # Get Currency Ref
        currency_id = post['currency_id']

        # Get Amount
        amount = post['amount']

        # Get email billing
        billing_partner_email = post['billing_partner_email']
        billing_partner_name = post['billing_partner_name']
        billing_partner_phone = post['billing_partner_phone']
        # ==================================================================

        # DB Querying
        # ==================================================================
        # Get id sale order by name
        filter = [('name', '=', ref)]
        saleorders = http.request.env['sale.order'].sudo().search(filter)
        id_sale_order = saleorders.id

        # Get all productos
        filterProducts = [('order_id', '=', id_sale_order)]
        order_products = http.request.env['sale.order.line'].sudo().search(
            filterProducts)

        # Get Currency
        filter_currency = [('id', '=', currency_id)]
        currency = http.request.env['res.currency'].sudo().search(
            filter_currency)
        currency_name = currency.name
        _logger.info(currency_name)

        # Get Base Url
        base_url = http.request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        # base_url = 'https://915e34fdd14b.ngrok.io'
        _logger.info(base_url)

        # Get Api key & Token
        filterAcquirer = [('name', '=', 'Mobbex')]
        mobbexAcquirer = http.request.env['payment.acquirer'].sudo().search(
            filterAcquirer)

        mobbex_api_key = mobbexAcquirer.mobbex_api_key
        mobbex_access_token = mobbexAcquirer.mobbex_access_token
        # ==================================================================

        # Build transaction
        # ==================================================================
        items = []
        customer = dict()
        transaction = dict()
        options = dict()
        platform = dict()

        # Iterate products
        for product in order_products:
            # Build item detail
            item = dict()
            item[
                'image'] = f'{base_url}/web/image/product.product/{product.product_id.id}/image_128/{product.name.replace(" ","%20")}'
            item['quantity'] = product.product_uom_qty
            item['description'] = product.name
            item['total'] = product.price_subtotal

            # Append to items
            items.append(item)

        platform["name"] = "odoo"
        platform["version"] = "1.0.0"
        options["platform"] = platform

        # Customer Data
        customer['email'] = billing_partner_email
        # customer['identification'] = ''
        customer['name'] = billing_partner_name
        customer['phone'] = billing_partner_phone

        transaction['total'] = amount
        transaction['currency'] = currency_name
        transaction['reference'] = f'{reference[0]}-{reference[1]}'
        transaction["description"] = f'Orden de compra: {reference[0]}-{reference[1]}'
        transaction['items'] = items
        transaction['customer'] = customer
        transaction['options'] = options
        transaction['webhook'] = f'{base_url}/payment/mobbex/return_url/'
        # transaction['webhook'] = f'https://94de78905bf2.ngrok.io/payment/mobbex/return_url/'
        _logger.info(transaction)
        # ==================================================================

        # Build header
        # ==================================================================
        _logger.info(mobbex_api_key)
        _logger.info(mobbex_access_token)

        headers = {"x-api-key": mobbex_api_key,
                   "x-access-token": mobbex_access_token,
                   "x-lang": "es",
                   "Content-Type": "application/json",
                   "cache-control": "no-cache"}
        # ==================================================================

        # Post & Redirect
        # ==================================================================
        data = json.dumps(transaction)
        r = requests.post("https://api.mobbex.com/p/checkout",
                          data=data, headers=headers)
        dataRes = r.json()

        return werkzeug.utils.redirect(dataRes['data']['url'])
        # ==================================================================
        # return werkzeug.utils.redirect('/payment/process')
        # return ''

    @http.route([
        '/payment/mobbex/return_url/'], type='http', auth="public", methods=['POST'], csrf=False)
    def mobbex_return(self, **post):
        """ Mobbex Return """
        _logger.info('Controller Return')
        _logger.info(post)

        status = int(post.get("data[payment][status][code]"))
        reference = post.get("data[payment][reference]")

        feedback = {"reference": reference, "status": status}
        # Testing Change Status
        res = request.env['payment.transaction'].sudo(
        ).form_feedback(feedback, 'mobbex')
        _logger.info(res)
        return 'Ok'
