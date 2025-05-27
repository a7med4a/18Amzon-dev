# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EvaluationItem(models.Model):
    _name = "fleet.accident.evaluation.item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Accident Evaluation Items"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
