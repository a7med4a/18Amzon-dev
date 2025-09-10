from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.vehicle_info.models.fleet_vehicle import VEHICLE_STATUS, VEHICLE_PARTS_STATUS, AVAILABILITY, \
    WORKING_CONDITION, FUEL_TYPE_STATUS, CAR_SEATS_STATUS


class LimousineContract(models.Model):
    _name = 'limousine.contract'
    _description = 'Limousine Contract'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Contract Number', copy=False, default='New', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, tracking=True,
                                 default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.companies.ids)])
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Opened'),
        ('closing_info', 'Closing Info'),
        ('delivered_indebit', 'Delivered Indebit'),
        ('close', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', tracking=True, copy=False)

    # Driver Info Fields
    partner_id = fields.Many2one('res.partner', string='Driver', required=True, tracking=True,
                                 domain=[('limousine_driver', '=', True), ('driver_state', 'in', ('free', 'warning'))])
    driver_type = fields.Selection(related='partner_id.driver_type', tracking=True, )
    mobile_no = fields.Char(string="Mobile Number", tracking=True, )
    id_no = fields.Char(string="ID Number", tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    # Vehicle Info Fields
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True,
                                 domain=lambda self: [('state_id.type', '=', 'ready_to_rent'),
                                                      ('usage_type', '=', 'limousine'),
                                                      ('company_id', '=', self.env.company.id)])
    license_plate = fields.Char(string="License Plate", tracking=True, )
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', tracking=True, )
    category_id = fields.Many2one('fleet.vehicle.model.category', string='Category', tracking=True, )
    odometer = fields.Float(string='Last Odometer', tracking=True, )
    vehicle_color = fields.Char('Vehicle Color', tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    # Check List Out Information
    # --------------------> Group 1
    out_ac = fields.Selection(selection=VEHICLE_PARTS_STATUS, string='Ac', tracking=True, )
    out_radio_stereo = fields.Selection(selection=VEHICLE_PARTS_STATUS, string='Radio Stereo', tracking=True, )
    out_screen = fields.Selection(selection=VEHICLE_PARTS_STATUS, string='Screen', tracking=True, )
    out_spare_tire_tools = fields.Selection(selection=AVAILABILITY, string='Spare Tire Tools', tracking=True, )
    out_tires = fields.Selection(selection=VEHICLE_PARTS_STATUS, string='Tires', tracking=True, )
    out_spare_tires = fields.Selection(selection=VEHICLE_PARTS_STATUS, string='Spare Tires', tracking=True, )

    # --------------------> Group 2
    out_speedometer = fields.Selection(selection=WORKING_CONDITION, string='Speedometer', tracking=True, )
    out_keys = fields.Selection(selection=WORKING_CONDITION, string='Keys', tracking=True, )
    out_care_seats = fields.Selection(selection=CAR_SEATS_STATUS, string='Care Seats', tracking=True, )
    out_oil_change_km = fields.Float('Oil Change KM Distance', tracking=True, )
    out_fuel_type_code = fields.Selection(FUEL_TYPE_STATUS, string='Fuel Type Code', tracking=True, )
    out_keys_number = fields.Integer('Number Of Keys', tracking=True, )

    # --------------------> Group 3
    out_safety_triangle = fields.Selection(selection=AVAILABILITY, string='Safety Triangle', tracking=True, )
    out_fire_extinguisher = fields.Selection(selection=AVAILABILITY, string='Fire Extinguisher', tracking=True, )
    out_first_aid_kit = fields.Selection(selection=AVAILABILITY, string='First Aid Kit', tracking=True, )
    out_oil_type = fields.Char('Oil Type', tracking=True, )
    out_oil_change_date = fields.Date('Oil Change Date', tracking=True, )
    out_vehicle_status = fields.Selection(selection=VEHICLE_STATUS, string='Vehicle Status', tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    out_attachment_1 = fields.Binary(attachment=True, string='Attachment 1')
    out_attachment_2 = fields.Binary(attachment=True, string='Attachment 2')
    out_attachment_3 = fields.Binary(attachment=True, string='Attachment 3')
    out_attachment_4 = fields.Binary(attachment=True, string='Attachment 4')
    out_attachment_5 = fields.Binary(attachment=True, string='Attachment 5')
    out_attachment_6 = fields.Binary(attachment=True, string='Attachment 6')
    out_attachment_7 = fields.Binary(attachment=True, string='Attachment 7')
    out_attachment_8 = fields.Binary(attachment=True, string='Attachment 8')

    # -----------------------------------------------------------------------------------------------------------------

    first_driver_signature = fields.Binary(string="Driver Signature", required=True, tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    # Contract Info Fields
    branch_id = fields.Many2one('res.branch', string='Pickup Branch', tracking=True, )
    start_date = fields.Datetime('Start Date', default=lambda self: fields.Datetime.now(), tracking=True, )
    drop_off_date = fields.Datetime('Drop Off Date', copy=False, tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    # Pricing Info
    pricing_line_id = fields.Many2one('limousine.pricing.line', string='Pricing Line', tracking=True,
                                      compute='_compute_pricing_details', store=True)
    pricing_id = fields.Many2one('limousine.pricing', string='Pricing', tracking=True,
                                 compute='_compute_pricing_details', store=True)

    # -----------------------------------------------------------------------------------------------------------------

    # Financial Info
    daily_rate = fields.Float(string='Daily Rate', compute='_compute_pricing_details', store=True, tracking=True, )
    is_friday_free = fields.Boolean(string='Friday Free', compute='_compute_pricing_details', store=True,
                                    tracking=True, )
    total_duration = fields.Float(compute='_compute_duration', store=True, tracking=True)
    free_duration = fields.Float(compute='_compute_duration', store=True, tracking=True)

    # -----------------------------------------------------------------------------------------------------------------

    # Check List IN Information
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
    in_oil_type = fields.Char('Oil Type')
    in_oil_change_date = fields.Date(
        'Oil Change Date')
    in_vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Vehicle Status')

    second_driver_signature = fields.Binary(string="Driver Signature", tracking=True, )

    # -----------------------------------------------------------------------------------------------------------------

    total_before_tax = fields.Monetary(compute='_compute_amount', currency_field='currency_id', tracking=True)
    tax_amount = fields.Monetary(compute='_compute_amount', currency_field='currency_id', tracking=True)
    total_after_tax = fields.Monetary(compute='_compute_amount', currency_field='currency_id', tracking=True)
    due_amount = fields.Monetary(compute='_compute_amount', currency_field='currency_id', tracking=True)
    paid_amount = fields.Monetary(compute='_compute_amount', currency_field='currency_id', tracking=True)

    # -----------------------------------------------------------------------------------------------------------------

    timesheet_ids = fields.One2many('limousine.contract.timesheet', 'contract_id', string='Timesheets')
    timesheet_count = fields.Integer(string='Timesheet Count', compute='_compute_timesheet_count')

    account_payment_ids = fields.One2many('account.payment', 'limousine_contract_id', string='Payments', copy=False)
    payment_count = fields.Integer('Payment Count', compute='_compute_payment_count')

    # -----------------------------------------------------------------------------------------------------------------

    def action_view_timesheets(self):
        """Action to view timesheets for this contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Timesheets'),
            'res_model': 'limousine.contract.timesheet',
            'view_mode': 'list',
            'domain': [('contract_id', '=', self.id)],
            'context': {
                'default_contract_id': self.id,
                'create': False,
            },
            'target': 'current',
        }

    def view_related_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('limousine_contract_id', '=', self.id)]
        }

    # -----------------------------------------------------------------------------------------------------------------

    @api.constrains('vehicle_id')
    def _check_vehicle_active_pricing(self):
        """Check that the selected vehicle has an active limousine pricing"""
        for contract in self:
            if contract.vehicle_id:

                # Check if there's an active pricing for this model
                active_pricing = self.env['limousine.pricing'].search([
                    ('model_id', '=', contract.vehicle_id.model_id.id),
                    ('state', '=', 'active'),
                    ('company_id', '=', contract.company_id.id)
                ], limit=1)

                if not active_pricing:
                    raise ValidationError(_(
                        "The selected vehicle model '%s' does not have an active pricing. "
                        "Please create an active pricing for this model before creating a contract."
                    ) % contract.vehicle_id.model_id.name)

    @api.constrains('start_date')
    def _check_start_date_not_future(self):
        """Constraint to ensure start date is not in the future"""
        for contract in self:
            if contract.start_date and contract.start_date > fields.Datetime.now():
                raise ValidationError(_('Start date cannot be in the future.'))

    @api.constrains('partner_id', 'vehicle_id', 'state')
    def _check_driver_vehicle_assignment(self):
        """Ensure driver and vehicle are only assigned to one active contract"""
        for contract in self:
            if contract.state in ('draft', 'open', 'closing_info'):
                # Check for other active contracts with same driver
                driver_contracts = self.search([
                    ('partner_id', '=', contract.partner_id.id),
                    ('state', 'in', ['draft', 'open', 'closing_info']),
                    ('id', '!=', contract.id)
                ], limit=1)

                if driver_contracts:
                    raise ValidationError(_(
                        "Driver %s is already assigned to active contract %s. "
                        "Please choose another driver or close the existing contract first."
                    ) % (contract.partner_id.name, driver_contracts[0].name))

                # Check for other active contracts with same vehicle
                vehicle_contracts = self.search([
                    ('vehicle_id', '=', contract.vehicle_id.id),
                    ('state', 'in', ['draft', 'open', 'closing_info']),
                    ('id', '!=', contract.id)
                ], limit=1)

                if vehicle_contracts:
                    raise ValidationError(_(
                        "Vehicle %s is already assigned to active contract %s. "
                        "Please choose another vehicle or close the existing contract first."
                    ) % (contract.vehicle_id.name, vehicle_contracts[0].name))

    # -----------------------------------------------------------------------------------------------------------------

    @api.depends('vehicle_id', 'vehicle_id.model_id', 'partner_id', 'partner_id.driver_type', 'company_id')
    def _compute_pricing_details(self):
        """Compute pricing details by first finding the pricing line and then deriving other fields from it"""
        for contract in self:
            if contract.vehicle_id and contract.driver_type:

                # Find the pricing line directly
                pricing_line = self.env['limousine.pricing.line'].search([
                    ('pricing_id.model_id', '=', contract.vehicle_id.model_id.id),
                    ('pricing_id.state', '=', 'active'),
                    ('pricing_id.company_id', '=', contract.company_id.id),
                    ('driver_type', '=', contract.driver_type)
                ], limit=1)

                if pricing_line:
                    contract.pricing_line_id = pricing_line.id
                    contract.pricing_id = pricing_line.pricing_id.id
                    contract.daily_rate = pricing_line.daily_rate
                    contract.is_friday_free = pricing_line.is_friday_free
                else:
                    # No pricing line found, set all fields to False/empty
                    contract.pricing_line_id = False
                    contract.pricing_id = False
                    contract.daily_rate = 0.0
                    contract.is_friday_free = False
            else:
                # Missing required fields, set all to False/empty
                contract.pricing_line_id = False
                contract.pricing_id = False
                contract.daily_rate = 0.0
                contract.is_friday_free = False

    @api.depends('timesheet_ids')
    def _compute_timesheet_count(self):
        for contract in self:
            contract.timesheet_count = len(contract.timesheet_ids)

    @api.depends('timesheet_ids')
    def _compute_duration(self):
        for contract in self:
            contract.total_duration = len(contract.timesheet_ids)
            contract.free_duration = len(contract.timesheet_ids.filtered(lambda l: l.time_spent == 0))

    @api.depends('timesheet_ids')
    def _compute_amount(self):
        for contract in self:
            contract.total_before_tax = sum(contract.timesheet_ids.mapped('daily_rate')) / 1.15
            contract.tax_amount = contract.total_before_tax * 15 / 100
            contract.total_after_tax = contract.total_before_tax + contract.tax_amount
            contract.paid_amount = sum(contract.account_payment_ids.filtered(lambda p: p.state == 'paid').mapped('amount'))
            contract.due_amount = contract.total_after_tax - contract.paid_amount

    @api.depends('account_payment_ids')
    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.account_payment_ids)

    # -----------------------------------------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        for contract in contracts:
            contract.name = self.env['ir.sequence'].next_by_code('limousine.contract')
        return contracts

    # -----------------------------------------------------------------------------------------------------------------

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            return

        self.mobile_no = self.partner_id.mobile2
        self.id_no = self.partner_id.id_no

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if not self.vehicle_id:
            return

        self.license_plate = self.vehicle_id.license_plate
        self.model_id = self.vehicle_id.model_id
        self.category_id = self.vehicle_id.category_id
        self.odometer = self.vehicle_id.odometer
        self.vehicle_color = self.vehicle_id.vehicle_color

        self.out_ac = self.vehicle_id.ac
        self.out_radio_stereo = self.vehicle_id.radio_stereo
        self.out_screen = self.vehicle_id.screen
        self.out_spare_tire_tools = self.vehicle_id.spare_tire_tools
        self.out_tires = self.vehicle_id.tires
        self.out_spare_tires = self.vehicle_id.spare_tires
        self.out_speedometer = self.vehicle_id.speedometer
        self.out_keys = self.vehicle_id.keys
        self.out_care_seats = self.vehicle_id.care_seats
        self.out_oil_change_km = self.vehicle_id.oil_change_km
        self.out_fuel_type_code = self.vehicle_id.fuel_type_code
        self.out_keys_number = self.vehicle_id.keys_number
        self.out_safety_triangle = self.vehicle_id.safety_triangle
        self.out_fire_extinguisher = self.vehicle_id.fire_extinguisher
        self.out_first_aid_kit = self.vehicle_id.first_aid_kit
        self.out_oil_type = self.vehicle_id.oil_type
        self.out_oil_change_date = self.vehicle_id.oil_change_date
        self.out_vehicle_status = self.vehicle_id.vehicle_status

        self.branch_id = self.vehicle_id.branch_id

    @api.onchange('start_date')
    def _onchange_start_date(self):
        """Validate that start date is not in the future"""
        if not self.start_date:
            return

        if self.start_date > fields.Datetime.now():
            return {
                'warning': {
                    'title': _('Invalid Date'),
                    'message': _('Start date cannot be in the future. Please select a current or past date.')
                }
            }

    # -----------------------------------------------------------------------------------------------------------------

    def action_draft(self):
        """Set state to Draft"""
        rental_vehicle_state = self.env['fleet.vehicle.state'].search([('type', '=', 'ready_to_rent')], limit=1)
        if not rental_vehicle_state:
            raise ValidationError(_("Please configure Ready To Rent state in vehicle states."))
        self.vehicle_id.write({'state_id': rental_vehicle_state.id})
        self.partner_id.write({'driver_state': 'free'})
        self.write({'state': 'draft'})

    def action_open(self):
        """Set state to Open"""
        rental_vehicle_state = self.env['fleet.vehicle.state'].search([('type', '=', 'rented')], limit=1)
        if not rental_vehicle_state:
            raise ValidationError(_("Please configure Rent state in vehicle states."))
        self.vehicle_id.write({'state_id': rental_vehicle_state.id})
        self.partner_id.write({'driver_state': 'busy'})
        self.write({'state': 'open'})

    def action_cancel(self):
        """Set state to Cancelled"""
        self.write({
            'state': 'cancelled',
        })

    def action_pay(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pay'),
            'res_model': 'limousine.contract.payment.register',
            'view_mode': 'form',
            'context': {'default_contract_id': self.id},
            'target': 'new',
        }

    def action_return(self):
        pass

    def action_add_fines(self):
        pass

    def action_add_accident(self):
        pass

    def action_add_damage(self):
        pass

    def action_refund(self):
        pass

    # -----------------------------------------------------------------------------------------------------------------

    def _auto_create_daily_timesheets(self):
        """Scheduled action to create daily timesheets for open contracts"""
        # Get all open contracts
        open_contracts = self.search([('state', '=', 'open')])

        for contract in open_contracts:
            if not contract.start_date:
                continue  # Skip contracts without start date

            # Convert datetime to user's timezone context for accurate date comparison
            start_datetime_utc = contract.start_date
            start_datetime_user_tz = fields.Datetime.context_timestamp(contract.with_context(tz='Asia/Riyadh'),
                                                                       start_datetime_utc)
            start_date = start_datetime_user_tz.date()

            # Create timesheets for all days from start_date to today
            current_date = start_date
            while current_date <= fields.Date.context_today(self):
                # Check if timesheet already exists for this date
                existing_timesheet = self.env['limousine.contract.timesheet'].search(
                    [('date', '=', current_date), ('contract_id', '=', contract.id)], limit=1)

                if not existing_timesheet:
                    # Calculate time spent based on whether it's the first day or not
                    if not contract.timesheet_ids:
                        # First day - use shift-based calculation with actual datetime in user's timezone
                        time_spent = self._calculate_first_day_time(contract, start_datetime_user_tz)
                    else:
                        # Regular day - check if it's Friday
                        time_spent = self._calculate_regular_day_time(contract, current_date)

                    self.env['limousine.contract.timesheet'].create({
                        'date': current_date,
                        'contract_id': contract.id,
                        'company_id': contract.company_id.id,
                        'time_spent': time_spent,
                        'time_spent_char': f"{time_spent} Day",
                        'daily_rate': contract.daily_rate * time_spent,
                        'description': ''
                    })

                # Move to next day
                current_date = current_date + timedelta(days=1)

    def _is_friday_free_day(self, contract, date):
        is_friday = date.weekday() == 4  # Monday=0, Friday=4
        return is_friday and contract.is_friday_free

    def _calculate_first_day_time(self, contract, start_datetime_user_tz):
        """Calculate time spent for the first day based on contract start datetime in user's timezone"""
        # Check if start date is Friday and free
        if self._is_friday_free_day(contract, start_datetime_user_tz.date()):
            return 0.0

        # Get company shift configurations
        company = contract.company_id
        shifts = {
            'full_day': {'from': company.limousine_full_day_from, 'to': company.limousine_full_day_to},
            'half_day': {'from': company.limousine_half_day_from, 'to': company.limousine_half_day_to},
            'free_day': {'from': company.limousine_free_day_from, 'to': company.limousine_free_day_to},
        }

        # Convert start datetime to float time (hours.decimal) in user's timezone
        start_time_float = start_datetime_user_tz.hour + (start_datetime_user_tz.minute / 60.0)

        # Determine which shift the start time falls into
        if shifts['full_day']['from'] <= start_time_float < shifts['full_day']['to']:
            return 1.0
        elif shifts['half_day']['from'] <= start_time_float < shifts['half_day']['to']:
            return 0.5
        elif shifts['free_day']['from'] <= start_time_float < shifts['free_day']['to']:
            return 0.0
        else:
            return 0.0

    def _calculate_regular_day_time(self, contract, date):
        """Calculate time spent for a regular day (not first day)"""
        # Check if it's Friday and contract has Friday free
        if self._is_friday_free_day(contract, date):
            return 0.0
        return 1.0

    # -----------------------------------------------------------------------------------------------------------------
