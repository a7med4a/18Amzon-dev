# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_third_party = fields.Boolean('Third Party', copy=False, default=False)
