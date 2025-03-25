# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    vehicle_status_log_ids = fields.One2many(
        'fleet.vehicle.status.log', 'fleet_vehicle_id', string='Status Log')
    status_log_count = fields.Integer(
        'Log Count', compute="_compute_status_log_count")

    @api.depends('vehicle_status_log_ids')
    def _compute_status_log_count(self):
        for vehicle in self:
            vehicle.status_log_count = len(vehicle.vehicle_status_log_ids)
