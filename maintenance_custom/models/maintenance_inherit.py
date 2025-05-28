# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import  timedelta

DAYS_reverse = {'Monday': '0',
                'Tuesday': '1',
                'Wednesday': '2',
                'Thursday': '3',
                'Friday': '4',
                'Saturday': '5',
                'Sunday': '6'}


class MaintenanceRequestInherit(models.Model):
    _inherit = 'maintenance.request'

    name = fields.Char('Repair Description Number',readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        default=lambda self: self.env.company)
    maintenance_type = fields.Selection([('preventive', 'Preventive'), ('damage', 'Damage'), ('accident', 'Accident')], string='Maintenance Type', default="preventive")
    damage_number = fields.Integer(string='Damage Number')
    accident_number = fields.Integer(string='Accident Number')
    stage_type = fields.Selection(related='stage_id.stage_type', string='Stage Type', readonly=True)
    worksheet_template_id = fields.Many2one(
        'worksheet.template', string="Worksheet Template",invisible=True,
        domain="[('res_model', '=', 'maintenance.request'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Create templates for each type of request you have and customize their content with your own custom fields.")
    request_description = fields.Text('Request Description')
    vehicle_id=fields.Many2one('fleet.vehicle',string='Vehicle',required=True,domain=lambda self: [('company_id', '=', self.env.company.id),('branch_id.branch_type', '=', 'workshop'),('branch_id', 'in', self.env.user.branch_ids.ids)])
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                               string="Model", related='vehicle_id.model_id', store=True)
    vin_sn = fields.Char(string="Chassis Number",related='vehicle_id.vin_sn', store=True)
    usage_type = fields.Selection(string="Usage Type",related='vehicle_id.usage_type', store=True)
    route_id = fields.Many2one('branch.route', string="Route")
    request_creation_date = fields.Datetime(string='Request Creation Date', required=False)
    open_date = fields.Datetime(string='Open Date', required=False,copy=False)
    request_close_date = fields.Datetime(string='Close Date', required=False,copy=False)
    request_duration = fields.Float(string="Duration", compute="_compute_duration")
    maintenance_job_order_ids= fields.One2many(comodel_name='maintenance.job.order',inverse_name='maintenance_request_id',)
    maintenance_job_order_count=fields.Integer(compute="_compute_maintenance_job_order_count")
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='maintenance_request_id', string="Transfer")
    transfer_count = fields.Integer(compute="_compute_transfer_count")
    route_branch_domain = fields.Binary(
        string="Route Branch domain", help="Dynamic domain used for the Source branch",
        compute="_compute_route_branch_domain")

    def _compute_route_branch_domain(self):
        for rec in self:
            rec.route_branch_domain = [
                ('id', '=', 5),
            ]

    @api.depends('maintenance_job_order_ids')
    def _compute_maintenance_job_order_count(self):
        for maintenance in self:
            maintenance.maintenance_job_order_count=len(maintenance.maintenance_job_order_ids.ids)

    @api.depends('transfer_ids')
    def _compute_transfer_count(self):
        for maintenance in self:
            maintenance.transfer_count=len(maintenance.transfer_ids.ids)

    @api.depends('open_date', 'request_close_date')
    def _compute_duration(self):
        for rec in self:
            rec.request_duration = 0
            if rec.open_date and rec.request_close_date:
                open_shift = self.get_current_shift(rec.open_date)
                close_shift = self.get_current_shift(rec.request_close_date)
                if open_shift and close_shift:
                    open_time = self._time_to_float(rec.open_date)
                    close_time = self._time_to_float(rec.request_close_date)
                    if open_shift.id == close_shift.id:
                        rec.request_duration = (close_time - open_time)
                    else:
                        rec.request_duration = (open_shift.hour_to - open_time) + (close_time - close_shift.hour_from)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.request.seq')
        return super().create(vals_list)
    def action_repair_approval_request(self):
        for rec in self:
            rec.stage_id = self.env.ref('maintenance.stage_1').id
    def action_confirm(self):
        for rec in self:
            #must be a vehicle to open
            if not rec.route_id:
                raise ValidationError(_('Please select a route Branch for this vehicle'))
            if not rec.schedule_date:
                raise ValidationError(_('Please Add a Schedule Date for this request'))
            rec.open_date = fields.Datetime.now()
            current_shift = self.get_current_shift(rec.open_date)
            if not current_shift:
                raise ValidationError(_('No shift found at this time'))
            rec.stage_id = self.env.ref('maintenance.stage_3').id
            rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_under_maintenance').id

    def _time_to_float(self, dt):
        """Convert a datetime object to a float representing hours (e.g., 14:30 -> 14.5)."""
        if not dt:
            return 0.0
        hours = dt.hour
        minutes = dt.minute
        return hours + minutes / 60.0

    def get_current_shift(self,date):
        for rec in self:
            open_date = date + timedelta(hours=3)
            day_name = open_date.strftime("%A")
            day_of_week = DAYS_reverse.get(day_name)
            open_time_float = self._time_to_float(open_date)
            if day_of_week is None:
                return False
            domain = [
                ('dayofweek', '=', day_of_week),
                ('hour_from', '<=', open_time_float),
                ('hour_to', '>=', open_time_float),
            ]
            current_shift = self.env['maintenance.shift'].search(domain,limit=1)
            return current_shift
        return False

    def action_close(self):
        #job order must be repaired to close
        for rec in self:
            rec.request_close_date = fields.Datetime.now()
            if rec.open_date > rec.request_close_date:
                raise ValidationError(_('Close Date must be greater than Open Date'))
            current_shift = self.get_current_shift(rec.request_close_date)
            if not current_shift:
                raise ValidationError(_('No shift found at this time'))
            rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_ready_to_rent').id

            rec.stage_id = self.env.ref('maintenance.stage_4').id
    def action_cancel(self):
        #no cancellation if job order
        for rec in self:
            rec.stage_id = self.env.ref('maintenance_custom.stage_5').id
    def action_reject(self):
        for rec in self:
            rec.stage_id = self.env.ref('maintenance_custom.stage_6').id
    def action_reset_draft(self):
        for rec in self:
            rec.stage_id = self.env.ref('maintenance.stage_0').id
    def action_create_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Job Order'),
            'res_model': 'maintenance.job.order.wizard',
            'view_mode': 'form',
            'context': {'default_maintenance_request_id': self.id},
            'target': 'new',
        }

    def view_maintenance_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Job Order'),
            'res_model': 'maintenance.job.order',
            'view_mode': 'list,form',
            'domain':[('id','in',self.maintenance_job_order_ids.ids)]
        }
    def view_maintenance_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain':[('id','in',self.transfer_ids.ids)]
        }




class MaintenanceTeamInherit(models.Model):
    _inherit = 'maintenance.team'

    route_id = fields.Many2one('stock.route')


class BranchRoute(models.Model):
    _inherit = 'branch.route'

    def action_approve(self):
        for rec in self:
            if not rec.vehicle_route_ids:
                raise ValidationError(
                    _("You can't approve route with empty vehicles"))
            if rec.destination_type and rec.destination_type == 'workshop':
                if rec.vehicle_route_ids:
                    for vehicle in rec.vehicle_route_ids:
                        if vehicle.fleet_vehicle_id.state_id.id == self.env.ref('fleet_status.fleet_vehicle_state_under_maintenance').id:
                            raise ValidationError(_(f'This Vehicle {vehicle.fleet_vehicle_id.name}is already under maintenance'))


        self.vehicle_route_ids.action_branch_approve()
        self.write({'state': 'approved', 'approve_date': fields.Datetime.now()})



