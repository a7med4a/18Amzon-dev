from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    po_id=fields.Many2one('vehicle.purchase.order')
    vehicle_purchase_order_line_ids=fields.Many2many('vehicle.purchase.order.line',readonly=True)



