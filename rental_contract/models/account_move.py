# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', readonly=True)
    invoice_log_id = fields.Many2one(
        'rental.contract.schedular.invoice.log', string='invoice_log')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    rental_contract_duration = fields.Char('Duration')
