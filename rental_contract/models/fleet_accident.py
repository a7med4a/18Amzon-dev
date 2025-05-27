# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetAccident(models.Model):
    _inherit = "fleet.accident"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.')


class AccidentDueAmountLine(models.Model):
    _inherit = "accident.due.amount.line"

    def _prepare_invoice_vals(self):
        res = super()._prepare_invoice_vals()
        if self.default_accident_item_id.accident_item == 'customer' and self.accident_id.rental_contract_id:
            self.accident_id.rental_contract_id.current_accident_damage_amount += self.to_invoice_amount
            self.accident_id.rental_contract_id.update_state_after_close()
        return res
