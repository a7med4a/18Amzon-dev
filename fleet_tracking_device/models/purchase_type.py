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

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    def _get_purchase_type_ids(self):
        purchase_type_ids = self.env['ir.config_parameter'].sudo().get_param(
            'fleet_tracking_device.purchase_type_ids', default='[]'
        )
        ids = eval(purchase_type_ids) if purchase_type_ids else []
        return ids if isinstance(ids, list) else []

    purchase_type_id = fields.Many2one(
        comodel_name='purchase.type.names',
        string='Purchase Type',
        domain=lambda self: [
            ('id', 'in', self._get_purchase_type_ids())
        ],
        help='Select the purchase type for this fleet tracking device.'
    )

    def write(self, values):
        res=super(PurchaseOrderInherit, self).write(values)
        if values.get('purchase_type_id'):
            self.order_line.unlink()
        return res


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_type_ids = fields.Many2many(
        comodel_name='purchase.type.names',
        string='Purchase Types',
        help='Select the purchase types for fleet tracking devices.'
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'fleet_tracking_device.purchase_type_ids',
            self.purchase_type_ids.ids
        )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        purchase_type_ids = self.env['ir.config_parameter'].sudo().get_param('fleet_tracking_device.purchase_type_ids', default='[]')
        purchase_type_ids = eval(purchase_type_ids) if purchase_type_ids else []
        res.update(
            purchase_type_ids=[(6, 0, purchase_type_ids)] if purchase_type_ids else False
        )
        return res


class PurchaseTypeNames(models.Model):
    _name = 'purchase.type.names'
    _description = 'Purchase Type Names'

    name = fields.Char(required=True)