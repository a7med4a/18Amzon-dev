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

    owner_name = fields.Char(string="Owner name")
    owner_id = fields.Char(string="Owner Id")
    insurance_policy_line_ids = fields.One2many(
        comodel_name='insurance.policy.line',
        inverse_name='vehicle_id',
        required=False)
    vehicle_color2 = fields.Char('Color')


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not name:
            return super().name_search(name, args, operator, limit)

        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        is_positive = operator not in expression.NEGATIVE_TERM_OPERATORS
        domain = args or []
        vehicle = self.env['fleet.vehicle']

        if operator in positive_operators:
            vehicle = self.search(expression.AND([domain, [('vin_sn', '=', name)]]), limit=limit)

        if not vehicle:
            if is_positive:
                vehicle = self.search(expression.AND([domain, [('vin_sn', operator, name)]]), limit=limit)
                limit_rest = limit - len(vehicle) if limit else None

                if limit_rest is None or limit_rest > 0:
                    vehicle |= self.search(expression.AND([
                        domain,
                        [('id', 'not in', vehicle.ids), '|', ('vin_sn', operator, name), ('name', operator, name)]
                    ]), limit=limit_rest)
            else:
                domain_neg = [('name', operator, name), ('vin_sn', operator, name)]
                vehicle = self.search(expression.AND([domain, domain_neg]), limit=limit)

        return [(rec.id, rec.display_name) for rec in vehicle.sudo()]

    def policy_log(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'insurance.policy.line',
            'views': [[self.env.ref('fleet_insurance.policy_line_view_tree').id, 'list']],
            'domain': [('vehicle_id', '=', self.id)],
        }


