# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    accident_due_amount_line_id = fields.Many2one(
        'accident.due.amount.line', string='Accident Due Amount Line')
    is_accident = fields.Boolean('Is Accident Invoice')
