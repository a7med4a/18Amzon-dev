# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DefaultAccidentItem(models.Model):
    _name = "default.accident.item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Default Accident Items"
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    accident_item = fields.Selection([
        ('customer', 'Customer'),
        ('other_party', 'Other Party'),
        ('amazon', 'Amazon Insurance Company'),
    ], string='Accident Item', required=True)
    name = fields.Char('Description', required=True, translate=True)
    compensation_type = fields.Selection([
        ('full', 'Full'),
        ('third', 'Third'),
        ('both', 'Both')
    ], string='Compensation Type', required=True)
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    account_id = fields.Many2one(
        'account.account', string='Account', required=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    _sql_constraints = [
        ('accident_item_uniq', 'unique(accident_item)',
         'Accident Item must be unique!'),
    ]
