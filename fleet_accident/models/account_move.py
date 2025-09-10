# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    accident_due_amount_line_id = fields.Many2one(
        'accident.due.amount.line', string='Accident Due Amount Line')
    is_accident = fields.Boolean('Is Accident Invoice')

    def button_cancel(self):
        for rec in self:
            if rec.accident_due_amount_line_id and rec.accident_due_amount_line_id.invoice_id.id == rec.id:
                rec.accident_due_amount_line_id.write({'invoice_id': False})
        return super().button_cancel()
