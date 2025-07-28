# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    naql_id = fields.Char(
        string='Naql ID',
        help='Country ID from Naql Platform API',
        index=True
    )
    nationality_naql_id = fields.Char(
        string='Nationality Naql ID',
        help='Nationality ID from Naql Platform API (Yakeen)',
        index=True
    )