from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


class InheritResBranch(models.Model):
    _inherit = 'res.branch'

    route_ids = fields.Many2many('stock.route')
