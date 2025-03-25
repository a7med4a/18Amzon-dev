# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


VEHICLE_STATUS = [
    ('excellent', 'Excellent'),
    ('good', 'Good'),
    ('simple_scratch', 'Simple Scratch'),
    ('deep_scratch', 'Deep Scratch'),
    ('very_deep_scratch', 'Very Deep Scratch'),
    ('bend_in_structure', 'Bend In Structure')
]
VEHICLE_PARTS_STATUS = [
    ('excellent', 'Excellent'),
    ('good', 'Good'),
    ('week', 'Week'),
    ('not_working', 'Not Working')
]
AVAILABILITY = [
    ('available', 'Available'),
    ('not_available', 'Not Available')
]
WORKING_CONDITION = [
    ('working', 'Working'),
    ('not_working', 'Not Working')
]
FUEL_TYPE_STATUS = [
    ('91', '91'),
    ('95', '95'),
    ('diesel', 'Diesel'),
    ('electric', 'Electric')
]
CAR_SEATS_STATUS = [('clean', 'Clean'), ('dirty', 'Dirty')]


class vehicle_info(models.Model):
    _inherit = 'fleet.vehicle'

    vin_sn = fields.Char(required=True)
    model_year = fields.Char(required=True)
    category_id = fields.Many2one(
        'fleet.vehicle.model.category', required=True)

    # Vehicle Information
    serial_number = fields.Char('Serial Number', required=True)
    card_number = fields.Char('Card Number', required=True)
    usage_type = fields.Selection(
        selection=[('rental', 'Rental'), ('limousine', 'Limousine')],
        string='Usage Type', required=True)
    license_type = fields.Selection(
        selection=[('special_transportation', 'Special Transportation'),
                   ('private', 'Private'),
                   ('public_transportation', 'Public Transportation')
                   ],
        string='License Type', required=True)
    branch_id = fields.Many2one(
        'res.branch', string='Location', required=True)

    # Chick List Information
    # Group 1
    ac = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Ac', required=True)
    radio_stereo = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Radio Stereo', required=True)
    screen = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Screen', required=True)
    spare_tire_tools = fields.Selection(
        selection=AVAILABILITY,
        string='Spare Tire Tools', required=True)
    tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Tires', required=True)
    spare_tires = fields.Selection(
        selection=VEHICLE_PARTS_STATUS,
        string='Spare Tires', required=True)

    # Group 2
    speedometer = fields.Selection(
        selection=WORKING_CONDITION,
        string='Speedometer', required=True)
    keys = fields.Selection(
        selection=WORKING_CONDITION,
        string='Keys', required=True)
    care_seats = fields.Selection(
        selection=CAR_SEATS_STATUS,
        string='Care Seats', required=True)
    oil_change_km = fields.Float('Oil Change KM Distance', required=True)
    fuel_type_code = fields.Selection(
        FUEL_TYPE_STATUS, string='Fuel Type Code', required=True)
    keys_number = fields.Integer('Number Of Keys', required=True)

    # Group 3
    safety_triangle = fields.Selection(
        selection=AVAILABILITY,
        string='Safety Triangle', required=True)
    fire_extinguisher = fields.Selection(
        selection=AVAILABILITY,
        string='Fire Extinguisher', required=True)
    first_aid_kit = fields.Selection(
        selection=AVAILABILITY,
        string='First Aid Kit', required=True)
    oil_type = fields.Char('Oil Type', required=True)
    oil_change_date = fields.Date('Oil Change Date', required=True)
    vehicle_status = fields.Selection(
        selection=VEHICLE_STATUS,
        string='Vehicle Status', required=True)

    vehicle_color = fields.Integer('Color')

    #  Analytic account
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', ondelete='cascade', copy=False, readonly=True)

    # Check Chassis Number and License Plate Lengt
    @api.constrains('vin_sn', 'license_plate')
    def _check_vin_sn_license_plate_length(self):
        for vehicle in self:
            if vehicle.vin_sn and len(vehicle.vin_sn) != self.env.company.vin_sn_length:
                raise ValidationError(
                    _('Chassis Number Length Must be %s Digits' % self.env.company.vin_sn_length))
            if vehicle.license_plate and len(vehicle.license_plate) != self.env.company.license_plate_length:
                raise ValidationError('License Plate Length Must be %s Digits' %
                                      self.env.company.license_plate_length)

    # Check Chassis Number and License Plate Unique
    @api.constrains('vin_sn', 'license_plate')
    def _check_vin_sn_license_plate_unique(self):
        for vehicle in self:
            if vehicle.vin_sn and self.search_count([('vin_sn', '=', vehicle.vin_sn), ('id', '!=', vehicle.id)]):
                raise ValidationError(_('Chassis Number Must be Unique'))
            if vehicle.license_plate and self.search_count([('license_plate', '=', vehicle.license_plate), ('id', '!=', vehicle.id)]):
                raise ValidationError(_('License Plate Must be Unique'))

    # Create Analytic Account
    @api.model_create_multi
    def create(self, vals_list):
        vehicles = super().create(vals_list)
        plan_id = self.env.ref('vehicle_info.vehicle_analytic_plan')
        for vehicle in vehicles:
            analytic_account_name = ''
            analytic_account_name += vehicle.license_plate if vehicle.license_plate else 'No Plate'
            analytic_account_name += ' / ' + \
                vehicle.vin_sn if vehicle.vin_sn else ' / No Chassis'
            analytic_account = self.env['account.analytic.account'].create({
                'name': analytic_account_name,
                'plan_id': plan_id.id,
            })
            vehicle.analytic_account_id = analytic_account.id

        return vehicles

    # modify Analytic account
    def write(self, vals):
        res = super().write(vals)
        if 'license_plate' in vals or 'vin_sn' in vals:
            for vehicle in self:
                analytic_account_name = ''
                analytic_account_name += vehicle.license_plate if vehicle.license_plate else 'No Plate'
                analytic_account_name += ' / ' + \
                    vehicle.vin_sn if vehicle.vin_sn else ' / No Chassis'
                vehicle.analytic_account_id.name = analytic_account_name
        return res
