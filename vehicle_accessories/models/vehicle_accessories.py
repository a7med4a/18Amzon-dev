
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta


class VehicleAccessories(models.Model):
    _name = 'vehicle.accessories'
    _description='Vehicle Accessories'

    vehicle_accessories_type_id =fields.Many2one('vehicle.accessories.type', required=True)
    description = fields.Text( string="Description",required=False)
    count = fields.Integer(required=True)


