# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RentalConfigSettings(models.Model):
    _name = 'rental.config.settings'
    _description = 'Rental Default Settings'
    _rec_name = 'company_id'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([('type', '=', 'rental')],
                             order="id desc", limit=1)
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
    in_attachment_image_required = fields.Integer('In Attachment Image Required',
                                                  default=6, help="Number of images required for the rental contract to be considered valid.")
    out_attachment_image_required = fields.Integer('Out Attachment Image Required',
                                                   default=6, help="Number of images required for the rental contract to be considered valid.")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            config = self.search(
                [('type', '=', vals['type'])], order="id desc", limit=1)
            if config:
                config.write(vals)
                return config
        return super().create(vals_list)
