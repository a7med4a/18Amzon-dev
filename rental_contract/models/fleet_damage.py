# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetDamage(models.Model):
    _inherit = "fleet.damage"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.', domain="[('state','in',('opened','delivered_pending','delivered_debit','closed')),('partner_id','=',customer_id)]")

    def action_charge(self):
        res = super().action_charge()
        for rec in self:
            if rec.rental_contract_id:
                rec.rental_contract_id.current_accident_damage_amount = rec.total_include_tax
                rec.rental_contract_id.invoice_damage_accident = 'invoiced'
        return res
