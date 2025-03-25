# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EvaluationItem(models.Model):
    _name = "fleet.accident.evaluation.item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Accident Evaluation Items"

    name = fields.Char('Name', required=True)
