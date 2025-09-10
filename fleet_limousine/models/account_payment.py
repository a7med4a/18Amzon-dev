# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    limousine_contract_id = fields.Many2one('limousine.contract', string='Limousine Contract')
