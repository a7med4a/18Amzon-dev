# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    branch_tracking_ids = fields.One2many(
        'fleet.branch.tracking', 'fleet_id', string='Branch Tracking')
    branch_tracking_count = fields.Integer(
        'Branch Tracking Count', compute='_compute_branch_tracking_count', store=True)

    @api.depends('branch_tracking_ids')
    def _compute_branch_tracking_count(self):
        for record in self:
            record.branch_tracking_count = len(record.branch_tracking_ids)

    def write(self, vals):
        if 'branch_id' in vals:
            tracking_vals_list = []
            for vehicle in self:
                tracking_vals = {
                    'fleet_id': vehicle.id,
                    'from_branch_id': vehicle.branch_id.id,
                    'to_branch_id': vals.get('branch_id') if vals.get('branch_id') else False,
                }
                if not self._context.get('external_change'):
                    tracking_vals.update({'type': 'manual'})
                else:
                    if self._context.get('rental_id'):
                        tracking_vals.update({
                            'type': 'rental',
                            'rental_id': self._context.get('rental_id')
                        })
                    elif self._context.get('route_id'):
                        vehicle_route = self.env['vehicle.route'].browse(
                            self._context.get('route_id'))
                        if vehicle_route:
                            tracking_vals.update({
                                'type': 'route',
                                'route_id': vehicle_route.branch_route_id.id,
                            })
                tracking_vals_list.append(tracking_vals)
            self.env['fleet.branch.tracking'].create(tracking_vals_list)
        return super().write(vals)

    def view_related_branch_tracking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Branch Tracking'),
            'res_model': 'fleet.branch.tracking',
            'view_mode': 'list,form',
            'domain': [('fleet_id', '=', self.id)],
            'context': {'create': 0}
        }
