# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Journal(models.Model):
    _inherit = 'account.journal'

    branch_id = fields.Many2one('res.branch', string='Branch')
