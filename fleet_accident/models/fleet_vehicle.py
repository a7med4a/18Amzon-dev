# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Fleet(models.Model):
    _inherit = "fleet.vehicle"

    accident_ids = fields.One2many(
        'fleet.accident', 'fleet_vehicle_id')
    accident_count = fields.Integer(
        compute="_compute_accident_count", store=True)

    @api.depends('accident_ids')
    def _compute_accident_count(self):
        for rec in self:
            rec.accident_count = len(rec.accident_ids)

    def view_related_accident(self):
        self.ensure_one()
        return {
            'name': 'Accident',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.accident',
            'domain': [('fleet_vehicle_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'create': 0, 'edit': 0}
        }
