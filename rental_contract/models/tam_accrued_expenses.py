# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TamAccruedExpenses(models.Model):
    _name = 'tam.accrued.expenses'
    _description = 'Tam Accrued Expenses'
    _rec_name = 'rental_contract_id'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract')
    auth_start_date = fields.Date('Auth Start Date')
    auth_end_date = fields.Date('Auth End Date')
    amount = fields.Float('Amount')
