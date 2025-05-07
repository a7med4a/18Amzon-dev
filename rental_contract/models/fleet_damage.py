# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetDamage(models.Model):
    _inherit = "fleet.damage"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.',domain="[('state','in',('opened','delivered_pending','delivered_debit','closed')),('partner_id','=',customer_id)]")
