# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PoliceAlert(models.Model):
    _name = 'police.alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Police Alert'

    # Contract Details
    name = fields.Char(string='Name')
    rental_contract_id = fields.Many2one(
        comodel_name='rental.contract',
        string='Rental Contract',
        required=True,
        ondelete='cascade',
    )
    fleet_vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Fleet Vehicle',
        related='rental_contract_id.vehicle_id',
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='rental_contract_id.partner_id',
        store=True,
    )
    description = fields.Text(string='Description', required=True)

    # Request Details
    request_no = fields.Char('Request NO.')
    dispatch_no = fields.Char('Dispatch NO.')
    request_date = fields.Date('Request Date')

    police_alert_decision_ids = fields.One2many(
        'police.alert.decision', 'police_alert_request_id', string='Police Alert Decisions')

    state = fields.Selection([
        ('under_process', 'Under Process'),
        ('decision_34', 'Decision 34'),
        ('decision_68', 'Decision 68'),
        ('decision_68', 'Decision 68'),
        ('blacklisted', 'Blacklisted'),
        ('investigation_hold', 'Investigation Hold'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='State', default="under_process", tracking=True)

    reject_reason = fields.Text('Reject Reason')

    def decision_34_action(self):
        for request in self:
            request.state = 'decision_34'
            request.police_alert_decision_ids = [
                (0, 0, {'decision_number': 34})]

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_under_process(self):
        self.write({'state': 'under_process'})

    def decision_68_action(self):
        for request in self:
            request.state = 'decision_68'
            request.police_alert_decision_ids = [
                (0, 0, {'decision_number': 68})]

    def action_black_listed(self):
        self.write({'state': 'blacklisted'})
        self.rental_contract_id.write({'police_alert_state': 'blacklisted'})
        self.fleet_vehicle_id.write({'police_alert_state': 'blacklisted'})

    def action_investigation_hold(self):
        self.write({'state': 'investigation_hold'})
        self.rental_contract_id.write({'police_alert_state': False})
        self.fleet_vehicle_id.write({'police_alert_state': False})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'police.alert.seq')
        requests = super().create(vals_list)
        requests.rental_contract_id.write({'police_alert_state': 'alert'})
        requests.fleet_vehicle_id.write({'police_alert_state': 'alert'})
        return requests

    def view_reject_reason_popup(self):
        view_id = self.env.ref(
            'legal_department.view_police_alert_reject_reason_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Reason'),
            'res_model': 'police.alert',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [[view_id, 'form']]
        }


class PoliceAlertDecision(models.Model):
    _name = 'police.alert.decision'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Police Alert Decision'
    _rec_name = 'decision_number'

    police_alert_request_id = fields.Many2one(
        'police.alert', string='Police Alert Request')
    decision_number = fields.Char('Decision Number', required=True)
    decision_date = fields.Date('Decision Date')
    description = fields.Char('Decision Description')
