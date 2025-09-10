# -*- coding: utf-8 -*-

from odoo import models, fields, api
from random import randint


class Branch(models.Model):
    _inherit = 'res.branch'
    _description = 'Branches'

    def _get_default_color(self):
        return randint(1, 11)

    naql_id = fields.Char('Naql ID')
    branch_type = fields.Selection([
        ('rental', 'Rental'),
        ('limousine', 'Limousine'),
        ('workshop', 'Workshop'),
        ('administration', 'Administration')
    ], string='Branch Type')

    color = fields.Integer(
        string='Color', default=_get_default_color, aggregator=False)

    # accounting Tab Fields
    sales_journal_ids = fields.Many2many(
        'account.journal', 'branch_sales_journal_rel', 'branch_id', 'journal_id', string='Allowed Sales Journals', domain=[('type', '=', 'sale')])
    purchase_journal_ids = fields.Many2many(
        'account.journal', 'branch_purchase_journal_rel', 'branch_id', 'journal_id', string='Allowed Purchase Journals', domain=[('type', '=', 'purchase')])
    cash_journal_ids = fields.One2many(
        'account.journal', 'branch_id', string='Allowed Cash Journals', domain=[('type', '=', 'cash')])
    bank_journal_ids = fields.One2many(
        'account.journal', 'branch_id', string='Allowed Bank Journals', domain=[('type', '=', 'bank')])
    misc_journal_ids = fields.Many2many(
        'account.journal', 'branch_misc_journal_rel', 'branch_id', 'journal_id', string='Allowed MISC Journals', domain=[('type', '=', 'general')])
    transfer_journal_ids = fields.Many2many(
        'account.journal', 'branch_transfer_journal_rel', 'branch_id', 'journal_id', string='Allowed Transfers Money', domain=[('type', 'in', ['cash', 'bank'])])
    analytic_plan_ids = fields.Many2many(
        'account.analytic.plan', string='Analytic Plan')
    analytic_account_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Account', domain="[('plan_id', 'in', analytic_plan_ids)]")

    # Allowed Users Tab
    allowed_user_ids = fields.Many2many(
        'res.users', 'users_branch_rel', string='Allowed Users')
