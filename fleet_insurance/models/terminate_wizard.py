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
    type = fields.Selection(string='Type',selection=[('refunded', 'Refunded'), ('cancel', 'Cancellation'), ], required=True)



    @api.depends('line_ids.vehicle_id')
    def _compute_used_vehicle_ids(self):
        for vehicle in self:
            vehicle.used_vehicle_ids = vehicle.line_ids.mapped('vehicle_id').ids

    def action_confirm_termination(self):
        terminates=[]
        for rec in self:
            if not rec.line_ids :
                raise ValidationError(_("Please add add at least one line To terminate!"))
            for line in rec.line_ids:
                terminate_logs = self.env["termination.log"].search(
                    [("vehicle_id", "=", line.vehicle_id.vehicle_id.id),
                     ("police_line_id", "=", line.vehicle_id.id),
                     ("police_id", "=", self.policy_id.id),])
                if terminate_logs :
                    raise ValidationError(_(
                        f"Vehicle { line.vehicle_id.vehicle_id.name} is already terminated before!"
                    ))
                if rec.type == 'refunded':
                    estimated_refunded_amount=(line.vehicle_id.end_date - line.stop_date).days * line.vehicle_id.daily_rate if line.vehicle_id.end_date and line.stop_date else 0
                    termination_log_vals = {
                        'vehicle_id': line.vehicle_id.vehicle_id.id,
                        'police_line_id': line.vehicle_id.id,
                        'police_id': self.policy_id.id,
                        'stop_date': line.stop_date,
                        'type': 'refunded',
                        'estimated_refunded_amount': estimated_refunded_amount,
                        'actual_refunded_amount':  estimated_refunded_amount
                    }
                    terminates.append(termination_log_vals)
                elif rec.type == 'cancel':
                    cancel_configuration=rec.policy_id.cancel_insurance_policy_ids.filtered(lambda l: l.from_month<=line.number_of_months and l.to_month >=line.number_of_months)
                    if not cancel_configuration:
                        raise ValidationError(_(f"No Cancel configuration found for Vehicle {line.vehicle_id.vehicle_id.name}!"))
                    estimated_refunded_amount = (cancel_configuration[0].percentage/100) * line.vehicle_id.endurance_rate
                    termination_log_vals = {
                        'vehicle_id': line.vehicle_id.vehicle_id.id,
                        'police_line_id': line.vehicle_id.id,
                        'police_id': self.policy_id.id,
                        'stop_date': line.stop_date,
                        'type': 'cancel',
                        'estimated_refunded_amount': estimated_refunded_amount,
                        'actual_refunded_amount':estimated_refunded_amount,
                        'to_month':cancel_configuration[0].to_month,
                        'from_month':cancel_configuration[0].from_month,
                        'percentage':cancel_configuration[0].percentage,
                    }
                    terminates.append(termination_log_vals)
            for vals in terminates:
                self.env['termination.log'].create(vals)


class InsurancePolicyTerminateLine(models.TransientModel):
    _name = 'insurance.policy.terminate.line'
    _description = 'Termination Details'

    wizard_id = fields.Many2one('insurance.policy.terminate.wizard', string="Wizard")
    policy_id = fields.Many2one('insurance.policy', string="Policy", readonly=True)
    vehicle_id = fields.Many2one('insurance.policy.line')
    start_date = fields.Date(string="Start Date", related='vehicle_id.start_date')
    stop_date = fields.Date(string="Stop Date")
    number_of_months = fields.Integer(string="Number of Months",compute='_compute_number_of_months',store=True)

    @api.depends('start_date','stop_date')
    def _compute_number_of_months(self):
        for rec in self:
            if rec.start_date and rec.stop_date :
                rec.number_of_months = (rec.stop_date.year - rec.start_date.year) * 12 + (rec.stop_date.month - rec.start_date.month)
            else:
                rec.number_of_months = 0


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
            vin_sn=str(line[1])
            if line[1]:
                vehicle = self.env['fleet.vehicle'].search(
                    ['|','|',('name', '=', line[1]),('license_plate', '=', line[1]),('vin_sn', 'ilike', vin_sn)], limit=1)
                if line[0] :
                    insurance_police_line = self.env['insurance.policy.line'].search([('id', '=', line[0])], limit=1)
                    print("insurance_police_line", insurance_police_line)
                    if vehicle and insurance_police_line :
                        if insurance_police_line.bill_status == "true" :
                            raise ValidationError("Cannot update a True Bill status insurance policy line!")
                        insurance_police_line.write(self.prepare_insurance_line_vals(line,vin_sn))

                    elif vehicle and not insurance_police_line :
                        self.env['insurance.policy.line'].create(self.prepare_insurance_line_vals(line,vin_sn))
                else :
                    if not vehicle :
                        raise ValidationError("Chassis Number is not found ,Please add another one!")
                    new_policy_line=self.env['insurance.policy.line'].create(self.prepare_insurance_line_vals(line,vin_sn))
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

    def prepare_insurance_line_vals(self,line,vin_sn):
        return {
            'vin_sn': vin_sn,
            'policy_id': self.policy_id.id,
            'purchase_market_value': line[2],
            'insurance_rate': line[3],
            'minimum_insurance_rate': line[4],
            'start_date': line[5],
            'endurance_rate': line[6],
            'endurance_customer': line[7],
        }
