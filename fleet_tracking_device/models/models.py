from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from odoo.osv import expression

class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    is_tracking_device = fields.Boolean(default=False)
    is_spare_parts = fields.Boolean(default=False)
    purchase_type = fields.Selection(
        selection=[('Spare Parts', 'Spare Parts'), ('Tracking Device', 'Tracking Device'), ('Other', 'Other'),],
        default='other')
    purchase_type_id = fields.Many2one(comodel_name='purchase.type.names')



