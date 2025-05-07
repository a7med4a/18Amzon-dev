# -*- coding: utf-8 -*-

from odoo import fields, models, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_truck = fields.Boolean('Truck', compute="_compute_is_truck", store=True)
    usage_type = fields.Selection(selection_add=[
        ('truck', 'Truck'),
    ],
        ondelete={
            'truck': 'cascade',
    })

    vehicle_route_ids = fields.One2many(
        'vehicle.route', 'fleet_vehicle_id')
    vehicle_route_count = fields.Integer(
        compute="_compute_vehicle_route_count", store=True)

    @api.depends('vehicle_route_ids')
    def _compute_vehicle_route_count(self):
        for rec in self:
            rec.vehicle_route_count = len(rec.vehicle_route_ids)

    def view_related_vehicle_routes(self):
        self.ensure_one()
        return {
            'name': 'Routes',
            'type': 'ir.actions.act_window',
            'res_model': 'vehicle.route',
            'domain': [('fleet_vehicle_id', 'in', self.ids)],
            'view_mode': 'list,form',
            'context': {'create': 0, 'edit': 0}
        }

    @api.depends('usage_type')
    def _compute_is_truck(self):
        for rec in self:
            rec.is_truck = True if rec.usage_type == 'truck' else False
