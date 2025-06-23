# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RentalContract(models.Model):
    _inherit = 'rental.contract'

    police_alert_state = fields.Selection([
        ('alert', 'Alert'),
        ('blacklisted', 'Blacklisted'),
    ], string='Police Alert State', tracking=True)

    police_alert_request_count = fields.Integer(
        'Police Alert Request Count', compute="_compute_police_alert_request_count", store=True)

    police_alert_request_ids = fields.One2many(
        'police.alert', 'rental_contract_id', string='Police Alert Requests')

    vehicle_id = fields.Many2one('fleet.vehicle',
                                 domain=lambda self: [('branch_id', 'in', self.env.branches.ids), ('state_id.type', '=', 'ready_to_rent'), ('company_id', '=', self.env.company.id), ('police_alert_state', '=', False)])

    @api.depends('police_alert_request_ids')
    def _compute_police_alert_request_count(self):
        for rec in self:
            rec.police_alert_request_count = len(rec.police_alert_request_ids)

    def view_create_police_alert_popup(self):
        view_id = self.env.ref(
            'legal_department.view_create_contract_police_alert_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Police Alert'),
            'res_model': 'police.alert',
            'target': 'new',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'context': {
                'default_rental_contract_id': self.id,
            }
        }

    def view_related_police_alert_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Police Alert'),
            'res_model': 'police.alert',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id)]
        }
