from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from odoo.osv import expression

class InheritFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    po_id=fields.Many2one('vehicle.purchase.order')


