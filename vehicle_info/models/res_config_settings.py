# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Vehicle Information
    vin_sn_length = fields.Integer(
        'Chassis NO/SN Length', related='company_id.vin_sn_length', readonly=False)
    license_plate_length = fields.Integer(
        'License Plate Length', related='company_id.license_plate_length', readonly=False)
