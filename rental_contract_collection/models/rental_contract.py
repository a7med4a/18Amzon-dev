# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RentalContract(models.Model):
    _inherit = 'rental.contract'

    collector_user_ids = fields.Many2many('res.users', string='Collector')

    collection_action_ids = fields.One2many(
        'collection.action.report', 'rental_contract_id', string='Collection Actions')
    collection_action_count = fields.Integer(
        'damage Count', compute="_compute_collection_action", store=True)

    payment_grace_agreement_ids = fields.One2many(
        'payment.grace.agreement.report', 'rental_contract_id', string='Payment Grace Agreements')
    payment_grace_agreement_count = fields.Integer(
        'damage Count', compute="_compute_payment_grace_agreement_count", store=True)

    grace_agreement_amount = fields.Monetary(
        'Grace Agreement Amount', currency_field='company_currency_id', copy=False)

    @api.depends('collection_action_ids')
    def _compute_collection_action(self):
        for rec in self:
            rec.collection_action_count = len(rec.collection_action_ids)

    @api.depends('payment_grace_agreement_ids')
    def _compute_payment_grace_agreement_count(self):
        for rec in self:
            rec.payment_grace_agreement_count = len(
                rec.payment_grace_agreement_ids)

    def action_view_all_contracts(self):
        collection_obj = self.env['collection.setting'].search([])
        view_id = self.env.ref(
            "rental_contract_collection.view_rental_contract_form").id
        if self.env.user in collection_obj.allowed_all_contract_user_ids:
            self.search([])._compute_display_open_state_fields()
            matched_contracts = self.search(
                ['|',
                    ('state', 'in', collection_obj.rental_contract_status_ids.mapped('value')),
                    '&',
                    ('state', '=', 'opened'),
                    ('late_days', '>=', collection_obj.allowed_late_days)
                 ])
            domain = [('id', 'in', matched_contracts.ids)]
        else:
            domain = [('id', '=', [])]
        return {
            'type': 'ir.actions.act_window',
            'name': _('All Contracts'),
            'res_model': 'rental.contract',
            'domain': domain,
            'views': [(False, 'list'), (view_id, 'form')],
            'view_mode': 'list,form',
            'context': {'create': False},
        }

    def action_view_my_contracts(self):
        collection_obj = self.env['collection.setting'].search([])
        view_id = self.env.ref(
            "rental_contract_collection.view_rental_contract_form").id
        if self.env.user in collection_obj.allowed_own_contract_user_ids:
            self.search([])._compute_display_open_state_fields()
            matched_contracts = self.search(
                [
                    ('collector_user_ids', 'in', self.env.user.ids),
                    '|',
                    ('state', 'in', collection_obj.rental_contract_status_ids.mapped('value')),
                    '&',
                    ('state', '=', 'opened'),
                    ('late_days', '>=', collection_obj.allowed_late_days)
                ])
            domain = [('id', 'in', matched_contracts.ids)]
        else:
            domain = [('id', '=', [])]
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Contracts'),
            'res_model': 'rental.contract',
            'domain': domain,
            'views': [(False, 'list'), (view_id, 'form')],
            'view_mode': 'list,form',
            'context': {'create': False},
        }

    def view_related_collection_actions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Collection Actions'),
            'res_model': 'collection.action.report',
            'view_mode': 'list',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'create': 0}
        }

    def view_related_payment_grace_agreements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Grace Agreement'),
            'res_model': 'payment.grace.agreement.report',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'create': 0, 'delete': 0}
        }
