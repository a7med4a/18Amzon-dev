# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError


class UpgradeDowngradePlan(models.Model):
    _name = 'upgrade.downgrade.rental.plan'
    _description = 'Upgrade Downgrade Rental Plan'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', compute="_compute_rental_contract_fields", store=True)
    contract_state = fields.Selection(
        related='rental_contract_id.state', string='Contract State')
    old_rental_plan = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Rental Plan', compute="_compute_rental_contract_fields", store=True)

    new_rental_plan = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Rental Plan', compute="_compute_rental_contract_fields", store=True)

    old_daily_rate = fields.Float(
        'Current Daily Rate', compute='_compute_rental_contract_fields', store=True)
    new_daily_rate = fields.Float(
        'New Daily Rate', compute='_compute_rental_contract_fields', store=True)

    current_days = fields.Integer(
        'Current Duration (Days)', compute='_compute_rental_contract_fields', store=True)
    current_hours = fields.Integer(
        'Current Duration (Hours)',  compute='_compute_rental_contract_fields', store=True)

    current_total = fields.Float(
        'Current Total', compute="_compute_rental_contract_fields", store=True)
    new_total = fields.Float(
        'New Total', compute="_compute_rental_contract_fields", store=True)
    difference_total = fields.Float(
        'Applies Discount / Fine', compute="_compute_rental_contract_fields", store=True)

    type = fields.Selection([
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade')
    ], string='Type', compute="_compute_rental_contract_fields", store=True)

    upgrade_downgrade_applied = fields.Boolean('Is Applied', copy=False)

    @api.depends('rental_contract_id')
    def _compute_rental_contract_fields(self):
        for rec in self:

            if rec.rental_contract_id and not rec.upgrade_downgrade_applied:
                # Plans
                rec.old_rental_plan = rec.rental_contract_id.rental_plan
                if rec.rental_contract_id.current_days >= 26:
                    new_rental_plan = 'monthly'
                elif rec.rental_contract_id.current_days >= 5:
                    new_rental_plan = 'weekly'
                else:
                    new_rental_plan = 'daily'
                rec.new_rental_plan = new_rental_plan

                # Type
                if rec.rental_contract_id.current_days > rec.rental_contract_id.duration:
                    rec.type = 'upgrade'
                elif rec.old_rental_plan == 'monthly' and rec.new_rental_plan in ['daily', 'weekly']\
                        and rec.rental_contract_id.current_days < rec.rental_contract_id.duration:
                    rec.type = 'downgrade'

                if rec.type:

                    # Daily Rate
                    old_daily_rate = rec.rental_contract_id.daily_rate
                    if new_rental_plan == 'daily':
                        new_daily_rate = rec.rental_contract_id.model_pricing_min_normal_day_price
                    elif new_rental_plan == 'weekly':
                        new_daily_rate = rec.rental_contract_id.model_pricing_min_weekly_day_price
                    elif new_rental_plan == 'monthly':
                        new_daily_rate = rec.rental_contract_id.model_pricing_min_monthly_day_price
                    else:
                        new_daily_rate = 0.0

                    rec.old_daily_rate = old_daily_rate
                    rec.new_daily_rate = new_daily_rate
                    # Duration
                    current_days = rec.rental_contract_id.current_days
                    current_hours = rec.rental_contract_id.current_hours
                    rec.current_days = current_days
                    rec.current_hours = current_hours

                    # Totals
                    current_total = (
                        current_days * old_daily_rate) + (current_hours / 24 * old_daily_rate)
                    new_total = (
                        current_days * new_daily_rate) + (current_hours / 24 * new_daily_rate)
                    rec.difference_total = abs(new_total - current_total)
                    rec.current_total = current_total
                    rec.new_total = new_total

    def apply_discount_fine(self):

        if not self.difference_total:
            pass
        if not self.rental_contract_id:
            raise ValidationError(_('Please select a rental contract.'))

        allowed_journal_ids = self.rental_contract_id.vehicle_branch_id.sales_journal_ids
        branch_analytic_account_ids = self.rental_contract_id.vehicle_branch_id.analytic_account_ids
        if not allowed_journal_ids:
            raise ValidationError(
                _(f"Add Sales Journals To {self.rental_contract_id.vehicle_branch_id.name}"))
        if not branch_analytic_account_ids:
            raise ValidationError(
                _(f"Add Analytic Accounts To {self.rental_contract_id.vehicle_branch_id.name}"))
        if not self.rental_contract_id.rental_configuration_id.upgrade_label or not self.rental_contract_id.rental_configuration_id.downgrade_label\
                or not self.rental_contract_id.rental_configuration_id.upgrade_account_id or not self.rental_contract_id.rental_configuration_id.downgrade_account_id:
            raise ValidationError(
                _("Please add upgrade / downgrade configuration in rental settings"))

        item_vals_list = []
        fines_discount_line_ids = []
        analytic_data = {
            self.rental_contract_id.vehicle_id.analytic_account_id.id: 100,
            branch_analytic_account_ids[0].id: 100
        }

        price_unit = self.difference_total

        item_vals_list.append((0, 0, {
            'name': self.rental_contract_id.rental_configuration_id.upgrade_label if self.type == 'upgrade' else self.rental_contract_id.rental_configuration_id.downgrade_label,
            'account_id': self.rental_contract_id.rental_configuration_id.upgrade_account_id.id if self.type == 'upgrade' else self.rental_contract_id.rental_configuration_id.downgrade_account_id.id,
            'quantity': 1,
            'price_unit': price_unit,
            'analytic_distribution': analytic_data,
            'tax_ids': [(6, 0, self.rental_contract_id.rental_configuration_id.tax_ids.ids)]
        }))

        entry_vals = {
            'move_type': 'out_invoice' if self.type == 'downgrade' else 'out_refund',
            'rental_contract_id': self.rental_contract_id.id,
            'invoice_date': fields.Date.today(),
            'journal_id': allowed_journal_ids[0].id,
            'partner_id': self.rental_contract_id.partner_id.id,
            'invoice_line_ids': item_vals_list,
            'currency_id': self.rental_contract_id.company_currency_id.id,
        }

        account_move_id = self.env['account.move'].sudo().create(entry_vals)
        account_move_id.action_post()
        self.rental_contract_id.reconcile_invoices_with_payments()
        self.upgrade_downgrade_applied = True
        fines_discount_line_ids.append((0, 0, {
            'name': self.rental_contract_id.rental_configuration_id.upgrade_label if self.type == 'upgrade' else self.rental_contract_id.rental_configuration_id.downgrade_label,
            'price': price_unit,
            'type': 'discount' if self.type == 'upgrade' else 'fine',
        }))
        self.rental_contract_id.write(
            {'fines_discount_line_ids': fines_discount_line_ids})

        return {'type': 'ir.actions.act_window_close'}
