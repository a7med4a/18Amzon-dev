# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VehicleRoute(models.Model):
    _inherit = 'vehicle.route'


    maintenance_external_job_order_id = fields.Many2one('maintenance.external.job.order', string='External Job order', ondelete="cascade")
    is_external_job_order=fields.Boolean(default=False)

    def action_external_job_order_approve(self):
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

    def action_external_exit_done(self):
        self.write({
            'state': 'exit_done',
            'exit_checklist_status': 'in_transfer',
            'exist_in_transfer_date': fields.Datetime.now()
        })
        self.action_branch_exit_done()

    def action_external_entry_done(self):
        self._check_odometer_validity()
        self.write({
            'state': 'entry_done',
            'entry_checklist_status': 'done',
            'entry_done_date': fields.Datetime.now()
        })
        self.action_branch_entry_done()
