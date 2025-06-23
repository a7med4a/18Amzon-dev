# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression


class Partner(models.Model):

    _inherit = 'res.partner'
    _rec_names_search = ['complete_name',
                         'email', 'ref', 'vat', 'company_registry', 'mobile2', 'id_no']

    rental_contact_ids = fields.One2many(
        'rental.contract', 'partner_id')
    rental_contact_count = fields.Integer(
        compute="_compute_rental_contact_count", store=True)

    @api.depends('rental_contact_ids')
    def _compute_rental_contact_count(self):
        for rec in self:
            rec.rental_contact_count = len(rec.rental_contact_ids)

    def view_related_rental_contact(self):
        self.ensure_one()
        return {
            'name': 'Rental Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.contract',
            'domain': [('partner_id', '=', self.id)],
            'view_mode': 'list',
            'context': {'create': 0, 'edit': 0}
        }
