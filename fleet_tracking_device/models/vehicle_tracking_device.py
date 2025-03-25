
from odoo import models, fields, api, _


class SerialNumberInherit(models.Model):
    _inherit = 'stock.lot'

    is_tracking_device = fields.Boolean(related="product_id.categ_id.is_tracking_device", default=True)
    is_spare_parts = fields.Boolean(related="product_id.categ_id.is_spare_parts", default=True)
    purchase_type=fields.Selection(related="product_id.categ_id.purchase_type",store=True)
    is_linked = fields.Boolean(readonly=True)
    vehicle_tracking_device_id = fields.Many2one( comodel_name='vehicle.tracking.device')
    state = fields.Selection(
        string='State',
        selection=[('new', 'New'), ('used', 'Used'), ('working', 'Working'), ('damaged', 'Damaged'), ], default="new")


class VehicleTrackingDevice(models.Model):
    _name = 'vehicle.tracking.device'
    _description = 'Vehicle Tracking Device'
    _order = 'id desc'

    vehicle_id = fields.Many2one( comodel_name='fleet.vehicle',  string='License Plate',required=True)
    tracking_device_ids = fields.One2many( comodel_name='stock.lot',inverse_name='vehicle_tracking_device_id',required=True)
    card_number = fields.Char(string='Card Number', required=True)
    device_state = fields.Selection(selection=[('working', 'Working'), ('not_working', 'Not Working')],required=True,default='working')

    @api.model_create_multi
    def create(self, values):
        res = super().create(values)
        for rec in res.tracking_device_ids:
            rec.write({'is_linked': True})
        return res

    def write(self, values):
        res=None
        for rec in self:
            if 'tracking_device_ids' in values :
                for device in rec.tracking_device_ids:
                    device.write({'is_linked': False})
            res = super().write(values)
            if 'tracking_device_ids' in values :
                for device in rec.tracking_device_ids:
                    device.write({'is_linked': True})
        return res



