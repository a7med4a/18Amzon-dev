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

    @api.depends('usage_type')
    def _compute_is_truck(self):
        for rec in self:
            rec.is_truck = True if rec.usage_type == 'truck' else False
