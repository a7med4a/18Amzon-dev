# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
PERCENTAGE_values = [
    ('0', '0'),
    ('25', '25'),
    ('50', '50'),
    ('75', '75'),
    ('100', '100')
]


class FleetAccident(models.Model):
    _name = "fleet.accident"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fleet Accident"

    name = fields.Char('Contract Number', copy=False, readonly=True,
                       default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
    accident_category = fields.Selection([
        ('received_accident', 'Received Accident'),
        ('discovered_accident', 'Discovered Accident'),
    ], string='Accident Category', required=True, default='received_accident')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', domain="[('create_from_rental', '=', True)]", required=True)
    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', domain="[('state_id.type', '!=', 'sold')]", required=True)
    image_128 = fields.Image(
        related='fleet_vehicle_id.model_id.image_128', readonly=True)
    vehicle_insurance_line_id = fields.Many2one(
        'insurance.policy.line', string='Insurance', compute='_compute_vehicle_insurance_line_id', store=True)
    endurance_rate = fields.Float(
        string="Endurance Rate", related='vehicle_insurance_line_id.endurance_rate')
    endurance_customer = fields.Float(
        string="Endurance Customer", related='vehicle_insurance_line_id.endurance_customer')
    insurance_type = fields.Selection(
        string="Insurance Type", related='vehicle_insurance_line_id.policy_id.insurance_type')

    # Announcement Field
    city_id = fields.Many2one(
        'res.country.state', string='City', domain="[('country_id.code', '=', 'SA')]")
    report_source = fields.Selection([
        ('negm', 'Negm'),
        ('morror', 'Morror'),
        ('other', 'Others')
    ], string='Report Source')
    other_report_source = fields.Char('Other Report Source')
    announcement_date = fields.Date('Announcement Date')
    accident_date = fields.Date('Accident Date')

    # Reporting Fields
    accident_type = fields.Selection([
        ('shared', 'Shared'),
        ('not_covered', 'Not Covered'),
        ('right_of_recourse', 'Right of Recourse'),
    ], string='Accident Type', default='shared')
    accident_report_no = fields.Integer('Accident Report NO.')
    report_date = fields.Date('Report Date')
    customer_percentage = fields.Selection(PERCENTAGE_values, string='Customer Percentage',
                                           default='0', compute="_compute_customer_percentage",
                                           store=True, readonly=False)
    other_party_no = fields.Integer(string='Number of other party', default=0)
    other_party1_id = fields.Many2one('res.partner', string='Other Party1')
    other_party2_id = fields.Many2one('res.partner', string='Other Party2')
    other_party3_id = fields.Many2one('res.partner', string='Other Party3')
    other_party4_id = fields.Many2one('res.partner', string='Other Party4')
    other_party1_percentage = fields.Selection(
        PERCENTAGE_values, 'Other Party Percentage1')
    other_party2_percentage = fields.Selection(
        PERCENTAGE_values, 'Other Party Percentage2')
    other_party3_percentage = fields.Selection(
        PERCENTAGE_values, 'Other Party Percentage3')
    other_party4_percentage = fields.Selection(
        PERCENTAGE_values, 'Other Party Percentage4')
    other_party_partner_ids = fields.Many2many(
        'res.partner', string='Selected Partner', compute="_compute_other_party_partner_ids")

    # Evaluation Page Fields
    evaluation_report_ids = fields.One2many(
        'accident.evaluation.report', 'accident_id', string='Evaluation Report')
    confirmed_evaluation_report_id = fields.Many2one(
        'accident.evaluation.report', string='Confirmed Evaluation', copy=False)
    evaluation_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Evaluation Type', related="confirmed_evaluation_report_id.evaluation_type", store=True)
    evaluation_party_id = fields.Many2one(
        'fleet.accident.evaluation.party', string='Evaluation Party', domain="[('company_id', '=', company_id)]",
        related="confirmed_evaluation_report_id.evaluation_party_id", store=True)
    evaluation_item_ids = fields.One2many(
        'accident.evaluation.item.line', 'accident_id', string='Evaluation Items',
        related="confirmed_evaluation_report_id.evaluation_item_ids")
    total_evaluation = fields.Float(
        'Total Evaluation', compute="_compute_total_evaluation", store=True)
    compensation_type = fields.Selection(string='Compensation Type',
                                         related="confirmed_evaluation_report_id.compensation_type", store=True)

    # Due Amount Tab Fields
    due_amount_line_ids = fields.One2many(
        'accident.due.amount.line', 'accident_id', string='Due Amount Lines')

    evaluation_count = fields.Integer(
        'Payment Count', compute='_compute_evaluation_count', store=True)
    state = fields.Selection([
        ('announcement', 'Announcement'),
        ('accident_report', 'Waiting Accident Report'),
        ('evaluation', 'Waiting Evaluation'),
        ('insurance_approve', 'Waiting Insurance Approve'),
        ('invoicing', 'Waiting Invoicing'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='state', default='announcement')
    active = fields.Boolean('Active', copy=False, default=True)
    invoice_count = fields.Integer(
        compute="_compute_invoice_count", store=True)
    credit_note_count = fields.Integer(
        compute="_compute_credit_note_count", store=True)
    payment_count = fields.Integer(
        compute="_compute_payment_count", store=True)

    @api.depends('fleet_vehicle_id')
    def _compute_vehicle_insurance_line_id(self):
        for rec in self:
            running_insurance = rec.fleet_vehicle_id.insurance_policy_line_ids.filtered(
                lambda x: x.insurance_status == 'running')
            rec.vehicle_insurance_line_id = running_insurance and running_insurance[0]

    @api.depends('evaluation_item_ids', 'evaluation_item_ids.evaluation_item_value')
    def _compute_total_evaluation(self):
        for rec in self:
            rec.total_evaluation = sum(
                rec.evaluation_item_ids.mapped('evaluation_item_value'))

    @api.depends('other_party1_id', 'other_party2_id', 'other_party3_id', 'other_party4_id')
    def _compute_other_party_partner_ids(self):
        for rec in self:
            rec.other_party_partner_ids = rec.other_party1_id | rec.other_party2_id | rec.other_party3_id | rec.other_party4_id

    @api.depends('due_amount_line_ids', 'due_amount_line_ids.invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.due_amount_line_ids.invoice_id)

    @api.depends('due_amount_line_ids', 'due_amount_line_ids.invoice_ids', 'due_amount_line_ids.invoice_id.line_ids.matched_credit_ids')
    def _compute_credit_note_count(self):
        for rec in self:
            matching_credit_notes = rec.due_amount_line_ids.invoice_id.line_ids.matched_credit_ids.credit_move_id.move_id.filtered(
                lambda m: not m.origin_payment_id and not m.statement_line_id)
            rec.credit_note_count = len(
                rec.due_amount_line_ids.invoice_ids.filtered(lambda m: m.move_type == 'out_refund') | matching_credit_notes)

    @api.depends('due_amount_line_ids', 'due_amount_line_ids.invoice_id.line_ids.matched_credit_ids')
    def _compute_payment_count(self):
        for rec in self:
            matching_payments = rec.due_amount_line_ids.invoice_id.line_ids.matched_credit_ids.credit_move_id.move_id.filtered(
                lambda m: m.origin_payment_id).origin_payment_id.ids
            rec.payment_count = len(matching_payments)

    @api.depends('accident_type')
    def _compute_customer_percentage(self):
        for rec in self:
            if rec.accident_type == 'not_covered':
                rec.customer_percentage = '100'

    @api.depends('evaluation_report_ids')
    def _compute_evaluation_count(self):
        for record in self:
            record.evaluation_count = len(record.evaluation_report_ids)

    @api.constrains('accident_date', 'announcement_date', 'report_date')
    def _check_accident_date(self):
        for rec in self:
            if rec.announcement_date and rec.accident_date and rec.announcement_date < rec.accident_date:
                raise ValidationError(
                    "Accident Date must be less than Announcement Date")
            if rec.accident_date and rec.report_date and rec.accident_date > rec.report_date:
                raise ValidationError(
                    "Accident Date must be less than Report Date")

    @api.constrains('accident_report_no', 'state')
    def _check_accident_report_no(self):
        for rec in self.filtered(lambda accident: accident.state not in ['announcement', 'accident_report']):
            if self.search([('accident_report_no', '=', rec.accident_report_no), ('id', '!=', rec.id)], limit=1):
                raise ValidationError(
                    _("This accident report NO. must be unique"))

    @api.constrains('other_party_no', 'state', 'accident_type')
    def _check_other_party_no(self):
        for rec in self:
            if (rec.other_party_no > 4 or rec.other_party_no <= 0) and rec.state not in ['announcement', 'accident_report'] and rec.accident_type != 'not_covered':
                raise ValidationError(
                    "Number of Other Party must be less than 4 and not equal 0")

    @api.constrains('other_party1_percentage', 'other_party2_percentage', 'other_party3_percentage', 'other_party4_percentage', 'customer_percentage')
    def _check_percentage(self):
        for rec in self:
            if float(rec.customer_percentage) + float(rec.other_party1_percentage) +\
                float(rec.other_party2_percentage) + float(rec.other_party3_percentage) + float(rec.other_party4_percentage) != 100\
                    and rec.state not in ['announcement']:
                raise ValidationError(
                    "Total Percentages must be equal 100%")

    @api.onchange('fleet_vehicle_id')
    def _onchange_fleet_vehicle_id(self):
        matching_records = self.search([('fleet_vehicle_id', '=', self.fleet_vehicle_id.id), (
            'id', '!=', self.id), ('state', 'not in', ['closed', 'cancel'])])
        if matching_records:
            return {
                'warning': {
                    'title': _('Existing accident card'),
                    'message': _(f"This Vehicle has existing in other accident card {', '.join(matching_records.mapped('name'))}")
                }
            }

    @api.onchange('accident_type')
    def _onchange_accident_type(self):
        for i in range(1, 5):
            self['other_party%s_id' % i] = False
            self['other_party%s_percentage' % i] = '0'

        self.other_party_no = 0

    @api.onchange('evaluation_type')
    def _onchange_evaluation_type(self):
        self.evaluation_party_id = False

    def check_default_accident_items(self):
        default_accident_items = self.env['default.accident.item'].search([])
        for rec in self:
            compensation_type = rec.compensation_type
            company_default_accident_items = default_accident_items.filtered(
                lambda d: d.company_id == rec.company_id)
            if not company_default_accident_items.filtered(lambda x: x.compensation_type in ['both', compensation_type]):
                raise ValidationError(
                    "Please Add Default Accident Item with Compensation Type: %s" % compensation_type + " and Both")

    def set_due_amount_lines(self):
        self.due_amount_line_ids.unlink()
        default_accident_items = self.env['default.accident.item'].search(
            [], order='sequence')
        vals_list = []
        for rec in self:
            compensation_type = rec.compensation_type

            company_default_accident_items = default_accident_items.filtered(
                lambda d: d.company_id == rec.company_id)
            matched_items = company_default_accident_items.filtered(
                lambda x: x.accident_item == 'customer')
            if rec.accident_type == 'shared':
                matched_items |= company_default_accident_items.filtered(
                    lambda x: x.compensation_type in ['both', compensation_type])
            for item in matched_items:
                partner_id = self.env['res.partner']
                partner_percentage_list = []
                allow_endurance = is_endurance = False

                if item.accident_item == 'customer':
                    partner_id = rec.partner_id
                    if partner_id:
                        partner_percentage_list.append(
                            (partner_id, float(rec.customer_percentage)))
                elif item.accident_item == 'other_party':
                    for i in range(1, rec.other_party_no + 1):
                        partner_id = rec['other_party%s_id' % i]
                        partner_percentage_list.append(
                            (partner_id, float(rec['other_party%s_percentage' % i])))
                elif item.accident_item == 'amazon':
                    partner_id = rec.vehicle_insurance_line_id.policy_id.insurance_company
                    partner_percentage_list.append(
                        (partner_id, 0.0))

                if rec.accident_type == 'shared' and item.accident_item == 'customer':
                    allow_endurance = True
                    is_endurance = True

                for partner_id, percentage in partner_percentage_list:
                    vals_list.append({
                        'accident_id': rec.id,
                        'default_accident_item_id': item.id,
                        'is_endurance': True if item.accident_item == 'customer' else False,
                        'partner_id': partner_id.id,
                        'allow_endurance': allow_endurance,
                        'is_endurance': is_endurance,
                        'line_percentage': percentage
                    })

        self.env['accident.due.amount.line'].create(vals_list)

    def _check_vehicle_running_policy(self):
        matched_policy_logs = self.env['insurance.policy.line'].search(
            [('vehicle_id', 'in', self.fleet_vehicle_id.ids), ('insurance_status', '=', 'running')])

        for rec in self.filtered(lambda c: c.fleet_vehicle_id):
            # Check Insurance Policy
            if not matched_policy_logs.filtered(lambda p: p.vehicle_id == rec.fleet_vehicle_id):
                raise ValidationError(
                    _("Selected Vehicle Hasn't Running Insurance Policy"))

    def button_announcement(self):
        self.state = 'announcement'

    def button_accident_report(self):
        self._check_vehicle_running_policy()
        self.state = 'accident_report'

    def button_evaluation(self):
        self.state = 'evaluation'

    def button_add_evaluation(self):
        self.ensure_one()
        view_id = self.env.ref(
            'fleet_accident.add_accident_evaluation_report_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Evaluation'),
            'res_model': 'accident.evaluation.report',
            'target': 'new',
            'view_mode': 'form',
            'context': {'default_accident_id': self.id},
            'views': [[view_id, 'form']]
        }

    def button_insurance_approve(self):
        if any(rec.total_evaluation <= 0.0 for rec in self):
            raise ValidationError(_("Please fill evaluation table "))
        if any(not rec.confirmed_evaluation_report_id for rec in self):
            raise ValidationError(
                _("You can't move to insurance approve state before confirm at least one evaluation!"))
        self.state = 'insurance_approve'

    def button_invoicing(self):
        self.state = 'invoicing'

    def button_closed(self):
        for rec in self:
            if sum(rec.due_amount_line_ids.mapped('remaining_amount')) > 0.0:
                raise ValidationError(
                    _("You can't close accident that have positive remaining amount!"))
        self.state = 'closed'

    def button_cancel(self):
        self.state = 'cancel'

    def compute_due_amount(self):
        self.check_default_accident_items()
        self.set_due_amount_lines()

    def recompute_due_amount(self):
        self.due_amount_line_ids.calculate_amount()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fleet.accident.seq')
        accidents = super().create(vals_list=vals_list)
        damage_state = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'accident_or_damage')], limit=1)
        if not damage_state:
            raise ValidationError(
                _("Please configure accident in vehicle states."))
        accidents.fleet_vehicle_id.write({
            'state_id': damage_state.id
        })
        return accidents

    def write(self, vals):
        if vals.get('state'):
            self._check_percentage()
        return super().write(vals)

    def view_related_evaluation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Evaluations'),
            'res_model': 'accident.evaluation.report',
            'view_mode': 'list,form',
            'domain': [('accident_id', '=', self.id)],
            'context': {'create': 0}
        }

    def view_related_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.due_amount_line_ids.invoice_id.ids)],
            'context': {'create': 0}
        }

    def view_related_credit_notes(self):
        self.ensure_one()

        matching_credit_notes = self.due_amount_line_ids.invoice_id.line_ids.matched_credit_ids.credit_move_id.move_id.filtered(
            lambda m: not m.origin_payment_id and not m.statement_line_id).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Notes'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.due_amount_line_ids.invoice_ids.filtered(lambda m: m.move_type == 'out_refund').ids + matching_credit_notes)],
            'context': {'create': 0}
        }

    def view_related_payments(self):
        self.ensure_one()
        matching_payments = self.due_amount_line_ids.invoice_id.line_ids.matched_credit_ids.credit_move_id.move_id.filtered(
            lambda m: m.origin_payment_id).origin_payment_id.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', matching_payments)],
            'context': {'create': 0}
        }


