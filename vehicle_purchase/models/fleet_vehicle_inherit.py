from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    po_id=fields.Many2one('vehicle.purchase.order')
    vehicle_purchase_order_line_ids=fields.Many2many('vehicle.purchase.order.line',readonly=True)

    def write(self, values):
        res = super(InheritFleetVehicle, self).write(values)
        for rec in self :
            align_items=self.env['account.move.line'].search([('vehicle_id','=',self.id)])
            align_assets=self.env['account.asset'].search([('vehicle_id','=',self.id)])
            if  values.get('license_plate') or values.get('vin_sin') :
                if align_items:
                    align_items.write({'name': rec.display_name,'analytic_distribution': {
                        rec.analytic_account_id.id: 100,
                    }})
                if align_assets:
                    align_assets.write({'name': rec.display_name,'analytic_distribution': {
                        rec.analytic_account_id.id: 100,
                    }})
        return res

