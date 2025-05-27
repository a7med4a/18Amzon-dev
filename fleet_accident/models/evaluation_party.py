# -*- coding: utf-8 -*-

from odoo import models, fields


class EvaluationParty(models.Model):
    _name = "fleet.accident.evaluation.party"
    _description = "Accident Evaluation Party"

    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Type', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
