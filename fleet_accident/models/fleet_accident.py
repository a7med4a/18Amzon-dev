# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetAccident(models.Model):
    _name = "fleet.accident"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fleet Accident"
    _rec_name = 'fleet_vehicle_id'

    accident_category = fields.Selection([
        ('received_accident', 'Received Accident'),
        ('discovered_accident', 'Discovered Accident'),
    ], string='Accident Category', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', domain="[('create_from_rental', '=', True)]", required=True)
    rental_contract_no = fields.Char('Rental Contract Number', required=True)
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
    city_id = fields.Many2one('res.country.state', string='City')
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
    accident_report_no = fields.Float('Accident Report NO.')
    report_date = fields.Date('Report Date')
    customer_percentage = fields.Selection([
        ('0', '0'),
        ('25', '25'),
        ('50', '50'),
        ('75', '75'),
        ('100', '100')
    ], string='Customer Percentage', default='0')
    other_party_no = fields.Integer(string='Number of other party', default=0)
    other_party1_id = fields.Many2one('res.partner', string='Other Party1')
    other_party2_id = fields.Many2one('res.partner', string='Other Party2')
    other_party3_id = fields.Many2one('res.partner', string='Other Party3')
    other_party4_id = fields.Many2one('res.partner', string='Other Party4')
    other_party1_percentage = fields.Float('Other Party Percentage1')
    other_party2_percentage = fields.Float('Other Party Percentage2')
    other_party3_percentage = fields.Float('Other Party Percentage3')
    other_party4_percentage = fields.Float('Other Party Percentage4')

    # Evaluation Page Fields
    evaluation_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Evaluation Type')
    evaluation_party_id = fields.Many2one(
        'fleet.accident.evaluation.party', string='Evaluation Party')
    evaluation_item_ids = fields.One2many(
        'accident.evaluation.item.line', 'accident_id', string='Evaluation Items')
    total_evaluation = fields.Float(
        'Total Evaluation', compute="_compute_total_evaluation", store=True)
    compensation_type = fields.Selection([
        ('full', 'Full'),
        ('third', 'Third')
    ], string='Compensation Type')

    # Due Amount Tab Fields
    due_amount_line_ids = fields.One2many(
        'accident.due.amount.line', 'accident_id', string='Due Amount Lines')

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

    @api.depends('due_amount_line_ids', 'due_amount_line_ids.invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.due_amount_line_ids.invoice_ids)

    @api.constrains('accident_date', 'announcement_date', 'report_date')
    def _check_accident_date(self):
        for rec in self:
            if rec.announcement_date and rec.accident_date and rec.announcement_date > rec.accident_date:
                raise ValidationError(
                    "Announcement Date must be less than Accident Date")
            if rec.accident_date and rec.report_date and rec.accident_date > rec.report_date:
                raise ValidationError(
                    "Report Date must be less than Accident Date")

    @api.constrains('other_party_no', 'state')
    def _check_other_party_no(self):
        for rec in self:
            if (rec.other_party_no > 4 or rec.other_party_no <= 0) and rec.state not in ['announcement', 'accident_report']:
                raise ValidationError(
                    "Number of Other Party must be less than 4 and not equal 0")

    @api.constrains('other_party1_percentage', 'other_party2_percentage', 'other_party3_percentage', 'other_party4_percentage', 'state')
    def _check_percentage(self):
        for rec in self:
            if float(rec.customer_percentage) + rec.other_party1_percentage +\
                rec.other_party2_percentage + rec.other_party3_percentage + rec.other_party4_percentage != 100\
                    and rec.state not in ['announcement', 'accident_report']:
                raise ValidationError(
                    "Total of Other Party Percentage must be equal 100%")

    @api.onchange('accident_type')
    def _onchange_accident_type(self):
        for i in range(1, 5):
            self['other_party%s_id' % i] = False
            self['other_party%s_percentage' % i] = 0

        self.other_party_no = 0
        if self.accident_type == 'not_covered':
            self.customer_percentage = '100'

    @api.onchange('evaluation_type')
    def _onchange_evaluation_type(self):
        self.evaluation_party_id = False

    def check_default_accident_items(self):
        default_accident_items = self.env['default.accident.item'].search([])
        for rec in self:
            compensation_type = rec.compensation_type
            if not default_accident_items.filtered(lambda x: x.compensation_type in ['both', compensation_type]):
                raise ValidationError(
                    "Please Add Default Accident Item with Compensation Type: %s" % compensation_type + " and Both")

    def set_due_amount_lines(self):
        self.due_amount_line_ids.unlink()
        default_accident_items = self.env['default.accident.item'].search(
            [], order='sequence')
        vals_list = []
        for rec in self:
            compensation_type = rec.compensation_type
            matched_items = default_accident_items.filtered(
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
                elif item.accident_item == 'other_party' and rec.accident_type == 'shared':
                    for i in range(1, rec.other_party_no + 1):
                        partner_id = rec['other_party%s_id' % i]
                        partner_percentage_list.append(
                            (partner_id, rec['other_party%s_percentage' % i]))
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

    def button_announcement(self):
        self.state = 'announcement'

    def button_accident_report(self):
        self.state = 'accident_report'

    def button_evaluation(self):
        self.state = 'evaluation'

    def button_insurance_approve(self):
        self.state = 'insurance_approve'

    def button_invoicing(self):
        self.state = 'invoicing'

    def button_closed(self):
        self.state = 'closed'

    def button_cancel(self):
        self.state = 'cancel'

    def compute_due_amount(self):
        self.check_default_accident_items()
        self.set_due_amount_lines()

    def recompute_due_amount(self):
        self.due_amount_line_ids.calculate_amount()


class AccidentEvaluationItemLine(models.Model):
    _name = "accident.evaluation.item.line"
    _description = "Accident Evaluation Item Line"

    accident_id = fields.Many2one('fleet.accident', string='Accident')
    evaluation_item_id = fields.Many2one(
        'fleet.accident.evaluation.item', string='Evaluation Item', required=True)
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
    remaining_amount = fields.Float(
        'Remaining Amount', compute='_compute_amounts', store=True)
    invoiced_amount = fields.Float(
        'Invoiced', compute='_compute_amounts', store=True)
    is_tax_active = fields.Boolean('Tax Active', default=False)
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               compute='_compute_tax_ids', store=True, readonly=False)
    invoice_ids = fields.One2many(
        'account.move', 'accident_due_amount_line_id', string='Invoices')

    @api.depends('default_accident_item_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.default_accident_item_id.name

    @api.depends('amount', 'invoice_ids', 'invoice_ids.state', 'invoice_ids.invoice_line_ids', 'invoice_ids.invoice_line_ids.price_subtotal')
    def _compute_amounts(self):
        for rec in self:
            invoiced_amount = sum(
                rec.invoice_ids.filtered(lambda inv: inv.state == 'posted').mapped('invoice_line_ids.price_subtotal'))
            rec.invoiced_amount = invoiced_amount
            rec.remaining_amount = rec.amount - invoiced_amount

    @api.depends('is_tax_active', 'default_accident_item_id')
    def _compute_tax_ids(self):
        for rec in self:
            if rec.is_tax_active:
                rec.tax_ids = rec.default_accident_item_id.tax_ids
            else:
                rec.tax_ids = [(6, 0, [])]

    @api.constrains('amount')
    def _check_amount_validation(self):
        for rec in self:
            if rec.amount > rec.accident_id.total_evaluation:
                raise ValidationError(
                    _(f"{rec.name} Amount can't be Greater than Total Evaluation"))

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

    def create_invoice(self):
        account_move_obj = self.env['account.move']
        vals_list = []
        for rec in self:
            vals_list.append({
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'journal_id': rec.default_accident_item_id.journal_id.id,
                'currency_id': self.env.company.currency_id.id,
                'accident_due_amount_line_id': rec.id,
                'invoice_line_ids': [(0, 0, {
                    'account_id': rec.default_accident_item_id.account_id.id,
                    'quantity': 1,
                    'price_unit': rec.remaining_amount,
                    'tax_ids': [(6, 0, rec.tax_ids.ids)] if rec.is_tax_active else False
                })]
            })
        account_move_obj.sudo().create(vals_list)
