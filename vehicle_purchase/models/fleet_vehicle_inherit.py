from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    po_id=fields.Many2one('vehicle.purchase.order')
    vehicle_purchase_order_line_ids=fields.Many2many('vehicle.purchase.order.line',readonly=True)

    def write(self, values):
        for rec in self :
           res = super(InheritFleetVehicle, self).write(values)
           align_items=self.env['account.move.line'].search([('vehicle_id','=',self.id)])
           print("align_items",align_items ,values.get('license_plate'))
           if values.get('license_plate') and align_items:
               align_items.write({'name': rec.display_name})
           if (values.get('vin_sin') or values.get('license_plate') )and align_items:
               align_items.write({'analytic_distribution': {
                        rec.analytic_account_id.id: 100,
                    }})
           return res
        return None

