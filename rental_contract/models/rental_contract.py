# -*- coding: utf-8 -*-


import datetime
import re
from odoo import models, fields, api, _
from odoo.addons.vehicle_info.models.fleet_vehicle import VEHICLE_STATUS, VEHICLE_PARTS_STATUS, AVAILABILITY, WORKING_CONDITION, FUEL_TYPE_STATUS, CAR_SEATS_STATUS

from odoo.exceptions import UserError, ValidationError


class RentalContract(models.Model):
    _name = 'rental.contract'
    _description = 'Rental Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Contract Number', copy=False, readonly=True,
                       default='New')
    # Customer Info Fields
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True,
                                 domain=[('create_from_rental', '=', True)])
    partner_mobile = fields.Char(
        string="Mobile Number", related='partner_id.mobile2', readonly=True, store=True)
    partner_id_no = fields.Char(
        string="ID No", related='partner_id.id_no', readonly=True, store=True)

    # Vehicle Info Fields

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                 domain=lambda self: [('branch_id', 'in', self.env.branches.ids), ('state_id.type', '=', 'ready_to_rent')])
    vehicle_model_datail_id = fields.Many2one(
        'fleet.vehicle.model.detail', string='Vehicle Model Detail', compute="_compute_vehicle_model_datail_id", readonly=True, store=True)
    license_plate = fields.Char(
        string="License Plate", related='vehicle_id.license_plate', readonly=True, store=True)
    model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', related='vehicle_id.model_id', readonly=True, store=True)
    category_id = fields.Many2one(
        'fleet.vehicle.model.category', string='Category', related='vehicle_id.category_id', readonly=True, store=True)

    # Chick List Information
    # Group 1
    ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Ac', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Radio Stereo', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Screen', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Spare Tire Tools', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Tires', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Spare Tires', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # Group 2
    speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Speedometer', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Keys', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Care Seats', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    oil_change_km = fields.Float(
        'Oil Change KM Distance', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Fuel Type Code', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    keys_number = fields.Integer(
        'Number Of Keys', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # Group 3
    safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Safety Triangle', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Fire Extinguisher', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='First Aid Kit', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    oil_type = fields.Char('Oil Type',
                           compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    oil_change_date = fields.Date(
        'Oil Change Date', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Vehicle Status', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    odometer = fields.Float(
        'Odometer', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # Contract Info Fields
    vehicle_branch_id = fields.Many2one(
        'res.branch', string='Pickup Branch', related='vehicle_id.branch_id', readonly=True, store=True)
    pickup_date = fields.Datetime(
        string='Pickup Date', default=fields.Datetime.now)
    duration = fields.Integer(
        string='Duration', default=1)
    expected_return_date = fields.Datetime(
        string='Expected Return Date', compute="_compute_expected_return_date", store=True, readonly=True)
    rental_plan = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Rental Plan', compute="_compute_rental_plan", store=True, readonly=False)
    authorization_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Authorization Type', default='internal')
    authorization_country_id = fields.Many2one(
        'additional.supplementary.services', string='Authorization Country', domain="[('type', '=', 'external_authorization')]")
    need_extra_driver = fields.Selection([
        ('true', 'True'),
        ('false', 'False'),
    ], string='Need Extra Driver', default='false')
    extra_driver_id = fields.Many2one(
        'res.partner', string='Extra Driver', domain="[('create_from_rental', '=', True)]")

    # Additional & Suppl Service Fields
    additional_services = fields.Many2many(
        'additional.supplementary.services', relation="rental_contract_additional_services_rel", string='Additional Services',
        domain="[('type', '=', 'additional')]")
    supplementary_services = fields.Many2many(
        'additional.supplementary.services', relation="rental_contract_supplementary_services_rel", string='Supplementary Services',
        domain="[('type', '=', 'supplementary')]")

    # Financial Info Fields
    daily_rate = fields.Float(
        'Daily Rate', compute='_compute_daily_rate', store=True)
    daily_additional_services_rate = fields.Float(
        'Daily Addition Service Rate', compute='_compute_daily_additional_services_rate', store=True)
    daily_supplementary_services_rate = fields.Float(
        'Daily Supplementary Service Rate', compute='_compute_daily_supplementary_services_rate', store=True)
    daily_authorization_country_rate = fields.Float(
        'Daily Authorization Country Rate', compute='_compute_daily_authorization_country_rate', store=True)
    total_per_day = fields.Float(
        'Total Per Day', compute='_compute_total_per_day', store=True)
    one_time_services = fields.Float(
        'One Time Services', compute='_compute_one_time_services', store=True)
    total_amount = fields.Float(
        'Total Amount', store=True, compute='_compute_total_amount')
    discount_percentage = fields.Float('Discount Percentage (%)')
    tax_percentage = fields.Float('Tax Percentage (%)', default=15)
    tax_amount = fields.Float(
        'Tax Amount', compute='_compute_tax_amount', store=True)
    due_amount = fields.Monetary(
        'Due Amount', store=True, compute='_compute_due_amount', currency_field='company_currency_id')
    paid_amount = fields.Float(
        'Paid Amount', compute='_compute_payment_amount', store=True)
    account_payment_ids = fields.One2many(
        'account.payment', 'rental_contract_id', string='Payments', copy=False)
    payment_count = fields.Integer(
        'Payment Count', compute='_compute_payment_count', store=True)

    # Current Due Amount

    display_actual_days = fields.Integer(
        'Actual Days', compute='_compute_display_open_state_fields')
    display_actual_hours = fields.Integer(
        'Actual Hours', compute='_compute_display_open_state_fields')
    actual_days = fields.Integer('Actual Days', default=0)
    actual_hours = fields.Integer('Actual Hours', default=0)

    display_current_days = fields.Integer(
        'Current Days', compute='_compute_display_open_state_fields')
    display_current_hours = fields.Integer(
        'Current Hours', compute='_compute_display_open_state_fields')
    current_days = fields.Integer('Current Days', default=0)
    current_hours = fields.Integer('Current Hours', default=0)
    assumed_amount = fields.Monetary(
        compute='_compute_assumed_amount', store=True, currency_field='company_currency_id')
    display_current_amount = fields.Monetary(
        'Current Amount', compute='_compute_display_current_amount', currency_field='company_currency_id')
    current_amount = fields.Monetary(
        'Current Amount', currency_field='company_currency_id')

    fines_discount_count = fields.Integer(
        'Discount Count', compute='_compute_fines_discount_count', store=True)
    fines_discount_line_ids = fields.One2many(
        'rental.contract.fines.discount.line', 'rental_contract_id', string='Fines/Discount Lines')
    current_fines_amount = fields.Monetary(
        'Current Fines Amount', currency_field='company_currency_id', compute="_compute_current_fines_amount", store=True)
    current_accident_damage_amount = fields.Monetary(
        'Current Accident Damage Amount', currency_field='company_currency_id')
    discount_voucher_amount = fields.Monetary(
        'Discount Voucher Amount', currency_field='company_currency_id', compute="_compute_discount_voucher_amount", store=True)
    current_km_extra_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id')

    # Calculate KM Popup Fields
    odometer_km_in = fields.Float('KM In')
    free_km_per_day = fields.Float(
        related='vehicle_model_datail_id.free_kilometers', store=True)
    total_free_km = fields.Float(compute="_compute_total_free_km")
    consumed_km = fields.Float(
        compute='_compute_consumed_extra_km')
    total_extra_km = fields.Float(
        compute='_compute_consumed_extra_km')
    extra_km_cost = fields.Float(
        related='vehicle_model_datail_id.extra_kilometers_cost', store=True)
    display_current_km_extra_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id', compute="_compute_display_current_km_extra_amount")

    current_due_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id', compute='_compute_current_due_amount', store=True)

    account_move_ids = fields.One2many(
        'account.move', 'rental_contract_id', string='Related Moves')
    invoice_count = fields.Integer(
        'invoice_count', compute="_compute_move_count")
    credit_note_count = fields.Integer(
        'invoice_count', compute="_compute_move_count")

    # Status Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('opened', 'Opened'),
        ('delivered_pending', 'Delivered Pending'),
        ('delivered_debit', 'Delivered InDebit'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    draft_state = fields.Selection([
        ('customer_info', 'Customer Info'),
        ('vehicle_info', 'Vehicle Info'),
        ('contract_info', 'Contract Info'),
        ('additional_suppl_service', 'Additional & Suppl Service'),
        ('financial_info', 'Financial Info')
    ], string='Status', default='customer_info')

    @api.depends('vehicle_id')
    def _compute_vehicle_model_datail_id(self):
        for record in self:
            if record.vehicle_id:
                record.vehicle_model_datail_id = self.env['fleet.vehicle.model.detail'].search(
                    [('branch_id', '=', record.vehicle_id.branch_id.id), ('vehicle_model_brand_id', '=', record.vehicle_id.model_id.brand_id.id), ('state', '=', 'running')], limit=1)

    @api.depends('vehicle_id')
    def _compute_vehicle_editable_fields(self):
        for record in self:
            if record.vehicle_id:
                record.ac = record.vehicle_id.ac
                record.radio_stereo = record.vehicle_id.radio_stereo
                record.screen = record.vehicle_id.screen
                record.spare_tire_tools = record.vehicle_id.spare_tire_tools
                record.tires = record.vehicle_id.tires
                record.spare_tires = record.vehicle_id.spare_tires
                record.speedometer = record.vehicle_id.speedometer
                record.keys = record.vehicle_id.keys
                record.care_seats = record.vehicle_id.care_seats
                record.oil_change_km = record.vehicle_id.oil_change_km
                record.fuel_type_code = record.vehicle_id.fuel_type_code
                record.keys_number = record.vehicle_id.keys_number
                record.safety_triangle = record.vehicle_id.safety_triangle
                record.fire_extinguisher = record.vehicle_id.fire_extinguisher
                record.first_aid_kit = record.vehicle_id.first_aid_kit
                record.oil_type = record.vehicle_id.oil_type
                record.oil_change_date = record.vehicle_id.oil_change_date
                record.vehicle_status = record.vehicle_id.vehicle_status
                record.odometer = record.vehicle_id.odometer

    @api.depends('pickup_date', 'duration')
    def _compute_expected_return_date(self):
        for record in self:
            if record.pickup_date and record.duration:
                expected_return_date = record.pickup_date + \
                    datetime.timedelta(days=record.duration)
                record.expected_return_date = expected_return_date
            else:
                record.expected_return_date = False

    @api.depends('duration')
    def _compute_rental_plan(self):
        for record in self:
            if record.duration >= 30:
                record.rental_plan = 'monthly'
            elif record.duration >= 7:
                record.rental_plan = 'weekly'
            else:
                record.rental_plan = 'daily'

    @api.depends('vehicle_model_datail_id', 'rental_plan')
    def _compute_daily_rate(self):
        for record in self:
            if record.vehicle_model_datail_id:
                if record.rental_plan == 'daily':
                    record.daily_rate = record.vehicle_model_datail_id.normal_day_price
                elif record.rental_plan == 'weekly':
                    record.daily_rate = record.vehicle_model_datail_id.weekly_day_price
                elif record.rental_plan == 'monthly':
                    record.daily_rate = record.vehicle_model_datail_id.monthly_day_price

    @api.depends('additional_services')
    def _compute_daily_additional_services_rate(self):
        for record in self:
            record.daily_additional_services_rate = sum(
                record.additional_services.filtered(lambda l: l.calculation == 'repeated').mapped('price'))

    @api.depends('supplementary_services')
    def _compute_daily_supplementary_services_rate(self):
        for record in self:
            record.daily_supplementary_services_rate = sum(
                record.supplementary_services.filtered(lambda l: l.calculation == 'repeated').mapped('price'))

    @api.depends('authorization_country_id', 'authorization_type')
    def _compute_daily_authorization_country_rate(self):
        for record in self.filtered(lambda l: l.authorization_country_id and l.authorization_type == 'external'):
            record.daily_authorization_country_rate = record.authorization_country_id.price

    @api.depends('daily_rate', 'daily_additional_services_rate', 'daily_supplementary_services_rate', 'daily_authorization_country_rate')
    def _compute_total_per_day(self):
        for record in self:
            record.total_per_day = record.daily_rate + record.daily_additional_services_rate + \
                record.daily_supplementary_services_rate + \
                record.daily_authorization_country_rate

    @api.depends('additional_services', 'supplementary_services')
    def _compute_one_time_services(self):
        for record in self:
            record.one_time_services = sum(
                record.additional_services.filtered(lambda l: l.calculation == 'once').mapped('price')) + sum(
                record.supplementary_services.filtered(lambda l: l.calculation == 'once').mapped('price'))

    @api.depends('total_per_day', 'duration', 'one_time_services')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (
                record.total_per_day * record.duration) + record.one_time_services

    @api.depends('total_amount', 'tax_percentage')
    def _compute_tax_amount(self):
        for record in self.filtered(lambda l: l.tax_percentage):
            record.tax_amount = record.total_amount - (
                record.total_amount / (1 + (record.tax_percentage / 100)))

    @api.depends('total_amount', 'paid_amount')
    def _compute_due_amount(self):
        for record in self:
            record.due_amount = record.total_amount - record.paid_amount

    @api.depends('account_payment_ids', 'account_payment_ids.state', 'account_payment_ids.amount')
    def _compute_payment_amount(self):
        for record in self:
            record.paid_amount = sum(record.account_payment_ids.filtered(
                lambda p: p.state == 'paid').mapped('amount'))

    @api.depends('account_payment_ids')
    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.account_payment_ids)

    @api.depends('state', 'pickup_date')
    def _compute_display_open_state_fields(self):
        for record in self:
            if record.state == 'opened':
                display_actual_days = record.pickup_date and ((
                    datetime.datetime.now() - record.pickup_date).days + 1) or 0
                display_hours = record.pickup_date and (
                    datetime.datetime.now() - record.pickup_date).seconds // 3600 or 0
                display_actual_hours = 0 \
                    if record.vehicle_model_datail_id and display_hours < record.vehicle_model_datail_id.number_delay_hours_allowed\
                    else display_hours

                display_current_days = display_actual_days if display_actual_hours < 4 else display_actual_days + 1
                display_current_hours = display_actual_hours if display_actual_hours < 4 else 0

                record.actual_days = display_actual_days
                record.actual_hours = display_actual_hours
                record.current_days = display_current_days
                record.current_hours = display_current_hours

            else:
                display_actual_days = 0
                display_actual_hours = 0
                display_current_days = 0
                display_current_hours = 0

            record.display_actual_days = display_actual_days
            record.display_actual_hours = display_actual_hours
            record.display_current_days = display_current_days
            record.display_current_hours = display_current_hours

    @api.depends('total_per_day', 'duration')
    def _compute_assumed_amount(self):
        for record in self:
            if record.total_per_day and record.duration:
                record.assumed_amount = record.total_per_day * record.duration
            else:
                record.assumed_amount = 0.0

    @api.depends('total_per_day', 'display_current_days', 'display_current_hours', 'state')
    def _compute_display_current_amount(self):
        for record in self:
            if record.total_per_day and (record.display_current_days or record.display_current_hours) and record.state == 'opened':
                display_current_amount = (record.total_per_day * record.display_current_days) + \
                    (record.total_per_day / 24) * record.display_current_hours
                record.display_current_amount = display_current_amount
                record.current_amount = display_current_amount
            else:
                record.display_current_amount = 0.0

    @api.depends('fines_discount_line_ids')
    def _compute_fines_discount_count(self):
        for record in self:
            record.fines_discount_count = len(record.fines_discount_line_ids)

    @api.depends('fines_discount_line_ids', 'fines_discount_line_ids.price', 'fines_discount_line_ids.type')
    def _compute_current_fines_amount(self):
        for record in self:
            record.current_fines_amount = sum(record.fines_discount_line_ids.filtered(
                lambda l: l.type == 'fine').mapped('price'))

    @api.depends('fines_discount_line_ids', 'fines_discount_line_ids.price', 'fines_discount_line_ids.type')
    def _compute_discount_voucher_amount(self):
        for record in self:
            record.discount_voucher_amount = sum(record.fines_discount_line_ids.filtered(
                lambda l: l.type == 'discount').mapped('price'))

    @api.depends('free_km_per_day', 'display_current_days')
    def _compute_total_free_km(self):
        for record in self:
            record.total_free_km = record.free_km_per_day * record.display_current_days

    @api.depends('odometer_km_in', 'odometer', 'total_free_km')
    def _compute_consumed_extra_km(self):
        for record in self:
            consumed_km = record.odometer_km_in - record.odometer
            record.consumed_km = consumed_km
            record.total_extra_km = consumed_km - \
                record.total_free_km if record.total_free_km < consumed_km else 0.0

    @api.depends('total_extra_km', 'extra_km_cost')
    def _compute_display_current_km_extra_amount(self):
        for record in self:
            record.display_current_km_extra_amount = record.total_extra_km * record.extra_km_cost

    @api.depends('current_amount', 'current_fines_amount', 'current_accident_damage_amount', 'discount_voucher_amount', 'current_km_extra_amount', 'paid_amount')
    def _compute_current_due_amount(self):
        for record in self:
            record.current_due_amount = record.current_amount + record.current_fines_amount\
                + record.current_accident_damage_amount + record.current_km_extra_amount\
                - (record.discount_voucher_amount + record.paid_amount)

    @api.depends('account_move_ids', 'account_move_ids.move_type')
    def _compute_move_count(self):
        for record in self:
            record.invoice_count = len(record.account_move_ids.filtered(
                lambda move: move.move_type == 'out_invoice'))
            record.credit_note_count = len(record.account_move_ids.filtered(
                lambda move: move.move_type == 'out_refund'))

    def next_draft_state(self):
        if self.draft_state == 'customer_info':
            self.draft_state = 'vehicle_info'
        elif self.draft_state == 'vehicle_info':
            self.draft_state = 'contract_info'
        elif self.draft_state == 'contract_info':
            self.draft_state = 'additional_suppl_service'
        elif self.draft_state == 'additional_suppl_service':
            self.draft_state = 'financial_info'

    def prev_draft_state(self):
        if self.draft_state == 'financial_info':
            self.draft_state = 'additional_suppl_service'
        elif self.draft_state == 'additional_suppl_service':
            self.draft_state = 'contract_info'
        elif self.draft_state == 'contract_info':
            self.draft_state = 'vehicle_info'
        elif self.draft_state == 'vehicle_info':
            self.draft_state = 'customer_info'

    def action_open(self):
        if not all(record.due_amount <= 0 for record in self):
            raise UserError(
                _('You cannot open this contract because due amount must be less or equal zero.'))

        rental_vehicle_state = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'rented')], limit=1)

        if not rental_vehicle_state:
            raise ValidationError(
                _("Please configure Rent state in vehicle states."))

        self.vehicle_id.write({'state_id': rental_vehicle_state.id})

        for rec in self:
            rec.name = self.env['ir.sequence'].next_by_code(
                'rental.contract.seq')

        self.write({'state': 'opened'})

    def action_delivered_pending(self):
        self.write({'state': 'delivered_pending'})

    def set_current_km_extra_amount(self):
        self.ensure_one()
        if self.odometer > self.odometer_km_in:
            raise ValidationError(_('KM In Must Be greater Than KM Out'))
        self.current_km_extra_amount = self.display_current_km_extra_amount
        return {'type': 'ir.actions.act_window_close'}

    def action_delivered_debit(self):
        self.write({'state': 'delivered_debit'})

    def action_close(self):
        # if not all(payment.state == 'paid' for payment in self.account_payment_ids):
        #     raise UserError(
        #         _('You cannot close this contract because there are payments that are not in posted state.'))
        self.write({'state': 'closed'})

    def action_cancel(self):
        if not all(payment.state == 'draft' for payment in self.account_payment_ids):
            raise UserError(
                _('You cannot cancel this contract because there are payments that are not in draft state.'))
        self.account_payment_ids.action_cancel()
        self.write({'state': 'cancelled'})

    def action_pay(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pay'),
            'res_model': 'rental.contract.payment.register',
            'view_mode': 'form',
            'target': 'new',
        }

    def view_vehicle_model_pricing(self):
        view_id = self.env.ref(
            'rental_contract.fleet_vehicle_model_pricing_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicle Model Pricing'),
            'res_model': 'fleet.vehicle.model.detail',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.vehicle_model_datail_id.id,
            'views': [[view_id, 'form']]
        }

    def view_calculate_km(self):
        view_id = self.env.ref(
            'rental_contract.view_rental_contract_calculate_km_form').id
        if not self.odometer_km_in:
            self.odometer_km_in = self.odometer
        return {
            'type': 'ir.actions.act_window',
            'name': _('Calculate KM'),
            'res_model': 'rental.contract',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [[view_id, 'form']]
        }

    def view_related_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id)]
        }

    def view_related_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id), ('move_type', '=', 'out_invoice')]
        }

    def view_related_credit_note(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Note'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id), ('move_type', '=', 'out_refund')]
        }


class RentalContractFinesDiscountLine(models.Model):
    _name = 'rental.contract.fines.discount.line'
    _description = 'Rental Contract Fines Discount Line'
    _rec_name = 'name'

    fines_discount_id = fields.Many2one(
        'contract.fines.discount.config', string='Fines/Discount', required=True)
    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', required=True)
    name = fields.Char(string='Description', required=True)
    price = fields.Float(
        string='Price', related='fines_discount_id.price', store=True)
    type = fields.Selection([
        ('fine', 'Fine'),
        ('discount', 'Discount'),
    ], string='Type', required=True)
