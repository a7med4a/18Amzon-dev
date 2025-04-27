# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetAccident(models.Model):
    _inherit = "fleet.accident"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.')
