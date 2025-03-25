from odoo import models, fields, api, _


class PurchaseType(models.Model):
    _name = 'purchase.type'
    _description = 'Purchase Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    type = fields.Selection(
        selection=[('spare_parts', 'Spare Parts'), ('tracking_device', 'Tracking Device'), ('other', 'Other'), ],
        default='tracking_device', required=True)
    is_tracking_device = fields.Boolean(compute="_product_type", default=False)
    is_spare_parts = fields.Boolean(compute="_product_type",)
    product_id = fields.Many2one( comodel_name='product.template',required=True)


    @api.depends('type')
    def _product_type(self):
        for rec in self:
            is_tracking_device = False
            is_spare_parts = False
            if rec.type == 'tracking_device':
                is_tracking_device = True
            elif rec.type == 'spare_parts':
                is_spare_parts = True
            rec.is_tracking_device = is_tracking_device
            rec.is_spare_parts = is_spare_parts

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_type = fields.Selection(
        selection=[('tracking_device', 'Tracking Device'),('spare_parts', 'Spare Parts'),  ('other', 'Other'), ],
        default=lambda self:self.env['ir.config_parameter'].sudo().get_param('fleet_tracking_device.purchase_type'), store=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_type = fields.Selection(
        selection=[('spare_parts', 'Spare Parts'), ('tracking_device', 'Tracking Device'), ('other', 'Other'), ],
        default='tracking_device', config_parameter='fleet_tracking_device.purchase_type')
    purchase_name = fields.Char(string="Name",default="Purchase Type", config_parameter='fleet_tracking_device.purchase_name')



