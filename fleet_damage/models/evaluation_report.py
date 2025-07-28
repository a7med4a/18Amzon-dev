# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DamageEvaluationReport(models.Model):
    _name = "damage.evaluation.report"
    _description = "Damage Evaluation Report"

    name = fields.Char('Name')
    evaluation_ids = fields.One2many(
        'fleet.evaluation', 'evaluation_report_id', string='Evaluation Items')
    damage_id = fields.Many2one('fleet.damage', string='Damage')
    company_id = fields.Many2one(
        'res.company', related="damage_id.company_id", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')
    ], string='State', default="draft")
    warning_confirm_message = fields.Char(
        compute="_compute_warning_confirm_message", store=True)

    @api.depends('damage_id', 'damage_id.evaluation_report_ids.state')
    def _compute_warning_confirm_message(self):
        for rec in self:
            damage_confirmed_evaluation = self.damage_id.evaluation_report_ids.filtered(
                lambda e: e.state == 'confirmed')
            if rec.state == 'draft' and damage_confirmed_evaluation:
                rec.warning_confirm_message = f"There is another confirmed evaluation ({damage_confirmed_evaluation.name})"
            else:
                rec.warning_confirm_message = False

    def action_confirm(self):
        self.ensure_one()
        if self.warning_confirm_message and not self._context.get('wizard_confirm'):
            view_id = self.env.ref(
                'fleet_damage.confirm_warning_damage_evaluation_report_view_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirm Evaluation'),
                'res_model': 'damage.evaluation.report',
                'target': 'new',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [[view_id, 'form']]
            }
        else:
            self.damage_id.evaluation_report_ids.filtered(
                lambda e: e.state == 'confirmed').write({'state': 'rejected'})
            self.damage_id.confirmed_evaluation_report_id = self.id
            self.write({'state': 'confirmed'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fleet.damage.evaluation.seq')
        evaluation_reports = super().create(vals_list=vals_list)
        return evaluation_reports