class AccidentEvaluationItemLine(models.Model):
    _name = "accident.evaluation.item.line"
    _description = "Accident Evaluation Item Line"

    evaluation_report_id = fields.Many2one(
        'accident.evaluation.report', string='Evaluation Report')
    accident_id = fields.Many2one('fleet.accident', string='Accident')
    company_id = fields.Many2one(
        'res.company', string='Company', related="evaluation_report_id.company_id", store=True)
    evaluation_item_id = fields.Many2one(
        'fleet.accident.evaluation.item', string='Evaluation Item', required=True, domain="[('company_id', '=', company_id)]")
    evaluation_item_value = fields.Float(string='Evaluation Item Value')


class AccidentDueAmountLine(models.Model):
    _name = "accident.due.amount.line"
    _description = "Accident Evaluation Item Line"

    accident_id = fields.Many2one('fleet.accident', string='Accident')
    default_accident_item_id = fields.Many2one(
        'default.accident.item', string='Default Accident Item')
    accident_item_compensation_type = fields.Selection(
        related='default_accident_item_id.compensation_type', store=True)
    accident_item_type = fields.Selection(
        related='default_accident_item_id.accident_item', store=True)
    name = fields.Char(
        'Accident Item', compute='_compute_name', store=True, readonly=False)
    allow_endurance = fields.Boolean('Allow Endurance')
    is_endurance = fields.Boolean('Endurance')
    computation_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed')
    ], string='Computation Type', default='percentage')
    line_percentage = fields.Float("Line Percentage")
    amount = fields.Float('Amount')
    partner_id = fields.Many2one('res.partner', string='Partner')
    is_tax_active = fields.Boolean('Tax Active', default=False)
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               compute='_compute_tax_ids', store=True)
    invoice_ids = fields.One2many(
        'account.move', 'accident_due_amount_line_id', string='All Invoices')
    invoice_id = fields.Many2one('account.move', string='Current Invoice')

    # Payment Fields
    paid_amount = fields.Float(
        'Paid Amount', compute="_compute_paid_amount", store=True)
    discount_amount = fields.Float(
        'Discount Amount', compute="_compute_discount_amount", store=True)
    remaining_amount = fields.Float(
        'Remaining Amount', compute="_compute_remaining_amount", store=True)

    # wizard
    wizard_discount_amount = fields.Float('Discount')

    @api.depends('default_accident_item_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.default_accident_item_id.name

    @api.depends('is_tax_active', 'default_accident_item_id')
    def _compute_tax_ids(self):
        for rec in self:
            if rec.is_tax_active:
                rec.tax_ids = rec.default_accident_item_id.tax_ids
            else:
                rec.tax_ids = [(6, 0, [])]

    @api.depends('invoice_id', 'invoice_id.line_ids', 'invoice_id.line_ids.matched_debit_ids', 'invoice_id.line_ids.matched_credit_ids')
    def _compute_paid_amount(self):
        for rec in self:
            payment_move_ids = rec.invoice_id.line_ids.matched_credit_ids.credit_move_id.move_id.filtered(
                lambda m: m.origin_payment_id)
            rec.paid_amount = sum(payment_move_ids.mapped('amount_total'))

    @api.depends('invoice_ids')
    def _compute_discount_amount(self):
        for rec in self:
            rec.discount_amount = sum(rec.invoice_ids.filtered(
                lambda m: m.move_type == 'out_refund').mapped('amount_total'))

    @api.depends('paid_amount', 'discount_amount', 'amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.amount - rec.discount_amount - rec.paid_amount

    @api.constrains('amount')
    def _check_amount_validation(self):
        for rec in self:
            if rec.amount > rec.accident_id.total_evaluation and not rec.is_endurance:
                raise ValidationError(
                    _(f"{rec.name} Amount can't be Greater than Total Evaluation"))

    # @api.onchange('is_tax_active')
    # def _onchange_is_tax_active(self):
    #     if self.is_tax_active and not self.default_accident_item_id.tax_ids:
    #         return {
    #             'warning': {
    #                 'title': "No Taxes In Configurations",
    #                 'message': "There's no taxis assign to this type in configuration!",
    #             }
    #         }

    @api.constrains('is_tax_active')
    def _check_is_tax_active(self):
        for rec in self:
            if rec.is_tax_active and not rec.default_accident_item_id.tax_ids:
                raise ValidationError(
                    _("There's no taxis assign to this type in configuration!"))

    def calculate_amount(self):
        for rec in self:
            if rec.is_endurance:
                rec.amount = rec.accident_id.endurance_customer
            elif rec.accident_item_type == 'amazon':
                rec.amount = rec.accident_id.total_evaluation \
                    - (rec.accident_id.endurance_rate *
                       float(rec.accident_id.customer_percentage) / 100)
            elif rec.computation_type == 'percentage':
                rec.amount = rec.accident_id.total_evaluation * rec.line_percentage / 100

    @api.model_create_multi
    def create(self, vals):
        amount_lines = super().create(vals)
        amount_lines.calculate_amount()
        return amount_lines

    def _prepare_invoice_vals(self):
        self.ensure_one()
        total_line_tax_percentage = sum(self.tax_ids.mapped('amount'))
        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'journal_id': self.default_accident_item_id.journal_id.id,
            'currency_id': self.env.company.currency_id.id,
            'accident_due_amount_line_id': self.id,
            'is_accident': True,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.default_accident_item_id.account_id.id,
                'quantity': 1,
                'price_unit': self.amount / (1 + (total_line_tax_percentage / 100)),
                'analytic_distribution': {self.accident_id.fleet_vehicle_id.analytic_account_id.id: 100},
                'tax_ids': [(6, 0, self.tax_ids.ids)] if self.is_tax_active else False
            })]
        }

    def create_invoice(self):
        account_move_obj = self.env['account.move']
        for rec in self:
            vals = rec._prepare_invoice_vals()
            invoice = account_move_obj.sudo().create(vals)
            invoice.action_post()
            rec.invoice_id = invoice.id
            # reconcile
            unreconciled_invoice_line = invoice.line_ids.filtered(
                lambda l: not l.reconciled and l.account_type == 'asset_receivable')
            unreconciled_credit_note_line = rec.invoice_ids.filtered(lambda m: m.move_type == 'out_refund').line_ids.filtered(
                lambda l: not l.reconciled and l.account_type == 'asset_receivable')
            if unreconciled_invoice_line and unreconciled_credit_note_line:
                try:
                    (unreconciled_credit_note_line +
                     unreconciled_invoice_line).reconcile()
                except Exception as e:
                    raise ValidationError(
                        _("Failed to reconcile invoice and credit note lines: %s") % str(e))

    def _prepare_credit_note_vals(self):
        self.ensure_one()
        total_line_tax_percentage = sum(self.tax_ids.mapped('amount'))
        return {
            'move_type': 'out_refund',
            'partner_id': self.partner_id.id,
            'journal_id': self.default_accident_item_id.journal_id.id,
            'currency_id': self.env.company.currency_id.id,
            'accident_due_amount_line_id': self.id,
            'is_accident': True,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.default_accident_item_id.account_id.id,
                'quantity': 1,
                'price_unit': self.wizard_discount_amount / (1 + (total_line_tax_percentage / 100)),
                'analytic_distribution': {self.accident_id.fleet_vehicle_id.analytic_account_id.id: 100},
                'tax_ids': [(6, 0, self.tax_ids.ids)] if self.is_tax_active else False
            })]
        }

    def create_credit_note(self):
        account_move_obj = self.env['account.move']
        for rec in self:
            if rec.wizard_discount_amount > rec.remaining_amount:
                raise ValidationError(
                    _("Discount can't be greater than remaining amount"))

            vals = rec._prepare_credit_note_vals()
            credit_note = account_move_obj.sudo().create(vals)
            credit_note.action_post()

            # reconcile
            unreconciled_invoice_line = rec.invoice_id.line_ids.filtered(
                lambda l: not l.reconciled and l.account_type == 'asset_receivable')
            unreconciled_credit_note_line = credit_note.line_ids.filtered(
                lambda l: not l.reconciled and l.account_type == 'asset_receivable')
            if unreconciled_invoice_line and unreconciled_credit_note_line:
                try:
                    (unreconciled_credit_note_line +
                     unreconciled_invoice_line).reconcile()
                except Exception as e:
                    raise ValidationError(
                        _("Failed to reconcile invoice and credit note lines: %s") % str(e))

            rec.wizard_discount_amount = 0.0

    def apply_discount(self):
        view_id = self.env.ref(
            'fleet_accident.accident_due_amount_line_view_discount_wiz').id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Apply Discount'),
            'res_model': 'accident.due.amount.line',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [[view_id, 'form']]
        }
