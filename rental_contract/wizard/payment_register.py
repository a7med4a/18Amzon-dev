# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentRegister(models.TransientModel):
    _name = 'rental.contract.payment.register'
    _description = 'Rental Contract Register Payment'

    def _default_amount(self):
        return self._get_due_amount()

    def _default_currency(self):
        contract = self.env['rental.contract'].browse(
            self._context.get('active_id'))
        return contract.company_currency_id

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method', compute="_compute_payment_method_line_id", store=True)
    payment_date = fields.Date(
        string='Payment Date', default=fields.Date.today())
    amount = fields.Float(string='Amount', required=True,
                          default=_default_amount, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', default=_default_currency, string='Currency', readonly=True)
    communication = fields.Char(string='Memo')

    payment_type_selection = fields.Selection(
        string='Payment Type Selection',
        selection=[('advance', 'مقدم'), ('extension', 'تمديد'), ('close', 'إغلاق'), ('debit', 'سداد مديونية'), ('extension_offline', 'تمديد بدون منصة'),
                   ('suspended_payment', 'سداد عقد معلق'), ],
        required=True, )

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for rec in self:
            available_payment_method_line_ids = rec.journal_id._get_available_payment_method_lines(
                'inbound')
            rec.payment_method_line_id = available_payment_method_line_ids[0]\
                if available_payment_method_line_ids else False

    def _get_due_amount(self):
        contract = self.env['rental.contract'].browse(
            self._context.get('active_id'))
        return contract.current_due_amount

    def action_register_payment(self):
        contract = self.env['rental.contract'].browse(
            self._context.get('active_id'))
        if not self.payment_method_line_id:
            raise ValidationError(
                _("Please Configure Incoming Payments in Selected Journal"))
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.partner_id.id,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'memo': self.communication,
            'rental_contract_id': contract.id,
            'company_id': contract.company_id.id,
            'date': self.payment_date,
            'payment_type_selection': self.payment_type_selection,
            'state': 'draft',
            'payment_method_line_id': self.payment_method_line_id.id,
        })
        payment.action_post()
        payment.action_validate()
        if payment:
            payment.action_post()
        return {
            'name': _('Payment'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'type': 'ir.actions.act_window',
        }
