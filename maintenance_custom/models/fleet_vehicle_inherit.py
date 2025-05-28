# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    def action_view_maintenance_request(self):
        return {
            'name': 'Maintenance',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)]
        }