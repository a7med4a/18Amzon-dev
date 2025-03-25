# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Vehicle Information
    vin_sn_length = fields.Integer('Chassis NO/SN Length', default=17)
    license_plate_length = fields.Integer('License Plate Length', default=10)
