# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContractFinesDiscountConfiguration(models.Model):
    _name = 'contract.fines.discount.config'
    _description = 'Contract Fines Discount Configuration'

    name = fields.Char(string='Name', required=True)
    type = fields.Selection([
        ('fine', 'Fine'),
        ('discount', 'Discount'),
    ], string='Type', required=True, default='fine')
    price = fields.Float(string='Price', required=True)
    account_id = fields.Many2one(
        'account.account', string='Account', required=True, domain="[('account_type', 'in', ['income', 'income_other'])]")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    tax_ids = fields.Many2many(
        'account.tax', string='taxes', domain="[('type_tax_use', '=', 'sale')]")
    contract_type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental')
