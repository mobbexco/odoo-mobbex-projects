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
    """Mobbex Controller Class

    Attributes:
        _return_url : return endpoint.
        _checkout_url : notify endpoint.
    """
    # Controller init
    _return_url = '/payment/mobbex/return_url/'
    _checkout_url = '/payment/mobbex/checkout/'

    @http.route([
        '/payment/mobbex/checkout/'],
        type='http', auth='public', methods=['POST'], csrf=False, website=True)
    def mobbex_checkout(self, **post):
        """Creates Mobbex checkout

        Fires when accesing mobbex checkout route

        Returns:
            (str): redirect url
        """
        # Set necessary variables
        items = []
        reference = post['reference'].split('-')
        sale_order = self.mobbex_get_sale_order(reference)
        products = self.mobbex_get_products(sale_order.id)
        mobbexAcquirer = self.mobbex_get_acquierer(post)
        base_url = http.request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        
        # Build header
        headers = {
            "x-lang": "es",
            "cache-control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": mobbexAcquirer.mobbex_api_key,
            "x-access-token": mobbexAcquirer.mobbex_access_token,
        }

        # Build body
        # Iterate products and set order items
        for product in products:
            # Build item detail
            item = {
                "description" : product.name,
                "total" : product.price_subtotal, 
                "quantity" : product.product_uom_qty,
                "image" : f'{base_url}/web/image/product.product/{product.product_id.id}/image_128/{product.name.replace(" ","%20")}',
            }
            # Append to items list
            items.append(item)

        platform = {
            "name" : "odoo",
            "version" : "1.0.2",
        }
        options = {
            "platform" : platform,
            "domain" : f'{base_url}/shop/payment',
        }
        customer = {
            "name" : post['billing_partner_name'],
            "phone" : post['billing_partner_phone'],
            "email" : post['billing_partner_email'],
            "identification" : self.mobbex_customer_dni_validation(post)
        }

        # Transaction data
        trx_data = {
            "items" : items,
            "options" : options,
            "customer" : customer,
            "total" : post.get('amount', ''),
            "currency" : self.mobbex_get_currency(post),
            "reference" : f'{reference[0]}-{reference[1]}',
            "test" : True if mobbexAcquirer.state == 'test' else False,
            "description" : f'Orden de compra: {reference[0]}-{reference[1]}',
            "return_url" : f"{base_url}/payment/mobbex/return_url/?reference={reference[0]}-{reference[1]}",
            # "webhook" : '',
        }

        # Post & Redirect
        data = json.dumps(trx_data)
        # Transaction data logs displayed in terminal
        _logger.info('Trx data')
        _logger.info(trx_data)
        # API request
        r = requests.post("https://api.mobbex.com/p/checkout",
                          data=data, headers=headers)
        dataRes = r.json()
        # Set state in sent when checkout is created (ex : '/payment/process')
        sale_order.write({'state': 'sent'})
        return werkzeug.utils.redirect(dataRes['data']['url'])

    @http.route([
        '/payment/mobbex/return_url/'],
          type='http', auth="public", methods=['GET'], csrf=False, website=True)
    def mobbex_return(self, **post):
        """Mobbex return controller
        Fires when accesing to return route

        Returns:
            str: process route
        """
        _logger.info('Controller Return')
        _logger.info(post)
        
        #Get status and reference from post data
        status    = post.get('status', '')
        reference = post.get('reference', '') 

        # Use reference name to get sale order
        ref_name   = reference.split('-')
        ref        = ref_name[0]
        filter     = [('name', '=', ref)]
        saleorders = http.request.env['sale.order'].sudo().search(filter)

        # Testing Change Status
        feedback   = {"reference": reference, "status": int(status)}
        res = http.request.env['payment.transaction'].sudo(
        ).form_feedback(feedback, 'mobbex')
        _logger.info(res)

        if res == 'paid':
            # If transaction was paid, we need confirm order sale
            saleorders.sudo().action_confirm()
            # Redirect to order process
            return werkzeug.utils.redirect(f'/payment/process/')
        else:
            # If isn't paid return to cart
            return werkzeug.utils.redirect('/shop/cart/')
    
    def mobbex_get_currency(self, post_data):
        """Get currency code name

        Args:
            post (dict): post data

        Returns:
            str: currency code
        """
        # Get currency post data
        currency_id = post_data['currency_id']
        currency_name = post_data['currency_name']

        try:
            # Checks if currency name is set
            if len(currency_name) > 0 and currency_name is not None:
                return currency_name
            # Get currency name by id
            elif len(currency_id):
                filter_currency = [('id', '=', currency_id)]
                currency = http.request.env['res.currency'].sudo().search(
                    filter_currency)
                return currency.name
        except NameError:
            print("Mobbex Error: currency name or currency id is not defined")
    
    def mobbex_customer_dni_validation(self, post_data):
        """Validates customer dni

        Args:
            post (dict): post data
        Returns:
            str: customer dni
        """
        # Get partner dni and mobbex form dni
        partner_dni_mobbex = post_data['partner_dni_mobbex']
        final_dni = partner_dni_mobbex
        form_dni_mobbex = post_data['form_dni_mobbex']

        try:
            if form_dni_mobbex != partner_dni_mobbex:
                final_dni = form_dni_mobbex
                # We update res_partner.dni_mobbex
                partner_id = post_data['partner_id']
                partner = request.env['res.partner'].sudo().browse(int(partner_id))
                partner.write({'dni_mobbex': form_dni_mobbex})
    
            if final_dni != '' and final_dni != None:
                return final_dni
        except NameError:
            print("Mobbex Error: mobbex dni is not defined")
        
    def mobbex_get_acquierer(self, post_data):
        # Get Acquirer ID
        acquirer_id = int(post_data['acquirer'].replace(
            'payment.acquirer(', '').replace(',', '').replace(')', ''))

        # Get Api key & Token
        filterAcquirer = [('id', '=', acquirer_id)]
        mobbexAcquirer = http.request.env['payment.acquirer'].sudo().search(
            filterAcquirer)

        return mobbexAcquirer
    
    def mobbex_get_sale_order(self, reference):
        """Get sale order

        Args:
            reference (str): order reference

        Returns:
            obj: sale order object
        """
        # Get name sale order
        sale_order = reference[0]
        # Get id sale order by name
        filter = [('name', '=', sale_order)]
        sale_order = http.request.env['sale.order'].sudo().search(filter)
        return sale_order
    
    def mobbex_get_products(self, sale_order_id):
        """Gets products from order

        Args:
            sale_order (str): sale order

        Returns:
            obj: product object
        """
        # Get all products
        filterProducts = [('order_id', '=', sale_order_id)]
        products = http.request.env['sale.order.line'].sudo().search(
            filterProducts)
        return products