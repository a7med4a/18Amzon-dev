import base64
import openpyxl
from io import BytesIO
from odoo.exceptions import ValidationError

import binascii
import xlrd
import tempfile
from odoo import models, fields, api, _

class InsurancePolicyTerminateWizard(models.TransientModel):
    _name = 'insurance.policy.terminate.wizard'

    line_ids = fields.One2many('insurance.policy.terminate.line', 'wizard_id', string="Termination Details")
    policy_id = fields.Many2one('insurance.policy', string="Policy", readonly=True)
    used_vehicle_ids = fields.Many2many('insurance.policy.line', string="Used Vehicle",compute='_compute_used_vehicle_ids',)

    @api.depends('line_ids.vehicle_id')
    def _compute_used_vehicle_ids(self):
        for vehicle in self:
            vehicle.used_vehicle_ids = vehicle.line_ids.mapped('vehicle_id').ids

    def action_confirm_termination(self):
        terminates=[]
        for line in self.line_ids:
            terminate_logs = self.env["termination.log"].search(
                [("vehicle_id", "=", line.vehicle_id.vehicle_id.id),
                 ("police_line_id", "=", line.vehicle_id.id),
                 ("police_id", "=", self.policy_id.id),])
            if terminate_logs :
                raise ValidationError(_(
                    f"Vehicle { line.vehicle_id.vehicle_id.name} is already terminated before!"
                ))
            termination_log_vals = {
                'vehicle_id': line.vehicle_id.vehicle_id.id,
                'police_line_id': line.vehicle_id.id,
                'police_id': self.policy_id.id,
                'stop_date': line.stop_date,
                'estimated_refunded_amount': ((line.vehicle_id.end_date - line.stop_date).days) * line.vehicle_id.daily_rate if line.vehicle_id.end_date and line.stop_date else 0,
                'actual_refunded_amount': (( line.vehicle_id.end_date - line.stop_date).days) * line.vehicle_id.daily_rate if line.vehicle_id.end_date and line.stop_date else 0,
            }
            terminates.append(termination_log_vals)
        for vals in terminates :
            self.env['termination.log'].create(vals)

class InsurancePolicyTerminateLine(models.TransientModel):
    _name = 'insurance.policy.terminate.line'
    _description = 'Termination Details'

    wizard_id = fields.Many2one('insurance.policy.terminate.wizard', string="Wizard")
    policy_id = fields.Many2one('insurance.policy', string="Policy", readonly=True)
    vehicle_id = fields.Many2one('insurance.policy.line')
    stop_date = fields.Date(string="Stop Date")


class ImportVehicle(models.TransientModel):
    _name = 'import.vehicle'
    _description = 'Import Vehicle'

    file = fields.Binary(string="File", required=True)
    file_name = fields.Char('File Name')
    policy_id = fields.Many2one('insurance.policy', string="Policy", required=True)

    def action_import(self):
        order = openpyxl.load_workbook(
            filename=BytesIO(base64.b64decode(self.file)))
        xl_order = order.active

        print("xl_order===>", xl_order)
        for record in xl_order.iter_rows(min_row=2, max_row=None,
                                         min_col=None,
                                         max_col=None,
                                         values_only=True):
            line = list(record)
            if line[1]:
                vehicle = self.env['fleet.vehicle'].search(
                    ['|','|',('name', '=', line[1]),('license_plate', '=', line[1]),('vin_sn', '=', line[1])], limit=1)
                if line[0] :
                    insurance_police_line = self.env['insurance.policy.line'].search(
                            [('id', '=', line[0])], limit=1)
                    if vehicle and insurance_police_line :
                        if insurance_police_line.bill_status == "true" :
                            raise ValidationError("Cannot update a True Bill status insurance policy line!")
                        insurance_police_line.write(self.prepare_insurance_line_vals(line,vehicle))
                    elif vehicle and not insurance_police_line :
                        self.env['insurance.policy.line'].create(self.prepare_insurance_line_vals(line,vehicle))
                else :
                    if not vehicle :
                        raise ValidationError("Chassis Number is not found ,Please add another one!")
                    new_policy_line=self.env['insurance.policy.line'].create(self.prepare_insurance_line_vals(line,vehicle))
                    if new_policy_line :
                        self.policy_id.show_create_bill=True
            else :
                raise ValidationError("Chassis Number is required ,Please add a vehicle to create policy line!")
                    
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'insurance.policy',
        #     'view_mode': 'form',
        #     'res_id': self.policy_id.id,
        # }

    def prepare_insurance_line_vals(self,line,vehicle):
        return {
            'vehicle_id': vehicle.id,
            'policy_id': self.policy_id.id,
            'purchase_market_value': line[2],
            'insurance_rate': line[3],
            'minimum_insurance_rate': line[4],
            'start_date': line[5],
            'endurance_rate': line[6],
            'endurance_customer': line[7],
        }
