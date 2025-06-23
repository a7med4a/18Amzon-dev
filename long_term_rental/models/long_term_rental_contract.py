# -*- coding: utf-8 -*-


import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import calendar
import pytz
from odoo import models, fields, api, _
from odoo.addons.vehicle_info.models.fleet_vehicle import VEHICLE_STATUS, VEHICLE_PARTS_STATUS, AVAILABILITY, WORKING_CONDITION, FUEL_TYPE_STATUS, CAR_SEATS_STATUS

from odoo.exceptions import UserError, ValidationError


class LongTermRentalContract(models.Model):
    _name = 'long.term.rental.contract'
    _description = 'Long Term Rental Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Contract Number', copy=False, readonly=True,
                       default='New')
    # Customer Info Fields
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True, readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True)
    partner_mobile = fields.Char(
        string="Mobile Number", related='partner_id.mobile2', readonly=True, store=True)
    partner_id_no = fields.Char(
        string="ID No", related='partner_id.id_no', readonly=True, store=True)

    # Vehicle Info Fields

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    image_128 = fields.Image(related='vehicle_id.image_128')
    vehicle_model_datail_id = fields.Many2one(
        'fleet.vehicle.model.detail', string='Vehicle Model Detail', compute="_compute_vehicle_model_datail_id", readonly=True)
    license_plate = fields.Char(
        string="License Plate", related='vehicle_id.license_plate', readonly=True, store=True)
    model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', related='vehicle_id.model_id', readonly=True, store=True)
    category_id = fields.Many2one(
        'fleet.vehicle.model.category', string='Category', related='vehicle_id.category_id', readonly=True, store=True)

    # Chick List Out Information
    # --------------------> Group 1
    out_ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Ac', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Radio Stereo', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Screen', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Spare Tire Tools', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Tires', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Spare Tires', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # --------------------> Group 2
    out_speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Speedometer', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Keys', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Care Seats', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_oil_change_km = fields.Float(
        'Oil Change KM Distance', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Fuel Type Code', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_keys_number = fields.Integer(
        'Number Of Keys', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # --------------------> Group 3
    out_safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Safety Triangle', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Fire Extinguisher', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='First Aid Kit', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_oil_type = fields.Char('Oil Type',
                               compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_oil_change_date = fields.Date(
        'Oil Change Date', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Vehicle Status', compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    out_odometer = fields.Float(
        'Odometer', compute="_compute_vehicle_editable_fields", store=True, readonly=False)

    # Contract Info Fields
    vehicle_branch_id = fields.Many2one(
        'res.branch', string='Pickup Branch', related='vehicle_id.branch_id', readonly=True, store=True)
    pickup_date = fields.Datetime(
        string='Pickup Date', default=fields.Datetime.now)
    contract_start_date = fields.Datetime(
        string='Contract Start Date', default=fields.Datetime.now)
    contract_end_date = fields.Datetime(
        string='Contract End Date', compute="_compute_contract_end_date", store=True, readonly=True)
    duration = fields.Integer(
        string='Duration', default=1)
    expected_return_date = fields.Datetime(
        string='Expected Return Date', compute="_compute_expected_return_date", store=True, readonly=True)
    rental_plan = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Rental Plan', default='monthly', readonly=False)
    authorization_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Authorization Type', default='internal')

    # Additional & Suppl Service Fields
    additional_service_ids = fields.Many2many(
        'additional.supplementary.services.line', relation="long_term_rental_contract_additional_services_line_rel", string='Additional Services')
    supplementary_service_ids = fields.Many2many(
        'additional.supplementary.services.line', relation="long_term_rental_contract_supplementary_services_line_rel", string='Supplementary Services')
    authorization_country_id = fields.Many2one(
        'additional.supplementary.services.line', string='Authorization Country',
        domain="[('type', '=', 'external_authorization')]")
    need_extra_driver = fields.Selection([
        ('true', 'True'),
        ('false', 'False'),
    ], string='Need Extra Driver', default='false')
    extra_driver_id = fields.Many2one(
        'res.partner', string='Extra Driver', domain="[('create_from_rental', '=', True)]")
    daily_rate = fields.Float('Daily Rate')
    daily_additional_services_rate = fields.Float(
        'Daily Addition Service Rate', store=True)
    daily_supplementary_services_rate = fields.Float(
        'Daily Supplementary Service Rate', store=True)
    daily_authorization_country_rate = fields.Float(
        'Daily Authorization Country Rate', store=True)
    total_per_day = fields.Float(
        'Total Per Day', store=True)
    due_amount = fields.Monetary(
        'Due Amount', store=True, currency_field='company_currency_id')
    # Financial Info Fields

    one_time_services = fields.Float(
        'One Time Services', compute='_compute_one_time_services', store=True)
    total_amount = fields.Float(
        'Total Amount', store=True, compute='_compute_total_amount')
    discount_percentage = fields.Float('Discount Percentage (%)')
    tax_percentage = fields.Float(
        'Tax Percentage (%)', compute="_compute_tax_percentage", store=True)
    tax_amount = fields.Float(
        'Tax Amount', compute='_compute_tax_amount', store=True)
    amount_before_tax = fields.Float(
        'Tax Amount', compute='_compute_tax_amount', store=True)
    paid_amount = fields.Float(
        'Paid Amount', compute='_compute_payment_amount', store=True)
    advanced_paid_amount = fields.Float(string='Paid Amount', readonly=True)
    account_payment_ids = fields.One2many(
        'account.payment', 'term_long_rental_contract_id', string='Payments Paid', copy=False)
    payment_count = fields.Integer(
        'Payment Count', compute='_compute_payment_count', store=True)
    rental_configuration_id = fields.Many2one('rental.config.settings')

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
        'Current Amount', currency_field='company_currency_id')
    current_amount = fields.Monetary(
        'Current Amount', currency_field='company_currency_id')

    fines_discount_count = fields.Integer(
        'Discount Count', compute='_compute_fines_discount_count', store=True)
    fines_discount_line_ids = fields.One2many(
        'rental.contract.fines.discount.line', 'long_term_rental_contract_id', string='Fines/Discount Lines')
    current_fines_amount = fields.Monetary(
        'Current Fines Amount', currency_field='company_currency_id', compute="_compute_current_fines_amount", store=True)
    current_accident_damage_amount = fields.Monetary(
        'Current Accident Damage Amount', currency_field='company_currency_id')
    discount_voucher_amount = fields.Monetary(
        'Discount Voucher Amount', currency_field='company_currency_id', compute="_compute_discount_voucher_amount", store=True)
    current_km_extra_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id')

    # Calculate KM Popup Fields
    in_odometer = fields.Float(
        'Odometer')
    total_free_km = fields.Float(compute="_compute_total_free_km")
    consumed_km = fields.Float(
        compute='_compute_consumed_extra_km')
    total_extra_km = fields.Float(
        compute='_compute_consumed_extra_km')
    display_current_km_extra_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id', compute="_compute_display_current_km_extra_amount")

    current_due_amount = fields.Monetary(
        'Current KM Extra Amount', currency_field='company_currency_id', compute='_compute_current_due_amount', store=True)

    account_move_ids = fields.One2many(
        'account.move', 'rental_contract_id', string='Related Moves')
    invoice_count = fields.Integer(
        'invoice_count', compute="_compute_move_count", store=True)
    credit_note_count = fields.Integer(
        'invoice_count', compute="_compute_move_count", store=True)

    # Closing State
    drop_off_date = fields.Datetime('Drop Off Date', copy=False)

    # Chick List IN Information
    # --------------------> Group 1
    in_ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Ac')
    in_radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Radio Stereo')
    in_screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Screen')
    in_spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Spare Tire Tools')
    in_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Tires')
    in_spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Spare Tires')

    # --------------------> Group 2
    in_speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Speedometer')
    in_keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Keys')
    in_care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Care Seats')
    in_oil_change_km = fields.Float(
        'Oil Change KM Distance')
    in_fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Fuel Type Code')
    in_keys_number = fields.Integer(
        'Number Of Keys')

    # --------------------> Group 3
    in_safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Safety Triangle')
    in_fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Fire Extinguisher')
    in_first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='First Aid Kit')
    in_oil_type = fields.Char('Oil Type',
                              compute="_compute_vehicle_editable_fields", store=True, readonly=False)
    in_oil_change_date = fields.Date(
        'Oil Change Date')
    in_vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Vehicle Status')

    vehicle_in_state = fields.Selection([
        ('none', 'None'),
        ('damage', 'Damage'),
        ('accident', 'Accident'),
        ('other', 'Other'),
    ], string='Has accident / damage')

    vehicle_in_state_other_reason = fields.Char('Other Reason')

    # Accident Announcement Field
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

    accident_ids = fields.One2many(
        'fleet.accident', 'rental_contract_id', string='accident')
    accident_count = fields.Integer(
        'invoice_count', compute="_compute_accident_count", store=True)

    damage_ids = fields.One2many(
        'fleet.damage', 'rental_contract_id', string='Damage')
    damage_count = fields.Integer(
        'invoice_count', compute="_compute_damage_count", store=True)
    contract_type = fields.Selection(string='Type', selection=[(
        'rental', 'Rental'), ('long_term', 'Long Term'),], default='long_term')
    # Status Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('opened', 'Opened'),
        ('close_info', 'Closing Info'),
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

    # Configuration Fields

    #   ----------> Model Pricing Fields
    model_pricing_vehicle_brand_id = fields.Many2one(
        comodel_name='fleet.vehicle.model.brand', string='Vehicle Model Brand')
    model_pricing_free_kilometers = fields.Float(string='Free Kilometers')
    model_pricing_extra_kilometers_cost = fields.Float(
        string='Extra kilometers cost')
    model_pricing_number_delay_hours_allowed = fields.Float()
    model_pricing_min_normal_day_price = fields.Float()
    model_pricing_min_weekly_day_price = fields.Float()
    model_pricing_min_monthly_day_price = fields.Float()
    model_pricing_max_normal_day_price = fields.Float()
    model_pricing_max_weekly_day_price = fields.Float()
    model_pricing_max_monthly_day_price = fields.Float()
    model_pricing_min_customer_age = fields.Float()
    model_pricing_max_customer_age = fields.Float()
    model_pricing_full_tank_cost = fields.Float()
    model_pricing_start_date = fields.Date()
    model_pricing_end_date = fields.Date()

    #  ----------> Additional Supplementary Services
    additional_supplement_service_line_ids = fields.One2many(
        'additional.supplementary.services.line', 'long_term_rental_contract_id', string='Additional Supplement Service Lines')
    additional_supplement_service_count = fields.Integer(
        compute="_compute_additional_supplement_service_count", store=True)

    #  ----------> Rental Config
    trip_days_account_id = fields.Many2one(
        "account.account", string="Trip Days Account")
    trip_days_label = fields.Char(string="Label")
    extra_km_account_id = fields.Many2one(
        "account.account", string="Trip Days Account")
    extra_km_label = fields.Char(string="Label")
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    #  ----------> Invoice Log
    schedular_invoice_log_ids = fields.One2many(
        'rental.contract.schedular.invoice.log', 'rental_contract_id')

    schedular_invoice_log_count = fields.Integer(
        compute="_compute_schedular_invoice_log_count", store=True)
    long_term_pricing_request = fields.Char(
        compute="_compute_long_term_pricing_request", string='Long Term Pricing Request', store=True)
    reservation_no = fields.Char(
        "Reservation Number", default=lambda self: False)
    invoice_damage_accident = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('none', 'None')], string='Invoice Accident/Damage', readonly=True)
    monthly_rate = fields.Float(
        compute="_compute_monthly_rate", string="Monthly Rate")
    advanced_payment = fields.Float(string="Advanced Payment")
    ownership_amount = fields.Float(string="Ownership Payment")
    remaining_amount = fields.Float(
        string="Remaining Amount", compute="_compute_remaining_amount")
    monthly_installment = fields.Float(
        string="Monthly Installment", compute="_compute_monthly_installment")
    contract_installment_ids = fields.One2many(
        comodel_name='contract.installment.line',
        inverse_name='long_term_contract_id',
        required=False)

    @api.constrains('partner_id')
    def _check_blacklist_status(self):
        for contract in self:
            if contract.partner_id.blacklist_status == 'blocked':
                raise UserError(
                    _("Cannot create rental contract for customer %s. Reason: %s") % (
                        contract.partner_id.name,
                        contract.partner_id.blacklist_reason or 'Blocked'
                    )
                )

    @api.onchange('partner_id')
    def _onchange_partner_id_blacklist(self):
        if self.partner_id.blacklist_status == 'warning':
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                {
                    'title': _("Warning"),
                    'message': _("Customer %s is under warning. Reason: %s") % (
                        self.partner_id.name,
                        self.partner_id.blacklist_reason or 'N/A'
                    ),
                    'type': 'warning',
                    'sticky': True
                }
            )

        return {}

    @api.depends('vehicle_id', 'draft_state')
    def _compute_vehicle_model_datail_id(self):
        for record in self:
            if record.draft_state == 'vehicle_info' and record.vehicle_id:
                record.vehicle_model_datail_id = self.env['fleet.vehicle.model.detail'].search(
                    [('branch_ids', 'in', [record.vehicle_id.branch_id.id]), ('vehicle_model_brand_id', '=', record.vehicle_id.model_id.brand_id.id), ('state', '=', 'running')], limit=1)
            else:
                record.vehicle_model_datail_id = False

    @api.depends('vehicle_id')
    def _compute_vehicle_editable_fields(self):
        for record in self:
            if record.vehicle_id:
                record.out_ac = record.vehicle_id.ac
                record.out_radio_stereo = record.vehicle_id.radio_stereo
                record.out_screen = record.vehicle_id.screen
                record.out_spare_tire_tools = record.vehicle_id.spare_tire_tools
                record.out_tires = record.vehicle_id.tires
                record.out_spare_tires = record.vehicle_id.spare_tires
                record.out_speedometer = record.vehicle_id.speedometer
                record.out_keys = record.vehicle_id.keys
                record.out_care_seats = record.vehicle_id.care_seats
                record.out_oil_change_km = record.vehicle_id.oil_change_km
                record.out_fuel_type_code = record.vehicle_id.fuel_type_code
                record.out_keys_number = record.vehicle_id.keys_number
                record.out_safety_triangle = record.vehicle_id.safety_triangle
                record.out_fire_extinguisher = record.vehicle_id.fire_extinguisher
                record.out_first_aid_kit = record.vehicle_id.first_aid_kit
                record.out_oil_type = record.vehicle_id.oil_type
                record.out_oil_change_date = record.vehicle_id.oil_change_date
                record.out_vehicle_status = record.vehicle_id.vehicle_status
                record.out_odometer = record.vehicle_id.odometer

    @api.depends('pickup_date', 'duration')
    def _compute_expected_return_date(self):
        for record in self:
            if record.pickup_date and record.duration:
                expected_return_date = record.pickup_date + \
                    datetime.timedelta(days=record.duration)
                record.expected_return_date = expected_return_date
            else:
                record.expected_return_date = False

    @api.depends('vehicle_id')
    def _compute_monthly_rate(self):
        for record in self:
            long_term_pricing_request = self.env['long.term.pricing.request.line'].search(
                [('vehicle_id', '=', record.vehicle_id.id),
                 ('long_term_pricing_request_id.state', 'in',
                  ('draft', 'under_review', 'confirmed')),
                 ('pricing_status', '=', 'running')], limit=1)
            if long_term_pricing_request:
                record.monthly_rate = long_term_pricing_request.rental_pricing_monthly
            else:
                record.monthly_rate = 0

    @api.depends('additional_service_ids', 'supplementary_service_ids', 'additional_supplement_service_line_ids')
    def _compute_one_time_services(self):
        for record in self:
            record.one_time_services = sum(
                record.additional_supplement_service_line_ids.mapped('price'))

    @api.depends('duration', 'one_time_services', 'monthly_rate')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (
                record.monthly_rate * record.duration) + record.one_time_services

    @api.depends('total_amount', 'tax_percentage')
    def _compute_tax_amount(self):
        for record in self.filtered(lambda l: l.tax_percentage):
            record.tax_amount = record.total_amount - (
                record.total_amount / (1 + (record.tax_percentage / 100)))
            record.amount_before_tax = record.total_amount - record.tax_amount

    @api.depends('total_amount', 'advanced_payment')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.total_amount - record.paid_amount

    @api.depends('remaining_amount', 'duration')
    def _compute_monthly_installment(self):
        for record in self:
            record.monthly_installment = (
                record.remaining_amount / record.duration) if record.duration > 0 else record.remaining_amount

    @api.depends('account_payment_ids', 'account_payment_ids.state', 'account_payment_ids.amount')
    def _compute_payment_amount(self):
        for record in self:
            record.paid_amount = sum(record.account_payment_ids.filtered(
                lambda p: p.state == 'paid').mapped('amount'))

    @api.depends('account_payment_ids')
    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.account_payment_ids)

    @api.depends('rental_configuration_id')
    def _compute_tax_percentage(self):
        for rec in self:
            if rec.rental_configuration_id:
                rec.tax_percentage = sum(
                    rec.rental_configuration_id.tax_ids.mapped('amount'))
            else:
                rec.tax_percentage = 0.0

    @api.depends('state', 'pickup_date')
    def _compute_display_open_state_fields(self):
        for record in self:
            if record.state == 'opened':
                display_actual_days = record.pickup_date and (
                    datetime.datetime.now() - record.pickup_date).days or 0
                display_hours = record.pickup_date and (
                    datetime.datetime.now() - record.pickup_date).seconds // 3600 or 0
                display_actual_hours = 0 \
                    if display_hours < record.model_pricing_number_delay_hours_allowed\
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

    @api.depends('model_pricing_free_kilometers', 'display_current_days')
    def _compute_total_free_km(self):
        for record in self:
            record.total_free_km = record.model_pricing_free_kilometers * \
                record.display_current_days

    @api.depends('in_odometer', 'out_odometer', 'total_free_km')
    def _compute_consumed_extra_km(self):
        for record in self:
            consumed_km = record.in_odometer - record.out_odometer
            record.consumed_km = consumed_km
            record.total_extra_km = consumed_km - \
                record.total_free_km if record.total_free_km < consumed_km else 0.0

    @api.depends('total_extra_km', 'model_pricing_extra_kilometers_cost')
    def _compute_display_current_km_extra_amount(self):
        for record in self:
            record.display_current_km_extra_amount = record.total_extra_km * \
                record.model_pricing_extra_kilometers_cost

    @api.depends('current_amount', 'current_fines_amount', 'current_accident_damage_amount', 'discount_voucher_amount', 'current_km_extra_amount', 'paid_amount')
    def _compute_current_due_amount(self):
        for record in self:
            record.current_due_amount = record.current_amount + record.current_fines_amount\
                + record.current_accident_damage_amount + record.current_km_extra_amount\
                - (record.discount_voucher_amount + record.paid_amount)

    @api.depends('account_move_ids', 'account_move_ids.move_type', 'damage_ids', 'damage_ids.invoice_id', 'damage_ids.state')
    def _compute_move_count(self):
        for record in self:
            invoice_contract_related = len(record.account_move_ids.filtered(
                lambda move: move.move_type == 'out_invoice'))
            invoice_damage_relate = len(record.damage_ids.filtered(
                lambda damage: damage.invoice_id != False and damage.invoice_id.state == 'posted'))
            print(record.damage_ids.filtered(
                lambda damage: damage.invoice_id != False))
            record.invoice_count = invoice_contract_related + invoice_damage_relate
            record.credit_note_count = len(record.account_move_ids.filtered(
                lambda move: move.move_type == 'out_refund'))

    # Done
    @api.depends('additional_supplement_service_line_ids')
    def _compute_additional_supplement_service_count(self):
        for rec in self:
            rec.additional_supplement_service_count = len(
                rec.additional_supplement_service_line_ids)

    @api.depends('schedular_invoice_log_ids')
    def _compute_schedular_invoice_log_count(self):
        for rec in self:
            rec.schedular_invoice_log_count = len(
                rec.schedular_invoice_log_ids)

    @api.depends('accident_ids')
    def _compute_accident_count(self):
        for rec in self:
            rec.accident_count = len(rec.accident_ids)

    @api.depends('damage_ids')
    def _compute_damage_count(self):
        for rec in self:
            rec.damage_count = len(rec.damage_ids)

    # Done
    @api.depends('contract_start_date', 'duration')
    def _compute_contract_end_date(self):
        for rec in self:
            if rec.contract_start_date:
                rec.contract_end_date = rec.contract_start_date + \
                    relativedelta(months=rec.duration)
            else:
                rec.contract_end_date = False

    # Done
    @api.depends('vehicle_id')
    def _compute_long_term_pricing_request(self):
        for rec in self:
            long_term_pricing_request = self.env['long.term.pricing.request.line'].search([('vehicle_id', '=', rec.vehicle_id.id), (
                'long_term_pricing_request_id.state', 'in', ('draft', 'under_review', 'confirmed')), ('pricing_status', '=', 'running')], limit=1)
            if long_term_pricing_request:
                rec.long_term_pricing_request = long_term_pricing_request.long_term_pricing_request_id.name
            else:
                rec.long_term_pricing_request = False

    # Done
    def check_vehicle_long_term_pricing(self):
        for rec in self:
            long_term_request_price_obj = self.env['long.term.pricing.request.line']
            long_term_request_price = long_term_request_price_obj.search(
                [('vehicle_id', '=', rec.vehicle_id.id)])
            if not long_term_request_price:
                raise ValidationError(
                    _("No Long Term Pricing Request Found For Selected Vehicle,Please Create New one !"))
            long_term_request_price_running = self.env['long.term.pricing.request.line'].search(
                [('vehicle_id', '=', rec.vehicle_id.id),
                 ('long_term_pricing_request_id.state', 'in',
                  ('draft', 'under_review', 'confirmed')),
                 ('pricing_status', '=', 'running')])
            if not long_term_request_price_running:
                raise ValidationError(
                    _("No Running Long Term Pricing Request Found For Selected Vehicle,Please Create Running one !"))

    # Done
    @api.constrains('partner_id')
    def _check_contract_partner_id_validity(self):
        matched_customer_contracts = self.search(
            [('partner_id', 'in', self.partner_id.ids), ('state', 'in', ['draft', 'opened'])])

        for rec in self.filtered(lambda c: c.partner_id):
            # check customer has other draft / running contracts
            if matched_customer_contracts.filtered(lambda c: c.partner_id == rec.partner_id and c.id != rec.id):
                conflict_contract = matched_customer_contracts.filtered(
                    lambda c: c.partner_id == rec.partner_id)[0]
                raise ValidationError(
                    _(f"Selected Customer Has Contract {conflict_contract.name} That In {conflict_contract.state} State"))

    # Done
    @api.constrains('vehicle_id')
    def _check_contract_vehicle_id_validity(self):
        matched_policy_logs = self.env['insurance.policy.line'].search(
            [('vehicle_id', 'in', self.vehicle_id.ids), ('insurance_status', '=', 'running')])
        matched_vehicle_contracts = self.search(
            [('vehicle_id', 'in', self.vehicle_id.ids), ('state', 'in', ['draft', 'opened'])])
        for rec in self.filtered(lambda c: c.vehicle_id):
            # Check Insurance Policy
            if not matched_policy_logs.filtered(lambda p: p.vehicle_id == rec.vehicle_id):
                raise ValidationError(
                    _("Selected Vehicle Hasn't Running Insurance Policy"))

            # Check vehicle Exist in other draft / running contracts
            if matched_vehicle_contracts.filtered(lambda c: c.vehicle_id == rec.vehicle_id and c.id != rec.id):
                conflict_contract = matched_vehicle_contracts.filtered(
                    lambda c: c.vehicle_id == rec.vehicle_id and c.id != rec.id)[0]
                raise ValidationError(
                    _(f"Selected Vehicle Exists On Contract {conflict_contract.name} That In {conflict_contract.state} State"))

    @api.constrains('accident_date', 'announcement_date')
    def _check_accident_date(self):
        for rec in self:
            if rec.announcement_date and rec.accident_date and rec.announcement_date < rec.accident_date:
                raise ValidationError(
                    "Accident Date must be less than Announcement Date")

    # Done

    @api.constrains('advanced_payment')
    def _check_advanced_payment(self):
        for rec in self:
            if rec.advanced_payment and rec.total_amount and rec.advanced_payment > rec.total_amount:
                raise ValidationError(
                    _("Advanced Payment must be less than Total Amount"))

    def get_day_hour(self, date_from, date_to):
        self.ensure_one()
        actual_days = date_from and\
            (date_to - date_from).days or 0
        hours = date_from and (
            date_to - date_from).seconds // 3600 or 0
        actual_hours = 0 \
            if hours < self.model_pricing_number_delay_hours_allowed\
            else hours

        current_days = actual_days if actual_hours < 4 else actual_days + 1
        current_hours = actual_hours if actual_hours < 4 else 0
        return {
            'actual_days': actual_days,
            'actual_hours': actual_hours,
            'current_days': current_days,
            'current_hours': current_hours,
        }

    def _prepare_account_move_values(self, invoice_date=fields.Date.today()):
        self.ensure_one()
        allowed_journal_ids = self.vehicle_branch_id.sales_journal_ids
        if not allowed_journal_ids:
            raise ValidationError(
                _(f"Add Sales Journals To {self.vehicle_branch_id.name}"))

        return {
            'move_type': 'out_invoice',
            'rental_contract_id': self.id,
            'invoice_date': invoice_date,
            'journal_id': allowed_journal_ids[0].id,
            'partner_id': self.partner_id.id,
            'currency_id': self.company_currency_id.id,
        }

    def _create_missing_schedular_invoice(self, drop_off_date):
        local_timezone = pytz.timezone(self.company_id.tz or 'UTC')

        drop_off_date_before_month = drop_off_date - relativedelta(month=1)
        last_day_of_last_month = calendar.monthrange(
            drop_off_date_before_month.year, drop_off_date_before_month.month)[1]

        local_date_to = drop_off_date_before_month.replace(
            day=last_day_of_last_month,  hour=23, minute=59, second=59)
        utc_date_to = local_timezone.localize(
            local_date_to).astimezone(pytz.UTC).replace(tzinfo=None)

        invoice_vals_list = self.create_schedular_contract_invoice_list(
            utc_date_to)

        invoices = self.env['account.move'].create(invoice_vals_list)
        invoices.action_post()

    def get_closing_day_hour(self, drop_off_date):
        self.ensure_one()
        local_timezone = pytz.timezone(self.company_id.tz or 'UTC')
        current_date_time = fields.Datetime.now()
        local_first_month_date_time = current_date_time.replace(
            day=1, hour=0, minute=0, second=0)
        utc_first_month_date_time = local_timezone.localize(
            local_first_month_date_time).astimezone(pytz.UTC).replace(tzinfo=None)

        date_to = drop_off_date
        date_from = self.pickup_date
        if self.pickup_date < utc_first_month_date_time:
            date_from = utc_first_month_date_time

        day_hour_dict = self.get_day_hour(date_from, date_to)

        # Get All Current hours of contract
        if date_from != self.pickup_date:
            pickup_date_day_hour_dict = self.get_day_hour(
                self.pickup_date, date_to)
            day_hour_dict.update(
                {'current_hours': pickup_date_day_hour_dict.get('current_hours')})

        return day_hour_dict

    def get_schedular_day_hour(self, date_time):
        self.ensure_one()
        local_timezone = pytz.timezone(self.company_id.tz or 'UTC')
        date_from = self.pickup_date
        last_current_month_day = calendar.monthrange(
            date_time.year, date_time.month)[1]
        local_first_month_date_time = date_time.replace(
            day=1, hour=0, minute=0, second=0)
        local_last_month_date_time = date_time.replace(
            day=last_current_month_day, hour=23, minute=59, second=59)

        utc_first_month_date_time = local_timezone.localize(
            local_first_month_date_time).astimezone(pytz.UTC).replace(tzinfo=None)
        utc_last_month_date_time = local_timezone.localize(
            local_last_month_date_time).astimezone(pytz.UTC).replace(tzinfo=None)

        date_to = utc_last_month_date_time
        if self.pickup_date < utc_first_month_date_time:
            date_from = utc_first_month_date_time

        day_hour_dict = self.get_day_hour(date_from, date_to)
        # postponement Current hours to be total calculated in closing invoice
        if date_from == self.pickup_date:
            day_hour_dict.update({'current_hours': 0})

        day_hour_dict.update({'date_from': date_from, 'date_to': date_to})
        return day_hour_dict

    def _get_dates_to_create(self, date_to):
        self.ensure_one()
        dates_to_create = []

        local_timezone = pytz.timezone(self.company_id.tz or 'UTC')
        last_pickup_month_day = calendar.monthrange(
            self.pickup_date.year, self.pickup_date.month)[1]

        local_start_date = self.pickup_date.replace(
            day=last_pickup_month_day,  hour=23, minute=30)
        utc_start_date = local_timezone.localize(
            local_start_date).astimezone(pytz.UTC).replace(tzinfo=None)

        while (utc_start_date <= date_to):
            date_exist = False
            for log in self.schedular_invoice_log_ids:
                if utc_start_date >= log.date_from and utc_start_date <= log.date_from:
                    date_exist = True
                    break
            if not date_exist:
                dates_to_create.append(utc_start_date)
            utc_start_date += relativedelta(months=1)
            last_start_date_month_day = calendar.monthrange(
                utc_start_date.year, utc_start_date.month)[1]
            utc_start_date = utc_start_date.replace(
                day=last_start_date_month_day)

        return dates_to_create

    def create_schedular_contract_invoice_list(self, date_to=fields.Datetime.now()):
        self.ensure_one()
        contract_invoice_vals_list = []
        dates_to_create = self._get_dates_to_create(date_to)
        for date_time in dates_to_create:
            day_hour_dict = self.get_schedular_day_hour(date_time)
            invoice_vals = self._prepare_invoice_vals_from_dates(
                day_hour_dict)
            if invoice_vals:

                invoice_log_id = self.env['rental.contract.schedular.invoice.log'].sudo().create({
                    'actual_days': day_hour_dict.get('actual_days'),
                    'actual_hours': day_hour_dict.get('actual_hours'),
                    'current_days': day_hour_dict.get('current_days'),
                    'current_hours': day_hour_dict.get('current_hours'),
                    'date_from': day_hour_dict.get('date_from'),
                    'date_to': day_hour_dict.get('date_to'),
                    'rental_contract_id': self.id
                })
                invoice_vals.update({'invoice_log_id': invoice_log_id.id})
                contract_invoice_vals_list.append(invoice_vals)
        return contract_invoice_vals_list

    @api.model
    def schedular_create_repeated_services_invoices(self):
        # Run On Only Open Contracts
        invoice_vals_list = []

        for contract in self.search([('state', '=', 'opened')]):
            invoice_vals_list.extend(
                contract.create_schedular_contract_invoice_list())

        invoices = self.env['account.move'].create(invoice_vals_list)
        invoices.action_post()

    def create_closing_invoice(self, drop_off_date):
        invoice_vals_list = []

        for contract in self.filtered(lambda c: c.state == 'opened'):
            # create missing schedular if exist
            contract._create_missing_schedular_invoice(drop_off_date)
            # Create Drop Off Invoice
            day_hour_dict = contract.get_closing_day_hour(drop_off_date)
            invoice_vals = contract._prepare_invoice_vals_from_dates(
                day_hour_dict)
            if invoice_vals:
                invoice_vals_list.append(invoice_vals)

        invoices = self.env['account.move'].create(invoice_vals_list)
        invoices.action_post()

    def check_model_pricing(self):
        for rec in self:
            if not rec.vehicle_model_datail_id:
                raise ValidationError(
                    _(f"Configure Model Pricing For {rec.vehicle_id.display_name}"))

    # Done
    # def check_customer_age(self):
    #     for rec in self:
    #         if rec.vehicle_model_datail_id.min_customer_age > float(rec.partner_id.age) or rec.vehicle_model_datail_id.max_customer_age < float(rec.partner_id.age):
    #             raise ValidationError(
    #                 _("Selected customer age is out of vehicle age range !"))

    # Done
    def assign_model_pricing_fields(self):
        for rec in self:

            # Set Configuration Fields
            #   ----------> Model Pricing Fields
            rec.model_pricing_vehicle_brand_id = rec.vehicle_model_datail_id.vehicle_model_brand_id
            rec.model_pricing_free_kilometers = rec.vehicle_model_datail_id.free_kilometers
            rec.model_pricing_extra_kilometers_cost = rec.vehicle_model_datail_id.extra_kilometers_cost
            rec.model_pricing_min_normal_day_price = rec.vehicle_model_datail_id.min_normal_day_price
            rec.model_pricing_min_weekly_day_price = rec.vehicle_model_datail_id.min_weekly_day_price
            rec.model_pricing_min_monthly_day_price = rec.vehicle_model_datail_id.min_monthly_day_price
            rec.model_pricing_max_normal_day_price = rec.vehicle_model_datail_id.max_normal_day_price
            rec.model_pricing_max_weekly_day_price = rec.vehicle_model_datail_id.max_weekly_day_price
            rec.model_pricing_max_monthly_day_price = rec.vehicle_model_datail_id.max_monthly_day_price
            rec.model_pricing_min_customer_age = rec.vehicle_model_datail_id.min_customer_age
            rec.model_pricing_max_customer_age = rec.vehicle_model_datail_id.max_customer_age
            rec.model_pricing_full_tank_cost = rec.vehicle_model_datail_id.full_tank_cost
            rec.model_pricing_start_date = rec.vehicle_model_datail_id.start_date
            rec.model_pricing_end_date = rec.vehicle_model_datail_id.end_date

    # Done
    def set_additional_supplementary_lines(self):
        available_lines = self.env['additional.supplementary.services'].search(
            [('contract_type', '=', 'long_term')])
        for rec in self:
            additional_supplement_service_line_ids = [(5, 0, 0)]
            for line in available_lines:
                vals = {
                    'name': line.name,
                    'type': line.type,
                    'calculation': line.calculation,
                    'price': line.price,
                    'account_id': line.account_id.id,
                }
                additional_supplement_service_line_ids.append((0, 0, vals))
            rec.additional_supplement_service_line_ids = additional_supplement_service_line_ids
        return True

    # Done
    def get_rental_configuration(self):
        all_config_allowed = self.env['rental.config.settings'].search(
            [('type', '=', 'long_term')])
        for rec in self:
            matched_record_config = all_config_allowed.filtered(
                lambda c: c.company_id == rec.company_id)
            # if not matched_record_config:
            #     raise ValidationError(
            #         _("Add Rental configuration for current company"))
            rec.rental_configuration_id = matched_record_config[0]

    # Done
    def assign_rental_configuration_fields(self):
        for rec in self:

            # Set Configuration Fields
            #   ----------> Rental Config Fields
            rec.trip_days_account_id = rec.rental_configuration_id.trip_days_account_id
            rec.trip_days_label = rec.rental_configuration_id.trip_days_label
            rec.extra_km_account_id = rec.rental_configuration_id.extra_km_account_id
            rec.extra_km_label = rec.rental_configuration_id.extra_km_label
            rec.tax_ids = [(6, 0, rec.rental_configuration_id.tax_ids.ids)]

    def assign_in_check_list_fields(self):
        for record in self:
            record.in_ac = record.out_ac
            record.in_radio_stereo = record.out_radio_stereo
            record.in_screen = record.out_screen
            record.in_spare_tire_tools = record.out_spare_tire_tools
            record.in_tires = record.out_tires
            record.in_spare_tires = record.out_spare_tires
            record.in_speedometer = record.out_speedometer
            record.in_keys = record.out_keys
            record.in_care_seats = record.out_care_seats
            record.in_oil_change_km = record.out_oil_change_km
            record.in_fuel_type_code = record.out_fuel_type_code
            record.in_keys_number = record.out_keys_number
            record.in_safety_triangle = record.out_safety_triangle
            record.in_fire_extinguisher = record.out_fire_extinguisher
            record.in_first_aid_kit = record.out_first_aid_kit
            record.in_oil_type = record.out_oil_type
            record.in_oil_change_date = record.out_oil_change_date
            record.in_vehicle_status = record.out_vehicle_status

    def apply_in_check_list_to_vehicle(self):
        for record in self:
            record.vehicle_id.ac = record.in_ac
            record.vehicle_id.radio_stereo = record.in_radio_stereo
            record.vehicle_id.screen = record.in_screen
            record.vehicle_id.spare_tire_tools = record.in_spare_tire_tools
            record.vehicle_id.tires = record.in_tires
            record.vehicle_id.spare_tires = record.in_spare_tires
            record.vehicle_id.speedometer = record.in_speedometer
            record.vehicle_id.keys = record.in_keys
            record.vehicle_id.care_seats = record.in_care_seats
            record.vehicle_id.oil_change_km = record.in_oil_change_km
            record.vehicle_id.fuel_type_code = record.in_fuel_type_code
            record.vehicle_id.keys_number = record.in_keys_number
            record.vehicle_id.safety_triangle = record.in_safety_triangle
            record.vehicle_id.fire_extinguisher = record.in_fire_extinguisher
            record.vehicle_id.first_aid_kit = record.in_first_aid_kit
            record.vehicle_id.oil_type = record.in_oil_type
            record.vehicle_id.oil_change_date = record.in_oil_change_date
            record.vehicle_id.vehicle_status = record.in_vehicle_status

    def next_draft_state(self):
        if self.draft_state == 'customer_info':
            self.draft_state = 'vehicle_info'
        elif self.draft_state == 'vehicle_info':
            self.assign_model_pricing_fields()
            self.check_vehicle_long_term_pricing()
            self.draft_state = 'contract_info'
        elif self.draft_state == 'contract_info':
            self.set_additional_supplementary_lines()
            self.draft_state = 'additional_suppl_service'
        elif self.draft_state == 'additional_suppl_service':
            self.assign_rental_configuration_fields()
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
        for rec in self:
            if rec.duration > 0 and not rec.contract_installment_ids:
                raise ValidationError(
                    _("Please Calculate Installments before open contract."))
            # elif rec.remaining_amount != sum(rec.contract_installment_ids.mapped('monthly_installment')):
            #     raise ValidationError(
            #         _("Please recalculate Installments to match remaining amount before open contract."))
            elif rec.advanced_payment-rec.advanced_paid_amount != 0:
                raise ValidationError(
                    _("Please Pay Advanced Payment before open contract."))

            rental_vehicle_state = self.env['fleet.vehicle.state'].search(
                [('type', '=', 'rented')], limit=1)
            if not rental_vehicle_state:
                raise ValidationError(
                    _("Please configure Rent state in vehicle states."))
            rec.vehicle_id.write({'state_id': rental_vehicle_state.id})
            rec.write({'state': 'opened'})

    # Done

    def action_close_info(self):
        drop_off_date = fields.Datetime.now()
        self.assign_in_check_list_fields()
        self.write({'state': 'close_info', 'drop_off_date': drop_off_date})

    def action_close(self):
        accident_obj = self.env['fleet.accident'].sudo()
        damage_obj = self.env['fleet.damage'].sudo()
        ready_to_rent_fleet_status = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'ready_to_rent')])

        for rec in self:
            if rec.vehicle_in_state == 'accident':
                accident_obj.create({
                    'accident_category': 'received_accident',
                    'fleet_vehicle_id': rec.vehicle_id.id,
                    'partner_id': rec.partner_id.id,
                    'rental_contract_id': rec.id,
                    'city_id': rec.city_id.id,
                    'report_source': rec.report_source,
                    'other_report_source': rec.other_report_source,
                    'announcement_date': rec.announcement_date,
                    'accident_date': rec.accident_date,
                })

            elif rec.vehicle_in_state == 'damage':
                damage_obj.create({
                    'vehicle_id': rec.vehicle_id.id,
                    'rental_contract_id': rec.id,
                    'customer_id': rec.partner_id.id,
                    'source': 'rental',
                    'id_no': rec.partner_id_no,
                })

            elif rec.vehicle_in_state == 'none':
                if rec.current_due_amount <= 0:
                    rec.state = 'closed'
                else:
                    rec.state = 'delivered_debit'

            if rec.vehicle_in_state in ['other', 'damage', 'accident']:
                rec.state = 'delivered_pending'

            if rec.vehicle_in_state in ['other', 'none']:
                if not ready_to_rent_fleet_status:
                    raise ValidationError(
                        _("Please Configure Ready To Rent Fleet status"))
                rec.vehicle_id.state_id = ready_to_rent_fleet_status[0].id

            rec.apply_in_check_list_to_vehicle()

    def action_final_close(self):
        for rec in self:

            # InDebit Status due amount check
            if rec.total_amount-rec.paid_amount > 0:
                raise ValidationError(
                    _("Due amount must be less than or equal to zero !"))

        self.write({'state': 'closed'})

    def action_cancel(self):
        if not all(payment.state == 'draft' for payment in self.account_payment_ids):
            raise UserError(
                _('You cannot cancel this contract because there are payments that are not in draft state.'))
        self.account_payment_ids.action_cancel()
        self.write({'state': 'cancelled'})

    def set_current_km_extra_amount(self):
        self.ensure_one()
        if self.out_odometer > self.in_odometer:
            raise ValidationError(_('KM In Must Be greater Than KM Out'))
        self.current_km_extra_amount = self.display_current_km_extra_amount
        return {'type': 'ir.actions.act_window_close'}

    def action_pay(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pay'),
            'res_model': 'long.term.rental.contract.payment.register',
            'view_mode': 'form',
            'view_id': self.env.ref('long_term_rental.view_long_term_rental_contract_payment_register_form').id,
            'context': {'default_contract_type': 'long_term', 'default_long_term_rental_contract_id': self.id},
            'target': 'new',
        }

    def calculate_installment(self):
        for rec in self:
            if rec.advanced_payment != rec.advanced_paid_amount:
                raise ValidationError(
                    _("Advance Payment must be paid before creating installments"))
            if rec.duration > 0 and rec.remaining_amount > 0:
                rec.contract_installment_ids.unlink()
                for i in range(1, rec.duration + 1):
                    rec.contract_installment_ids.create({
                        'long_term_contract_id': rec.id,
                        'name': i,
                        # installment_date
                        'installment_date': rec.contract_start_date + relativedelta(months=i - 1),
                        'monthly_installment': rec.monthly_installment
                    })

    def view_vehicle_model_pricing(self):
        self.ensure_one()
        if self.draft_state == 'vehicle_info' and self.vehicle_model_datail_id:
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
        else:
            view_id = self.env.ref(
                'rental_contract.view_rental_contract_model_pricing_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Vehicle Model Pricing'),
                'res_model': 'rental.contract',
                'target': 'new',
                'view_mode': 'form',
                'context': {'create': 0, 'edit': 0},
                'res_id': self.id,
                'views': [[view_id, 'form']]
            }

    def view_calculate_km(self):
        view_id = self.env.ref(
            'rental_contract.view_rental_contract_calculate_km_form').id
        if not self.in_odometer:
            self.in_odometer = self.out_odometer
        return {
            'type': 'ir.actions.act_window',
            'name': _('Calculate KM'),
            'res_model': 'rental.contract',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [[view_id, 'form']]
        }

    # Done
    def view_related_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('term_long_rental_contract_id', '=', self.id)]
        }

    def view_related_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': ['|', ('damage_id', 'in', self.damage_ids.ids), ('rental_contract_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('state', 'in', ('posted', 'draft'))]
        }

    def view_related_credit_note(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Note'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id), ('move_type', '=', 'out_refund')]
        }

    def view_contract_additional_supplement_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract Additional Supplementary Services'),
            'res_model': 'additional.supplementary.services.line',
            'view_mode': 'list',
            'domain': [('id', 'in', self.additional_supplement_service_line_ids.ids)]
        }

    def view_schedular_invoice_log(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rental Contract Schedular Invoice Log'),
            'res_model': 'rental.contract.schedular.invoice.log',
            'view_mode': 'list',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'default_rental_contract_id': self.id},
        }

    def view_related_accident(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Accident'),
            'res_model': 'fleet.accident',
            'view_mode': 'list, form',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'create': 0}
        }

    def view_related_damage(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Damage'),
            'res_model': 'fleet.damage',
            'view_mode': 'list,form',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'create': 0}
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_type') == 'long_term':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'long.term.rental.contract.seq')
        return super().create(vals_list)


