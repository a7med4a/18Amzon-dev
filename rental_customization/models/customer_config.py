# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class IndividualCustomerConfig(models.Model):
    _name = 'individual.customer.config'
    _description = 'Individual Customer Configration'
    _rec_name = 'account_receivable_id'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([('type', '=', 'rental')], order="id desc", limit=1)
        if config:
            field_names = ['category_id', 'account_receivable_id']
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field] for field in field_names
            })
        return result

    category_id = fields.Many2many('res.partner.category', string='Tags')
    account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     ondelete='restrict')
    is_default = fields.Boolean(string="Set Default")
    type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental')

    @api.model_create_multi
    def create(self, vals_list):
        config=False
        for vals in vals_list:
            config = self.search([('type', '=', vals['type'])], order="id desc", limit=1)
            if config:
                config.write(vals)
            else:
                config=super().create(vals_list)
        return config



