# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class VehiclePaymentRegister(models.TransientModel):
    _name = 'vehicle.purchase.payment.register'
    _description = 'Vehicle Register Payment'


    def _default_currency(self):
        po = self.env['vehicle.purchase.order'].browse(
            self._context.get('active_id'))
        return po.company_id.currency_id.id

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method')
    payment_date = fields.Date(
        string='Payment Date', required=True, default=fields.Date.today())
    amount = fields.Float(string='Amount', required=True, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', default=_default_currency, string='Currency', readonly=True)
    communication = fields.Char(string='Memo')
    pay_type = fields.Selection(
        string='Pay_type',
        selection=[('advance', 'Advanced Payment'),
                   ('installment', 'Pay Installment'), ],
        required=False, )

    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_payment_method_line_fields')

    @api.depends('journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            if wizard.journal_id:
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines(
                    'outbound')
            else:
                wizard.available_payment_method_line_ids = False


    def action_register_payment(self):
        po = self.env['vehicle.purchase.order'].browse(self._context.get('active_id'))
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': po.vendor_id.id,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'memo': po.name,
            'company_id': po.company_id.id,
            'date': self.payment_date,
            'state': 'draft',
            'payment_method_line_id': self.journal_id.outbound_payment_method_line_ids[0].id if self.journal_id.outbound_payment_method_line_ids else False,
            'vehicle_po_id': po.id,
        })

        payment.action_validate()
        if po.bill_id and po.bill_id.state == 'posted':
            po.bill_id.reconcile_advance_payments(payment)
            po.bill_id._compute_amount()

        if payment and self.pay_type == 'advance':
            po.write({'is_advanced_payment_paid': True})
        if payment and self.pay_type == 'installment':
            not_paid_installments=po.installment_board_ids.filtered(lambda x : x.state in ('not_paid','partial_paid'))
            if not_paid_installments :
                total_amount=self.amount
                for install in not_paid_installments :
                    if total_amount > 0 :
                        remaining=install.remaining_amount
                        if remaining <= total_amount :
                            install.paid_amount +=remaining
                            total_amount-=remaining
                        else :
                            install.paid_amount += total_amount
                            total_amount =0
            else:
                raise ValidationError(_("All installments is paid!"))

        return {
            'name': _('Payment'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'type': 'ir.actions.act_window',
        }
