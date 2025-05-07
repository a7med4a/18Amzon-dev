# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Fleet(models.Model):
    _inherit = "fleet.vehicle"

    rental_contact_ids = fields.One2many(
        'rental.contract', 'vehicle_id')
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
            'domain': [('vehicle_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'create': 0, 'edit': 0}
        }
