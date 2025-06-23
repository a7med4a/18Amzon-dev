# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    police_alert_state = fields.Selection([
        ('alert', 'Alert'),
        ('blacklisted', 'Blacklisted'),
    ], string='Police Alert State', tracking=True)
