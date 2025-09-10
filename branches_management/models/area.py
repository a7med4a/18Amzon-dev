# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Area(models.Model):
    _name = 'res.area'
    _description = 'Area'

    name = fields.Char(required=True)
    state_id = fields.Many2one('res.country.state', string='City')
    country_id = fields.Many2one(
        'res.country', string='Country', related="state_id.country_id", store=True)
    branch_ids = fields.One2many(
        'res.branch', 'area_id', string='Branches')
    company_id = fields.Many2one('res.company', string='Company')
