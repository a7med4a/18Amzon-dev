# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Fleet(models.Model):
    _inherit = "fleet.vehicle"

    tracking_device_ids = fields.One2many(
        'vehicle.tracking.device', 'vehicle_id')
    tracking_device_count = fields.Integer(
        compute="_compute_tracking_device_count", store=True)

    @api.depends('tracking_device_ids')
    def _compute_tracking_device_count(self):
        for rec in self:
            rec.tracking_device_count = len(rec.tracking_device_ids)

    def view_related_tracking_device(self):
        self.ensure_one()
        return {
            'name': 'Tracking Device',
            'type': 'ir.actions.act_window',
            'res_model': 'vehicle.tracking.device',
            'domain': [('vehicle_id', '=', self.id)],
            'view_mode': 'list',
            'context': {'create': 0, 'edit': 0}
        }
