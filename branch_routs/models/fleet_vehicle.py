# -*- coding: utf-8 -*-

from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_truck = fields.Boolean('Truck', copy=False, default=False)
