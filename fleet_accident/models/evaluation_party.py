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
