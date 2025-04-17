from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    vehicle_purchase_order_line_ids=fields.Many2many('vehicle.purchase.order.line',readonly=True)

    def action_view_vehicle_accessories(self):
        action = self.env['ir.actions.actions']._for_xml_id('vehicle_accessories.action_vehicle_accessories')
        return action
