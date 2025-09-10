# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentRegister(models.TransientModel):
    _name = 'limousine.contract.payment.register'
    _description = 'Limousine Contract Register Payment'

    def _default_amount(self):
        return self._get_due_amount()

    def _default_currency(self):
        contract = self.env['limousine.contract'].browse(self._context.get('active_id'))
        return contract.currency_id

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain=lambda self: [('id', 'in', self.env.user.branch_ids.filtered(
            lambda b: b.branch_type == 'limousine').cash_journal_ids.ids + self.env.user.branch_ids.filtered(
            lambda b: b.branch_type == 'limousine').bank_journal_ids.ids)])
    allowed_journal_ids = fields.Many2many(
        'account.journal', string='Allowed Journals', compute="_compute_allowed_journal_ids")
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method', required=True)
    available_payment_method_line_ids = fields.Many2many(
        'account.payment.method.line', compute='_compute_payment_method_line_fields')
    payment_date = fields.Date(
        string='Payment Date', default=fields.Date.today())
    amount = fields.Float(string='Amount', required=True,
                          default=_default_amount, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', default=_default_currency, string='Currency', readonly=True)
    communication = fields.Char(
        string='Memo', compute="_compute_communication", store=True, readonly=False)

    contract_id = fields.Many2one(
        'limousine.contract', string='Limousine Contract')
    contract_state = fields.Selection(
        related='contract_id.state', string='State', readonly=True)

    payment_type_selection = fields.Selection(
        string='Payment Type Selection',
        selection=[('advance', 'مقدم'), ('extension', 'تمديد'), ('close', 'إغلاق'), ('debit', 'سداد مديونية'),
                   ('extension_offline', 'تمديد بدون منصة'),
                   ('suspended_payment', 'سداد عقد معلق'), ('fine', 'غرامة'), ('closing_batch', 'دفعة اغلاق'),
                   ('refund', 'مردودات')])

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for rec in self:
            available_payment_method_line_ids = rec.journal_id._get_available_payment_method_lines('inbound')
            rec.payment_method_line_id = available_payment_method_line_ids[
                0] if available_payment_method_line_ids else False

    @api.depends('contract_id')
    def _compute_allowed_journal_ids(self):
        for rec in self:
            rec.allowed_journal_ids = self.env.branches.cash_journal_ids.ids + self.env.branches.bank_journal_ids.ids

    @api.depends('journal_id', 'currency_id', 'amount')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            payment_type = 'inbound' if self.amount > 0 else 'outbound'
            if wizard.journal_id:
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines(
                    payment_type)
            else:
                wizard.available_payment_method_line_ids = False

    @api.depends('contract_id')
    def _compute_communication(self):
        for rec in self:
            rec.communication = str(rec.contract_id.name) + ' - ' + str(rec.contract_id.vehicle_id.display_name)

    def _get_due_amount(self):
        contract = self.env['limousine.contract'].browse(self._context.get('active_id'))
        return contract.due_amount

    def action_register_payment(self):
        contract = self.env['limousine.contract'].browse(self._context.get('active_id'))
        if not self.payment_method_line_id:
            raise ValidationError(
                _("Please Configure Incoming Payments in Selected Journal"))
        if self.amount == 0:
            raise UserError(_("The amount must be greater than zero."))
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'partner_type': 'customer',
            'partner_id': contract.partner_id.id,
            'journal_id': self.journal_id.id,
            'amount': self.amount if self.amount > 0 else -self.amount,
            'currency_id': self.currency_id.id,
            'memo': self.communication,
            'limousine_contract_id': contract.id,
            'company_id': contract.company_id.id,
            'date': self.payment_date,
            'state': 'draft',
            'payment_type_selection': self.payment_type_selection,
            'payment_method_line_id': self.payment_method_line_id.id,
        })
        payment.action_post()
        payment.action_validate()