class RentalContractFinesDiscountLine(models.Model):
    _inherit = 'rental.contract.fines.discount.line'

    long_term_rental_contract_id = fields.Many2one(
        'long.term.rental.contract', string='Rental Contract', required=True)


class ContractFinesDiscountConfigLines(models.Model):
    _inherit = 'additional.supplementary.services.line'

    long_term_rental_contract_id = fields.Many2one(
        'long.term.rental.contract', string='Contract', ondelete="cascade")


class ContractInstallmentLines(models.Model):
    _name = 'contract.installment.line'
    _description = 'Contract Installment Line'

    name = fields.Integer(string='#')
    installment_date = fields.Date()
    monthly_installment = fields.Float('Monthly installment')
    paid_amount = fields.Float('Paid Amount')
    remaining_amount = fields.Float(
        'Remaining Amount', compute='_compute_remaining_amount')
    payment_status = fields.Selection(
        [('paid', 'Paid'), ('not_paid', 'Not Paid'),], default='not_paid', compute='_compute_remaining_amount')
    due_status = fields.Selection(
        [('due', 'Due'), ('not_due', 'Not Due'),], defaul='not_due', compute='_compute_remaining_amount')
    long_term_contract_id = fields.Many2one('long.term.rental.contract')

    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.monthly_installment - rec.paid_amount
            if rec.remaining_amount == 0:
                rec.payment_status = 'paid'
            else:
                rec.payment_status = 'not_paid'
            if rec.installment_date < fields.Date.today():
                rec.due_status = 'due'
            else:
                rec.due_status = 'not_due'
