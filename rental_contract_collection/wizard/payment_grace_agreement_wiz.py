# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class PaymentGraceAgreementWiz(models.TransientModel):
    _name = 'payment.grace.agreement.wiz'
    _description = 'Payment Grace Agreement Wiz'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract')
    start_date = fields.Date('Start Date')
    duration = fields.Integer('Duration')
    duration_type = fields.Selection([
        ('day', 'Days'),
        ('month', 'Months')
    ], string='Duration Type', default='month')

    installment_count = fields.Integer('Installment Count')
    discount_percentage = fields.Float('Discount(%)')
    discount_amount = fields.Float('Discount Amount')
    company_currency_id = fields.Many2one(
        'res.currency', related='rental_contract_id.company_currency_id', string='currency', store=True)
    due_amount = fields.Monetary(
        'Due Amount', related='rental_contract_id.current_due_amount', store=True, currency_field='company_currency_id')

    note = fields.Char('note')

    @api.constrains('duration', 'installment_count')
    def _check_installments(self):
        for rec in self:
            if rec.installment_count and rec.duration and rec.duration % rec.installment_count:
                raise ValidationError(_("Adjust Installment No and duration!"))

    def action_confirm(self):
        for rec in self:
            if not rec.installment_count or not rec.duration:
                raise ValidationError(
                    _("Insert Duration and installment count!"))
            net_amount = rec.due_amount
            if rec.discount_percentage:
                net_amount -= (rec.due_amount *
                               (rec.discount_percentage / 100))
            if rec.discount_amount:
                net_amount -= rec.discount_amount

            vals_list = []
            due_date = rec.start_date
            for time in range(rec.installment_count):
                if rec.duration_type == 'month':
                    due_date += relativedelta(months=time)
                else:
                    due_date += relativedelta(days=time)

                vals_list.append({
                    'due_date': due_date,
                    'rental_contract_id': rec.rental_contract_id.id,
                    'amount': net_amount / rec.installment_count,
                    'note': rec.note
                })

            self.env['payment.grace.agreement.report'].create(vals_list)
            rec.rental_contract_id.grace_agreement_amount = net_amount
