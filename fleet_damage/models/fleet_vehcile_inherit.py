from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not name:
            return super().name_search(name, args, operator, limit)

        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        is_positive = operator not in expression.NEGATIVE_TERM_OPERATORS
        domain = args or []
        vehicle = self.env['fleet.vehicle']

        if operator in positive_operators:
            vehicle = self.search(expression.AND([domain, [('license_plate', '=', name)]]), limit=limit)

        if not vehicle:
            if is_positive:
                vehicle = self.search(expression.AND([domain, [('license_plate', operator, name)]]), limit=limit)
                limit_rest = limit - len(vehicle) if limit else None
                if limit_rest is None or limit_rest > 0:
                    vehicle |= self.search(expression.AND([
                        domain,
                        [('id', 'not in', vehicle.ids), '|', ('license_plate', operator, name), ('name', operator, name)]
                    ]), limit=limit_rest)
            else:
                domain_neg = [('name', operator, name), ('license_plate', operator, name)]
                vehicle = self.search(expression.AND([domain, domain_neg]), limit=limit)
        return [(rec.id, rec.display_name) for rec in vehicle.sudo()]



