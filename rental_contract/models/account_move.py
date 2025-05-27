# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', readonly=True)
    invoice_log_id = fields.Many2one(
        'rental.contract.schedular.invoice.log', string='invoice_log')
    payment_type_selection = fields.Selection(
        string='Payment Type Selection',
        selection=[('advance', 'مقدم'), ('extension', 'تمديد'), ('close', 'إغلاق'), ('debit', 'سداد مديونية'), ('extension_offline', 'تمديد بدون منصة'),
                   ('suspended_payment', 'سداد عقد معلق'), ],
        required=True, )

    def button_cancel(self):
        res = super().button_cancel()
        if self.damage_id and self.damage_id.rental_contract_id:
            self.damage_id.rental_contract_id.current_accident_damage_amount = 0
        return res

    def unlink(self):
        res = super().button_cancel()
        if self.damage_id and self.damage_id.rental_contract_id:
            self.damage_id.rental_contract_id.current_accident_damage_amount = 0
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    rental_contract_duration = fields.Char('Duration')
