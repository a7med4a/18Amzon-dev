# -*- coding: utf-8 -*-

from ast import Raise
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VehicleRoute(models.Model):
    _inherit = 'vehicle.route'

    def update_fleet(self, type):
        return super(VehicleRoute, self.with_context(external_change=True, route_id=self.id)).update_fleet(type)
