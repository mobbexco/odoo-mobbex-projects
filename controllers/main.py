# -*- coding: utf-8 -*-

# Copyright 2015 Eezee-It
import logging
import json
import pprint
import werkzeug
import requests
from odoo import http
from odoo.http import request

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

        # Get name sale order
        reference = post['reference'].split('-')
        ref = reference[0]

        # _logger.info(ref)

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
        currency_name = order_products[0].currency_id.name

        # Get Base Ulr
        base_url = http.request.env['ir.config_parameter'].get_param(
            'web.base.url')
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
        transaction = dict()

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

        transaction['total'] = post['amount']
        transaction['currency'] = currency_name
        transaction['reference'] = ref
        transaction["description"] = f'Orden de compra: {reference[0]}-{reference[1]}'
        transaction['items'] = items
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

        #Post & Redirect
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
        return werkzeug.utils.redirect('/payment/process')
