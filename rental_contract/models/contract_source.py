# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContractSource(models.Model):
    _name = 'contract.source'
    _description = 'Contract Source'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string="Sequence")
    reservation_number = fields.Boolean(string='Reservation Number')


