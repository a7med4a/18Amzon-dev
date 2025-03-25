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
        selection=[('spare_parts', 'Spare Parts'), ('tracking_device', 'Tracking Device'), ('other', 'Other'),],
        default='other')



