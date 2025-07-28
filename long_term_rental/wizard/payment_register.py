# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentRegister(models.TransientModel):
    _name = 'long.term.rental.contract.payment.register'
    _description = 'Long Term Rental Contract Register Payment'

    def _default_amount(self):
        return self._get_due_amount()

    def _default_currency(self):
        contract = self.env['long.term.rental.contract']
        if self._context.get('default_long_term_rental_contract_id'):
            contract = self.env['long.term.rental.contract'].browse(
                self._context.get('active_id'))
        elif self._context.get('default_additional_supplement_service_line_id'):
            additional_service = self.env['additional.supplementary.services.line'].browse(
                self._context.get('default_additional_supplement_service_line_id'))
            contract = additional_service.long_term_rental_contract_id
        elif self._context.get('default_contract_installment_line_id'):
            contract_installment = self.env['contract.installment.line'].browse(
                self._context.get('default_contract_installment_line_id'))
            contract = contract_installment.long_term_contract_id
        return contract.company_currency_id

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method', compute="_compute_payment_method_line_id", store=True)
    payment_date = fields.Date(
        string='Payment Date', required=True, default=fields.Date.today())
    amount = fields.Float(string='Amount', required=True,
                          default=_default_amount, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', default=_default_currency, string='Currency', readonly=True)
    communication = fields.Char(string='Memo')

    payment_type_selection = fields.Selection(
        string='Payment Type Selection',
        selection=[('advance', 'مقدم'), ('extension', 'تمديد'), ('close', 'إغلاق'), ('debit', 'سداد مديونية'), ('extension_offline', 'تمديد بدون منصة'),
                   ('suspended_payment', 'سداد عقد معلق'), ],
        store=True, compute="_compute_payment_type_selection")
    contract_type = fields.Selection(string='Type', selection=[(
        'rental', 'Rental'), ('long_term', 'Long Term'),], default='long_term')
    long_term_rental_contract_id = fields.Many2one(
        'long.term.rental.contract', string='Rental Contract', compute="_compute_long_term_rental_contract_id", store=True, readonly="False", required=False)
    additional_supplement_service_line_id = fields.Many2one(
        'additional.supplementary.services.line')
    contract_installment_line_id = fields.Many2one(
        'contract.installment.line')
    allowed_branch_journal_id_ids = fields.Many2many(
        'account.journal', compute='_compute_allowed_branch_journal_id_ids', string='Allowed Branch Journals')

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for rec in self:
            available_payment_method_line_ids = rec.journal_id._get_available_payment_method_lines(
                'inbound')
            rec.payment_method_line_id = available_payment_method_line_ids[0]\
                if available_payment_method_line_ids else False

    @api.depends('long_term_rental_contract_id', 'additional_supplement_service_line_id', 'contract_installment_line_id')
    def _compute_payment_type_selection(self):
        for rec in self:
            payment_type_selection = 'advance'  # Default value
            if rec.contract_installment_line_id.is_down_payment:
                payment_type_selection = 'advance'
            elif not rec.contract_installment_line_id.is_down_payment or rec.additional_supplement_service_line_id:
                payment_type_selection = 'debit'
            rec.payment_type_selection = payment_type_selection

    @api.depends('additional_supplement_service_line_id', 'contract_installment_line_id')
    def _compute_long_term_rental_contract_id(self):
        for rec in self:
            if rec.contract_installment_line_id:
                rec.long_term_rental_contract_id = rec.contract_installment_line_id.long_term_contract_id
            elif rec.additional_supplement_service_line_id:
                rec.long_term_rental_contract_id = rec.additional_supplement_service_line_id.long_term_rental_contract_id

    @api.depends('long_term_rental_contract_id')
    def _compute_allowed_branch_journal_id_ids(self):
        for rec in self:
            if rec.long_term_rental_contract_id:
                branch_journal_ids = rec.long_term_rental_contract_id.vehicle_branch_id.cash_journal_ids | rec.long_term_rental_contract_id.vehicle_branch_id.bank_journal_ids
                rec.allowed_branch_journal_id_ids = branch_journal_ids
            else:
                rec.allowed_branch_journal_id_ids = self.env['account.journal']

    def _get_due_amount(self):
        if self._context.get('default_additional_supplement_service_line_id'):
            additional_service = self.env['additional.supplementary.services.line'].browse(
                self._context.get('default_additional_supplement_service_line_id'))
            return additional_service.price - additional_service.paid_amount
        elif self._context.get('default_contract_installment_line_id'):
            contract_installment = self.env['contract.installment.line'].browse(
                self._context.get('default_contract_installment_line_id'))
            return contract_installment.monthly_installment - contract_installment.paid_amount

        else:
            return 0

    def action_register_payment(self):
        contract = self.long_term_rental_contract_id
        if not contract:
            raise UserError(_('No contract found for this payment.'))
        if self.amount > self._get_due_amount():
            raise UserError(
                _('The amount to pay is greater than the due amount.'))
        if self.contract_installment_line_id.is_down_payment:
            self.long_term_rental_contract_id._check_before_open()

        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': contract.partner_id.id,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'memo': self.communication,
            'term_long_rental_contract_id': contract.id,
            'additional_supplement_service_line_id': self.additional_supplement_service_line_id.id if self.additional_supplement_service_line_id else False,
            'contract_installment_line_id': self.contract_installment_line_id.id if self.contract_installment_line_id else False,
            'company_id': contract.company_id.id,
            'date': self.payment_date,
            'payment_type_selection': self.payment_type_selection,
            'state': 'draft',
            'payment_method_line_id': self.payment_method_line_id.id,
        })
        if payment:
            payment.action_post()
            contract.write(
                {'advanced_paid_amount': contract.advanced_paid_amount + self.amount})
        invoice_vals = self.long_term_rental_contract_id._prepare_account_move_values()
        branch_analytic_account_ids = self.long_term_rental_contract_id.vehicle_branch_id.analytic_account_ids

        if not branch_analytic_account_ids:
            raise ValidationError(
                _(f"Add Analytic Accounts To {self.long_term_rental_contract_id.vehicle_branch_id.name}"))

        analytic_data = {
            self.long_term_rental_contract_id.vehicle_id.analytic_account_id.id: 100,
            branch_analytic_account_ids[0].id: 100
        }

        invoice_line_ids = [(0, 0, {
            'name': self.long_term_rental_contract_id.rental_configuration_id.trip_days_label,
            'quantity': 1,
            'price_unit': self.amount /
            (1 + (self.long_term_rental_contract_id.tax_percentage / 100)),
            'account_id': self.long_term_rental_contract_id.rental_configuration_id.trip_days_account_id.id,
            'currency_id': self.currency_id.id,
            'analytic_distribution': analytic_data,
            'tax_ids': [(6, 0, self.long_term_rental_contract_id.tax_ids.ids)]
        })]

        invoice_vals.update({
            'invoice_line_ids': invoice_line_ids,
            'additional_supplement_service_line_id': self.additional_supplement_service_line_id.id if self.additional_supplement_service_line_id else False,
            'contract_installment_line_id': self.contract_installment_line_id.id if self.contract_installment_line_id else False,
        })
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

        unreconciled_invoice_line = invoice.line_ids.filtered(
            lambda l: l.move_id.move_type == 'out_invoice' and not l.reconciled and l.account_type == 'asset_receivable')
        unreconciled_payment_line = payment.filtered(lambda payment: payment.payment_type == 'inbound').move_id.line_ids.filtered(
            lambda l: not l.reconciled and l.account_type == 'asset_receivable')
        (unreconciled_invoice_line + unreconciled_payment_line).reconcile()

        if self.contract_installment_line_id and self.contract_installment_line_id.is_down_payment:
            self.contract_installment_line_id.long_term_contract_id.action_open()
        return {
            'name': _('Invoice'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }
