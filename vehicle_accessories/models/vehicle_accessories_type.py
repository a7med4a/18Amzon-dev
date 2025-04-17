from email.policy import default

from odoo import models, fields, api, _



class VehicleAccessoriesType(models.Model):
    _name = 'vehicle.accessories.type'
    _description='Vehicle Accessories Type'
    _rec_name="name"

    name = fields.Char(string="Name")

