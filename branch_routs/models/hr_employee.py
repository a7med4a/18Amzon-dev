# -*- coding: utf-8 -*-

from odoo import fields, models


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_driver = fields.Boolean('Driver', copy=False, default=False)
