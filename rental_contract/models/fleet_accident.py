# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetAccident(models.Model):
    _inherit = "fleet.accident"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.')

    created_from_rental = fields.Boolean(
        'Created From Rental', copy=False, default=False)

    @api.model_create_multi
    def create(self, vals_list):
        accidents = super().create(vals_list)
        for accident in self:
            if not accident.created_from_rental and accident.rental_contract_id:
                accident.rental_contract_id.has_extra_accident = True
        return accidents


class AccidentDueAmountLine(models.Model):
    _inherit = "accident.due.amount.line"

    def create_invoice(self):
        res = super().create_invoice()
        if self.default_accident_item_id.accident_item == 'customer' and self.accident_id.rental_contract_id:
            self.accident_id.rental_contract_id.current_accident_damage_amount += self.invoice_id.amount_total
            self.accident_id.rental_contract_id.reconcile_invoices_with_payments()
            self.accident_id.rental_contract_id.action_final_close()
        return res
