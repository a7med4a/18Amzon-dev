from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from odoo.osv import expression


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    is_damage_invoice = fields.Boolean(default=False)
    damage_id = fields.Many2one(
        comodel_name='fleet.damage',
        string='Damage',
        required=False)
