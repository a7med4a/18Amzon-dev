# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VehicleStatus(models.Model):
    _inherit = 'fleet.vehicle.state'

    allow_transfer = fields.Boolean('Allow Transfer')
