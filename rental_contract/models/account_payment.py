# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', readonly=True)
