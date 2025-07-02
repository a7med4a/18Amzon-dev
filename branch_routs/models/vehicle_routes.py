# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.addons.vehicle_info.models.fleet_vehicle import VEHICLE_STATUS, VEHICLE_PARTS_STATUS, AVAILABILITY, WORKING_CONDITION, FUEL_TYPE_STATUS, CAR_SEATS_STATUS


class VehicleRouts(models.Model):
    _name = 'vehicle.route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle Routes'
    _rec_name = 'fleet_vehicle_id'

    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', required=True)
    branch_route_id = fields.Many2one(
        'branch.route', string='Branch Route', ondelete="cascade")
    maintenance_external_job_order_id = fields.Many2one('maintenance.external.job.order', string='External Job order')
    destination_type = fields.Selection(
        related='branch_route_id.destination_type', store=True)
    source_branch_id = fields.Many2one(
        'res.branch', string='Source',
        related='branch_route_id.source_branch_id', store=True)
    destination_branch_id = fields.Many2one(
        'res.branch', string='Destination',
        related='branch_route_id.destination_branch_id', store=True)
    transfer_type = fields.Selection(
        related='branch_route_id.transfer_type', string='Transfer Type', store=True)
    is_new_vehicle = fields.Boolean(
        related='branch_route_id.is_new_vehicle', string='New Vehicle', store=True)
    exit_checklist_status = fields.Selection([
        ('under_check', 'Under Check'),
        ('in_transfer', 'Exit Check Done'),
    ], string='Exist CheckList Status', tracking=True)
    entry_checklist_status = fields.Selection([
        ('in_transfer', 'In Transfer'),
        ('done', 'Entry Check Done'),
    ], string='Entry CheckList Status', tracking=True)
    exist_under_check_date = fields.Datetime(
        'Exist Under Check Date', tracking=True)
    exist_in_transfer_date = fields.Datetime(
        'Exist InTransfer Date', tracking=True)
    entry_in_transfer_date = fields.Datetime(
        'Entry InTransfer Date', tracking=True)
    entry_done_date = fields.Datetime('Entry Done Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('exit_check', 'Exit Check'),
        ('exit_done', 'Exit Done'),
        ('entry_check', 'Entry Check'),
        ('entry_done', 'Entry Done'),
        ('cancel', 'Cancelled')
    ], string='State', default='draft')
    fleet_domain = fields.Binary(
        string="Fleet domain", help="Dynamic domain used for the Vehicle", compute="_compute_fleet_domain")

    # Exist Chick List Information
    exit_odometer = fields.Float('Exit Odometer')
    exit_ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Exist Ac', tracking=True)
    exit_radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Exist Radio Stereo', tracking=True)
    exit_screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Exist Screen', tracking=True)
    exit_spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Exist Spare Tire Tools', tracking=True)
    exit_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Exist Tires', tracking=True)
    exit_spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Exist Spare Tires', tracking=True)
    exit_speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Exist Speedometer', tracking=True)
    exit_keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Exist Keys', tracking=True)
    exit_care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Exist Care Seats', tracking=True)
    exit_oil_change_km = fields.Float(
        'Exist Oil Change KM Distance', tracking=True)
    exit_fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Exist Fuel Type Code', tracking=True)
    exit_keys_number = fields.Integer('Exist Number Of Keys', tracking=True)
    exit_safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Exist Safety Triangle', tracking=True)
    exit_fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Exist Fire Extinguisher', tracking=True)
    exit_first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='Exist First Aid Kit', tracking=True)
    exit_oil_type = fields.Char('Exist Oil Type', tracking=True)
    exit_oil_change_date = fields.Date('Exist Oil Change Date', tracking=True)
    exit_vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Exist Vehicle Status', tracking=True)

    # Entry Chick List Information
    entry_odometer = fields.Float('Entry Odometer', tracking=True)
    entry_ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Entry Ac', tracking=True)
    entry_radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Entry Radio Stereo', tracking=True)
    entry_screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Entry Screen', tracking=True)
    entry_spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Entry Spare Tire Tools', tracking=True)
    entry_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Entry Tires', tracking=True)
    entry_spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Entry Spare Tires', tracking=True)
    entry_speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Entry Speedometer', tracking=True)
    entry_keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Entry Keys', tracking=True)
    entry_care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Entry Care Seats', tracking=True)
    entry_oil_change_km = fields.Float(
        'Entry Oil Change KM Distance', tracking=True)
    entry_fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Entry Fuel Type Code', tracking=True)
    entry_keys_number = fields.Integer('Entry Number Of Keys', tracking=True)
    entry_safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Entry Safety Triangle', tracking=True)
    entry_fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Entry Fire Extinguisher', tracking=True)
    entry_first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='Entry First Aid Kit', tracking=True)
    entry_oil_type = fields.Char('Entry Oil Type', tracking=True)
    entry_oil_change_date = fields.Date('Entry Oil Change Date', tracking=True)
    entry_vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Entry Vehicle Status', tracking=True)
    side_1 = fields.Binary(string="Side 1", readonly=False)
    side_2 = fields.Binary(string="Side 2", readonly=False)
    side_3 = fields.Binary(string="Side 3", readonly=False)
    side_4 = fields.Binary(string="Side 4", readonly=False)
    side_5 = fields.Binary(string="Side 5", readonly=False)
    side_6 = fields.Binary(string="Side 6", readonly=False)

    @api.depends('is_new_vehicle')
    def _compute_fleet_domain(self):
        running_vehicle_ids = self.env['vehicle.route'].search(
            [('branch_route_id.state', 'not in', ['entry_done', 'cancel'])]).mapped('fleet_vehicle_id')
        running_vehicle_ids |= self.branch_route_id.vehicle_route_ids.fleet_vehicle_id
        for route in self:
            if route.branch_route_id.is_new_vehicle:
                domain = [('state_id.type', '=', 'under_preparation'),
                          ('id', 'not in', running_vehicle_ids.ids)]
            else:
                domain = [('state_id.allow_transfer', '=', True),
                          ('branch_id', '=', route.source_branch_id.id), ('id', 'not in', running_vehicle_ids.ids)]

            route.fleet_domain = domain

    def _check_odometer_validity(self):
        for rec in self:
            if rec.exit_odometer >= rec.entry_odometer and not rec.is_new_vehicle:
                raise ValidationError(
                    _(f"Odometer must be greater than {rec.exit_odometer}"))

    @api.constrains('fleet_vehicle_id')
    def _check_exist_vehicle_route(self):
        for rec in self:
            exist_running_vehicle_route = self.sudo().search([('branch_route_id.state', 'not in', [
                'entry_done', 'cancel']), ('id', '!=', rec.id), ('fleet_vehicle_id', '=', rec.fleet_vehicle_id.id)], limit=1)
            if exist_running_vehicle_route and not rec.is_external_job_order:
                raise ValidationError(
                    _(f"Vehicle {rec.fleet_vehicle_id.display_name} exist in branch route {exist_running_vehicle_route.branch_route_id.name} which is in {exist_running_vehicle_route.branch_route_id.state} state"))

    # Exit Functions

    def action_branch_approve(self):
        for rec in self:
            if not rec.is_new_vehicle:
                rec.with_context(tracking_disable=True).write({
                    'exit_odometer': rec.fleet_vehicle_id.odometer,
                    'exit_ac': rec.fleet_vehicle_id.ac,
                    'exit_radio_stereo': rec.fleet_vehicle_id.radio_stereo,
                    'exit_screen': rec.fleet_vehicle_id.screen,
                    'exit_spare_tire_tools': rec.fleet_vehicle_id.spare_tire_tools,
                    'exit_tires': rec.fleet_vehicle_id.tires,
                    'exit_spare_tires': rec.fleet_vehicle_id.spare_tires,
                    'exit_speedometer': rec.fleet_vehicle_id.speedometer,
                    'exit_keys': rec.fleet_vehicle_id.keys,
                    'exit_care_seats': rec.fleet_vehicle_id.care_seats,
                    'exit_oil_change_km': rec.fleet_vehicle_id.oil_change_km,
                    'exit_fuel_type_code': rec.fleet_vehicle_id.fuel_type_code,
                    'exit_keys_number': rec.fleet_vehicle_id.keys_number,
                    'exit_safety_triangle': rec.fleet_vehicle_id.safety_triangle,
                    'exit_fire_extinguisher': rec.fleet_vehicle_id.fire_extinguisher,
                    'exit_first_aid_kit': rec.fleet_vehicle_id.first_aid_kit,
                    'exit_oil_type': rec.fleet_vehicle_id.oil_type,
                    'exit_oil_change_date': rec.fleet_vehicle_id.oil_change_date,
                    'exit_vehicle_status': rec.fleet_vehicle_id.vehicle_status,
                    'exit_checklist_status': 'under_check',
                    'state': 'exit_check',
                    'exist_under_check_date': fields.Datetime.now()
                })
            else:
                rec.with_context(tracking_disable=True).write({
                    'entry_odometer': rec.fleet_vehicle_id.odometer,
                    'entry_ac': rec.fleet_vehicle_id.ac,
                    'entry_radio_stereo': rec.fleet_vehicle_id.radio_stereo,
                    'entry_screen': rec.fleet_vehicle_id.screen,
                    'entry_spare_tire_tools': rec.fleet_vehicle_id.spare_tire_tools,
                    'entry_tires': rec.fleet_vehicle_id.tires,
                    'entry_spare_tires': rec.fleet_vehicle_id.spare_tires,
                    'entry_speedometer': rec.fleet_vehicle_id.speedometer,
                    'entry_keys': rec.fleet_vehicle_id.keys,
                    'entry_care_seats': rec.fleet_vehicle_id.care_seats,
                    'entry_oil_change_km': rec.fleet_vehicle_id.oil_change_km,
                    'entry_fuel_type_code': rec.fleet_vehicle_id.fuel_type_code,
                    'entry_keys_number': rec.fleet_vehicle_id.keys_number,
                    'entry_safety_triangle': rec.fleet_vehicle_id.safety_triangle,
                    'entry_fire_extinguisher': rec.fleet_vehicle_id.fire_extinguisher,
                    'entry_first_aid_kit': rec.fleet_vehicle_id.first_aid_kit,
                    'entry_oil_type': rec.fleet_vehicle_id.oil_type,
                    'entry_oil_change_date': rec.fleet_vehicle_id.oil_change_date,
                    'entry_vehicle_status': rec.fleet_vehicle_id.vehicle_status,
                    'entry_checklist_status': 'in_transfer',
                    'state': 'entry_check',
                    'entry_in_transfer_date': fields.Datetime.now()
                })


    def action_exit_done(self):
        self.write({
            'state': 'exit_done',
            'exit_checklist_status': 'in_transfer',
            'exist_in_transfer_date': fields.Datetime.now()
        })
        self.branch_route_id.action_exit_done()


    def action_branch_exit_done(self):
        in_transfer_fleet_status = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'in_transfer')])
        for rec in self:
            rec.with_context(tracking_disable=True).write({
                'entry_ac': rec.exit_ac,
                'entry_radio_stereo': rec.exit_radio_stereo,
                'entry_screen': rec.exit_screen,
                'entry_spare_tire_tools': rec.exit_spare_tire_tools,
                'entry_tires': rec.exit_tires,
                'entry_spare_tires': rec.exit_spare_tires,
                'entry_speedometer': rec.exit_speedometer,
                'entry_keys': rec.exit_keys,
                'entry_care_seats': rec.exit_care_seats,
                'entry_oil_change_km': rec.exit_oil_change_km,
                'entry_fuel_type_code': rec.exit_fuel_type_code,
                'entry_keys_number': rec.exit_keys_number,
                'entry_safety_triangle': rec.exit_safety_triangle,
                'entry_fire_extinguisher': rec.exit_fire_extinguisher,
                'entry_first_aid_kit': rec.exit_first_aid_kit,
                'entry_oil_type': rec.exit_oil_type,
                'entry_oil_change_date': rec.exit_oil_change_date,
                'entry_vehicle_status': rec.exit_vehicle_status,
                'entry_checklist_status': 'in_transfer',
                'state': 'entry_check',
                'entry_in_transfer_date': fields.Datetime.now()
            })
            rec.fleet_vehicle_id.write({
                'ac': rec.exit_ac,
                'radio_stereo': rec.exit_radio_stereo,
                'screen': rec.exit_screen,
                'spare_tire_tools': rec.exit_spare_tire_tools,
                'tires': rec.exit_tires,
                'spare_tires': rec.exit_spare_tires,
                'speedometer': rec.exit_speedometer,
                'keys': rec.exit_keys,
                'care_seats': rec.exit_care_seats,
                'oil_change_km': rec.exit_oil_change_km,
                'fuel_type_code': rec.exit_fuel_type_code,
                'keys_number': rec.exit_keys_number,
                'safety_triangle': rec.exit_safety_triangle,
                'fire_extinguisher': rec.exit_fire_extinguisher,
                'first_aid_kit': rec.exit_first_aid_kit,
                'oil_type': rec.exit_oil_type,
                'oil_change_date': rec.exit_oil_change_date,
                'vehicle_status': rec.exit_vehicle_status,
                'state_id': in_transfer_fleet_status.id
            })
    # Entry Functions


    def action_entry_done(self):
        self._check_odometer_validity()
        self.write({
            'state': 'entry_done',
            'entry_checklist_status': 'done',
            'entry_done_date': fields.Datetime.now()
        })
        self.branch_route_id.action_entry_done()

    def action_branch_entry_done(self):

        ready_to_rent_fleet_status = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'ready_to_rent')])
        # under_maintenance_fleet_status = self.env['fleet.vehicle.state'].search(
        #     [('type', '=', 'under_maintenance')])
        waiting_maintenance_fleet_status = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'waiting_maintenance')])
        in_service_fleet_status = self.env['fleet.vehicle.state'].search(
            [('type', '=', 'in_service')])
        for rec in self:
            fleet_status = self.env['fleet.vehicle.state']
            if rec.branch_route_id.destination_type == 'branch' or (rec.branch_route_id.is_new_vehicle and rec.destination_branch_id.branch_type in ['rental', 'limousine']):
                fleet_status = ready_to_rent_fleet_status
            elif rec.branch_route_id.destination_type == 'workshop' or (rec.branch_route_id.is_new_vehicle and rec.destination_branch_id.branch_type == 'workshop'):
                # fleet_status = under_maintenance_fleet_status
                fleet_status = waiting_maintenance_fleet_status
            elif rec.branch_route_id.is_new_vehicle and rec.destination_branch_id.branch_type == 'administration':
                fleet_status = in_service_fleet_status

            rec.fleet_vehicle_id.write({
                'ac': rec.entry_ac,
                'radio_stereo': rec.entry_radio_stereo,
                'screen': rec.entry_screen,
                'spare_tire_tools': rec.entry_spare_tire_tools,
                'tires': rec.entry_tires,
                'spare_tires': rec.entry_spare_tires,
                'speedometer': rec.entry_speedometer,
                'keys': rec.entry_keys,
                'care_seats': rec.entry_care_seats,
                'oil_change_km': rec.entry_oil_change_km,
                'fuel_type_code': rec.entry_fuel_type_code,
                'keys_number': rec.entry_keys_number,
                'safety_triangle': rec.entry_safety_triangle,
                'fire_extinguisher': rec.entry_fire_extinguisher,
                'first_aid_kit': rec.entry_first_aid_kit,
                'oil_type': rec.entry_oil_type,
                'oil_change_date': rec.entry_oil_change_date,
                'vehicle_status': rec.entry_vehicle_status,
                'state_id': fleet_status.id if fleet_status else False,
                'branch_id': rec.branch_route_id.destination_branch_id.id
            })

    def action_branch_button_cancel(self):
        self.write({
            'entry_checklist_status': False,
            'exit_checklist_status': False,
            'state': 'cancel'
        })

    def action_branch_button_draft(self):
        self.write({
            'entry_checklist_status': False,
            'exit_checklist_status': False,
            'state': 'draft'
        })
