
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentGraceAgreementReport(models.Model):
    _name = 'payment.grace.agreement.report'
    _description = 'Payment Grace Agreement Report'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract')
    partner_id = fields.Many2one(
        'res.partner', related='rental_contract_id.partner_id', string='Customer', store=True)
    partner_mobile = fields.Char(
        string="Mobile Number", related='partner_id.mobile2', readonly=True, store=True)
    partner_id_no = fields.Char(
        string="ID No", related='partner_id.id_no', readonly=True, store=True)
    due_date = fields.Date('Due Date')
    company_currency_id = fields.Many2one(
        'res.currency', related='rental_contract_id.company_currency_id', string='currency', store=True)
    amount = fields.Monetary(
        'Amount', currency_field='company_currency_id')
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ], string='Payment Status', default='pending')

    installment_status = fields.Selection([
        ('not_due', 'Not Due'),
        ('over_due', 'OverDue'),
        ('paid', 'Paid')
    ], string='Installment Status', compute="_compute_installment_status")

    note = fields.Char('note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='state', default='draft')

    @api.depends('payment_status')
    def _compute_installment_status(self):
        for rec in self:
            if rec.payment_status == 'paid':
                rec.installment_status = 'paid'
            elif rec.due_date <= fields.Date.today():
                rec.installment_status = 'over_due'
            else:
                rec.installment_status = 'not_due'

    @api.constrains('state')
    def _check_amounts(self):
        for rec in self:
            if rec.state not in ('draft', 'cancelled'):
                contract_grace_amount = rec.rental_contract_id.grace_agreement_amount
                total_amount = rec.rental_contract_id.payment_grace_agreement_ids.filtered(
                    lambda l: l.state != 'cancelled').mapped('amount')
                if contract_grace_amount != total_amount:
                    raise ValidationError(
                        _(f"Total lines amount must be equal to {contract_grace_amount}"))
