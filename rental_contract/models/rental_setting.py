# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RentalConfigSettings(models.Model):
    _name = 'rental.config.settings'
    _description = 'Rental Default Settings'
    _rec_name = 'company_id'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([], order="id desc", limit=1)
        if config:
            field_names = ['trip_days_account_id', 'trip_days_label',
                           'extra_km_account_id', 'extra_km_label']
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field] for field in field_names
            })
            result['tax_ids'] = [(6, 0, config.tax_ids.ids)]

        return result

    trip_days_account_id = fields.Many2one(
        "account.account", required=True, string="Trip Days Account")
    trip_days_label = fields.Char(string="Trip Days Label", required=True)
    extra_km_account_id = fields.Many2one(
        "account.account", required=True, string="Extra KM Account")
    extra_km_label = fields.Char(string="Extra KM Label", required=True)
    tax_ids = fields.Many2many('account.tax', string="Taxes", domain=[
                               ("type_tax_use", "=", "sale")])
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        config = self.search([], order="id desc", limit=1)
        if config and vals_list:
            # if many vals get first one
            val = vals_list[0]
            tax_list = val.pop('tax_ids')
            tax_ids = []
            for tax in tax_list:
                tax_ids.append(tax[1])
            val.update({
                'tax_ids': [(6, 0, tax_ids)]
            })
            config.write(val)
            return config
        return super().create(vals_list)
