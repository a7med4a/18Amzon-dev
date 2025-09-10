# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class FleetDamage(models.Model):
    _inherit = "fleet.damage"

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract NO.', domain="[('state','in',('opened','delivered_pending','delivered_debit','closed')),('partner_id','=',customer_id), ('company_id', '=', company_id)]")
    charged_waiting_contract = fields.Boolean(
        'Charged Waiting Contract', copy=False)
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle', required=False,
        compute="_compute_vehicle_id", store=True, readonly=False
    )
    created_from_rental = fields.Boolean(
        'Created From Rental', copy=False, default=False)

    @api.depends('rental_contract_id')
    def _compute_vehicle_id(self):
        for rec in self:
            if rec.rental_contract_id:
                rec.vehicle_id = rec.rental_contract_id.vehicle_id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.rental_contract_id = False
        return super()._onchange_company_id()

    def action_waiting_evaluation(self):
        res = super().action_waiting_evaluation()
        for rec in self:
            if not rec.created_from_rental and rec.rental_contract_id:
                rec.rental_contract_id.has_extra_damage = True
        return res

    def action_charge(self):
        res = super().action_charge()
        for rec in self:
            if rec.rental_contract_id:
                rec.rental_contract_id.current_accident_damage_amount += rec.total_include_tax
                rec.rental_contract_id.invoice_damage_accident = 'invoiced'
                rec.charged_waiting_contract = True
                rec.state = 'waiting_evaluation'
                rec.rental_contract_id.reconcile_invoices_with_payments()
                try:
                    rec.rental_contract_id.action_final_close()
                except:
                    continue
        return res

    def write(self, values):
        if values.get('state') == 'charged':
            return super(FleetDamage,
                         self.filtered(lambda d: (d.rental_contract_id and d.rental_contract_id.state == 'closed') or not d.rental_contract_id)).write(values)
        return super().write(values)
