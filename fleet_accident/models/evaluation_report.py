# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccidentEvaluationReport(models.Model):
    _name = "accident.evaluation.report"
    _description = "Accident Evaluation Report"

    name = fields.Char('Name')
    evaluation_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Evaluation Type')
    evaluation_party_id = fields.Many2one(
        'fleet.accident.evaluation.party', string='Evaluation Party', domain="[('company_id', '=', company_id)]")
    evaluation_item_ids = fields.One2many(
        'accident.evaluation.item.line', 'evaluation_report_id', string='Evaluation Items')
    total_evaluation = fields.Float(
        'Total Evaluation', compute="_compute_total_evaluation", store=True)
    compensation_type = fields.Selection([
        ('full', 'Full'),
        ('third', 'Third')
    ], string='Compensation Type')
    accident_id = fields.Many2one('fleet.accident', string='Accident')
    company_id = fields.Many2one(
        'res.company', related="accident_id.company_id", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')
    ], string='State', default="draft")
    warning_confirm_message = fields.Char(
        compute="_compute_warning_confirm_message", store=True)

    @api.depends('evaluation_item_ids', 'evaluation_item_ids.evaluation_item_value')
    def _compute_total_evaluation(self):
        for rec in self:
            rec.total_evaluation = sum(
                rec.evaluation_item_ids.mapped('evaluation_item_value'))

    @api.depends('accident_id', 'accident_id.evaluation_report_ids.state')
    def _compute_warning_confirm_message(self):
        for rec in self:
            accident_confirmed_evaluation = self.accident_id.evaluation_report_ids.filtered(
                lambda e: e.state == 'confirmed')
            if rec.state == 'draft' and accident_confirmed_evaluation:
                rec.warning_confirm_message = f"There is another confirmed evaluation ({accident_confirmed_evaluation.name})"
            else:
                rec.warning_confirm_message = False

    def action_confirm(self):
        self.ensure_one()
        if self.warning_confirm_message and not self._context.get('wizard_confirm'):
            view_id = self.env.ref(
                'fleet_accident.confirm_warning_accident_evaluation_report_view_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirm Evaluation'),
                'res_model': 'accident.evaluation.report',
                'target': 'new',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [[view_id, 'form']]
            }
        else:
            self.accident_id.evaluation_report_ids.filtered(
                lambda e: e.state == 'confirmed').write({'state': 'rejected'})
            self.accident_id.confirmed_evaluation_report_id = self.id
            self.write({'state': 'confirmed'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fleet.accident.evaluation.seq')
        evaluation_reports = super().create(vals_list=vals_list)
        return evaluation_reports
