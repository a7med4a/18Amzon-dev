# -*- coding: utf-8 -*-

from re import A
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VehicleStatusLog(models.Model):
    _name = "fleet.vehicle.status.log"
    _description = "Fleet Status Log"
    _rec_name = "fleet_vehicle_id"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fleet_state_id = fields.Many2one('fleet.vehicle.state', string='Status')
    branch_id = fields.Many2one('res.branch', string='Branch')
    count_days = fields.Integer('Count Days', default=1)
    last_update = fields.Date('Last Update', default=fields.Date.today())

    _sql_constraints = [
        ('unique_vehicle_date_log', 'UNIQUE(fleet_vehicle_id, last_update)',
         'Only one log for vehicle can created in one day')
    ]

    @api.model
    def _cron_daily_fleet_status_log(self):
        vals_list = []
        all_active_vehicles = self.env['fleet.vehicle'].search(
            [('active', '=', True)])
        for vehicle in all_active_vehicles:
            vals_list.append({
                'fleet_vehicle_id': vehicle.id,
                'branch_id': vehicle.branch_id.id,
                'fleet_state_id': vehicle.state_id.id
            })
        self.create(vals_list)
