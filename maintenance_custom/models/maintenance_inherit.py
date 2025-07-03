# -*- coding: utf-8 -*-
from email.policy import default

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
    maintenance_type = fields.Selection([('preventive', 'Preventive'),('damage', 'Damage'),  ('accident', 'Accident')], string='Type', default="damage")
    damage_id = fields.Many2one('fleet.damage',string='Damage Number')
    accident_id = fields.Many2one('fleet.accident',string='Accident Number')
    stage_type = fields.Selection(related='stage_id.stage_type', string='Stage Type', readonly=True,tracking=True)
    worksheet_template_id = fields.Many2one(
        'worksheet.template', string="Worksheet Template",invisible=True,
        domain="[('res_model', '=', 'maintenance.request'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Create templates for each type of request you have and customize their content with your own custom fields.")
    request_description = fields.Text('Request Description')
    vehicle_id=fields.Many2one('fleet.vehicle',string='Vehicle',required=False)
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                               string="Model", related='vehicle_id.model_id', store=True)
    vin_sn = fields.Char(string="Chassis Number",related='vehicle_id.vin_sn', store=True)
    usage_type = fields.Selection(string="Usage Type",related='vehicle_id.usage_type', store=True)
    route_id = fields.Many2one('branch.route', string="Route")
    request_creation_date = fields.Datetime(string='Request Creation Date', required=False,default=fields.Datetime.now(),readonly=True)
    open_date = fields.Datetime(string='Open Date', required=False,copy=False)
    request_close_date = fields.Datetime(string='Close Date', required=False,copy=False)
    request_duration = fields.Float(string="Duration", compute="_compute_duration")
    maintenance_job_order_ids= fields.One2many(comodel_name='maintenance.job.order',inverse_name='maintenance_request_id',)
    maintenance_external_job_order_ids= fields.One2many(comodel_name='maintenance.external.job.order',inverse_name='maintenance_request_id')
    move_ids= fields.One2many(comodel_name='account.move',inverse_name='maintenance_request_id')
    moves_count=fields.Integer("Moves",compute="_compute_moves_count")
    maintenance_job_order_count=fields.Integer(compute="_compute_maintenance_job_order_count")
    maintenance_external_job_order_count=fields.Integer(compute="_compute_maintenance_external_job_order_count")
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='maintenance_request_id', string="Transfer")
    transfer_count = fields.Integer(compute="_compute_transfer_count")
    transfer_old_spare_parts_count = fields.Integer(compute="_compute_transfer_count")
    route_branch_domain = fields.Binary(string="Route Branch domain", help="Dynamic domain used for Vehicle",compute="_compute_route_branch_domain")
    vehicle_domain = fields.Binary(string="Route Branch domain", help="Dynamic domain used for Vehicle",compute="_compute_vehicle_domain")
    allow_maintenance_expense_billing = fields.Boolean(related='maintenance_team_id.allow_maintenance_expense_billing',required=False,default=False)


    @api.depends("maintenance_team_id")
    def _compute_vehicle_domain(self):
        for maintenance in self:
            domain=[('id', 'not in', self.env['maintenance.request'].search([('stage_type', 'in', ('new', 'under_approval', 'opened'))]).mapped('vehicle_id').ids),('company_id', '=', self.env.company.id), ('branch_id.branch_type', '=', 'workshop')]
            if maintenance.maintenance_team_id :
                domain.append(('branch_id', '=', maintenance.maintenance_team_id.allowed_branch_id.id))
            maintenance.vehicle_domain = domain

    @api.depends("move_ids")
    def _compute_moves_count(self):
        for maintenance in self:
            maintenance.moves_count=len(maintenance.move_ids)

    @api.depends("vehicle_id","maintenance_team_id")
    def _compute_route_branch_domain(self):
        for maintenance in self:
            domain=[('destination_type', '=', 'workshop')]
            if maintenance.maintenance_team_id:
                domain.append(('destination_branch_id', '=', maintenance.maintenance_team_id.allowed_branch_id.id))
            if maintenance.vehicle_id:
                domain.append(('vehicle_route_ids.fleet_vehicle_id', '=', maintenance.vehicle_id.id))
            if not maintenance.vehicle_id:
                domain = [('id', '=', 0)]
            maintenance.route_branch_domain = domain

    @api.depends('maintenance_job_order_ids')
    def _compute_maintenance_job_order_count(self):
        for maintenance in self:
            maintenance.maintenance_job_order_count=len(maintenance.maintenance_job_order_ids.ids)

    @api.depends('maintenance_external_job_order_ids')
    def _compute_maintenance_external_job_order_count(self):
        for maintenance in self:
            maintenance.maintenance_external_job_order_count=len(maintenance.maintenance_external_job_order_ids.ids)

    @api.depends('transfer_ids')
    def _compute_transfer_count(self):
        for maintenance in self:
            maintenance.transfer_count=len(maintenance.transfer_ids.filtered(lambda x: x.is_old_spare_parts == False).ids)
            maintenance.transfer_old_spare_parts_count=len(maintenance.transfer_ids.filtered(lambda x: x.is_old_spare_parts == True).ids)

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
            if vals['vehicle_id']:
                self.env['fleet.vehicle'].browse(vals['vehicle_id']).write({'state_id': self.env.ref('fleet_status.fleet_vehicle_state_waiting_maintenance').id})
        return super().create(vals_list)

    def write(self, vals):
        vehicle_id = vals.get('vehicle_id', False)
        if vehicle_id and self.stage_type == 'new':
            self.env['fleet.vehicle'].browse(vehicle_id).write(
                {'state_id': self.env.ref('fleet_status.fleet_vehicle_state_waiting_maintenance').id})
        return super().write(vals)

    def action_repair_approval_request(self):
        for rec in self:
            if not rec.vehicle_id:
                raise ValidationError(_('Please select a vehicle'))
            # if not rec.open_date:
            #     raise ValidationError(_('Please Add a open Date for this request'))
            rec.open_date = fields.Datetime.now()
            current_shift = self.get_current_shift(rec.open_date)
            if not current_shift:
                raise ValidationError(_('No shift found at this time'))
            rec.stage_id = self.env.ref('maintenance.stage_1').id
            users = self.env.ref('maintenance_custom.group_approve_for_accident_repair').users
            activity_vals = []
            for user_id in users:
                activity_vals.append({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'automated': True,
                    'note': f"Maintenance Request number {rec.name} is in state Opened",
                    'user_id': user_id.id,
                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'maintenance.request')]).id,
                })
            self.env['mail.activity'].create(activity_vals)

    def action_confirm(self):
        for rec in self:
            #must be a vehicle to open
            if not rec.vehicle_id:
                raise ValidationError(_('Please select a vehicle'))
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
            if rec.maintenance_type == 'damage' and not rec.damage_id:
                raise ValidationError(_('Please add damage number before opening request'))
            if rec.maintenance_type == 'accident' and not rec.accident_id:
                raise ValidationError(_('Please add Accident number before opening request'))

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
            shifts= rec.maintenance_team_id.maintenance_shift_id.maintenance_shift_line_ids
            current_shift = shifts.filtered(lambda shift: shift.type != 'day_off' and shift.dayofweek == day_of_week and shift.hour_from <= open_time_float and shift.hour_to >= open_time_float )
            return current_shift
        return False

    def action_close(self):
        #job order must be repaired to close
        for rec in self:
            rec.request_close_date = fields.Datetime.now()
            if rec.open_date > rec.request_close_date:
                raise ValidationError(_('Close Date must be greater than Open Date'))
            if rec.maintenance_job_order_ids:
                for job in rec.maintenance_job_order_ids:
                    if job.state not in ('cancelled','repaired'):
                        raise ValidationError(_('You must repair or cancel job orders before you close maintenance request'))
            current_shift = self.get_current_shift(rec.request_close_date)
            if not current_shift:
                raise ValidationError(_('No shift found at this time'))
            rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_ready_to_transfer_from_workshop').id

            rec.stage_id = self.env.ref('maintenance.stage_4').id
    def action_cancel(self):
        for rec in self:
            if rec.maintenance_job_order_ids:
                for job in rec.maintenance_job_order_ids:
                    if job.state != 'cancelled':
                        raise ValidationError(_('You must cancel all job orders before you cancel maintenance request'))
            if rec.stage_type=='opened':
                rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_ready_to_transfer_from_workshop').id
            else:
                rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_waiting_maintenance').id
            rec.stage_id = self.env.ref('maintenance_custom.stage_5').id
    def action_reject(self):
        for rec in self:
            rec.stage_id = self.env.ref('maintenance_custom.stage_6').id
            rec.vehicle_id.state_id = self.env.ref('fleet_status.fleet_vehicle_state_waiting_maintenance').id

    def action_reset_draft(self):
        for rec in self:
            rec.stage_id = self.env.ref('maintenance.stage_0').id
    def action_create_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Job Order'),
            'res_model': 'maintenance.job.order.wizard',
            'view_mode': 'form',
            'context': {'default_maintenance_request_id': self.id,'default_job_order_type': 'internal'},
            'target': 'new',
        }
    def action_create_external_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('External Job Order'),
            'res_model': 'maintenance.job.order.wizard',
            'view_mode': 'form',
            'context': {'default_maintenance_request_id': self.id,'default_job_order_type': 'external'},
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

    def view_maintenance_external_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('External Job Order'),
            'res_model': 'maintenance.external.job.order',
            'view_mode': 'list,form',
            'domain':[('id','in',self.maintenance_external_job_order_ids.ids)]
        }

    def view_maintenance_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain':[('id','in',self.transfer_ids.ids),('is_old_spare_parts', '=',False)]
        }
    def view_maintenance_old_spare_parts_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain':[('id','in',self.transfer_ids.ids),('is_old_spare_parts', '=',True)]
        }
    

    def action_create_bill(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'maintenance_custom.action_maintenance_create_bill'
        )
        action['context'] = {
            'default_move_type': 'in_invoice',
            'default_maintenance_request_id': self.id,
            'default_journal_id': self.maintenance_team_id.journal_id.id if self.maintenance_team_id and self.maintenance_team_id.journal_id else False,
        }
        return action


    def view_expense_bills(self):
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice')
        action['domain'] =[('move_type', 'in', ['in_invoice', 'in_refund']),('maintenance_request_id', '=',self.id)]
        return action


class MaintenanceTeamInherit(models.Model):
    _inherit = 'maintenance.team'

    route_id = fields.Many2one('stock.route',string='Internal Route')
    external_route_id = fields.Many2one('stock.route',string='External Route')
    maintenance_shift_id = fields.Many2one('maintenance.shift.name')
    delivery_operation_id = fields.Many2one('stock.picking.type')
    old_spare_parts_operation_type_id = fields.Many2one('stock.picking.type',domain=[('code','=','incoming')])
    allowed_branch_id = fields.Many2one('res.branch' ,domain=[('branch_type','=' ,'workshop')])
    allowed_branch_ids = fields.Many2many('res.branch' ,domain=[('branch_type','=' ,'rental')])
    is_quick_maintenance = fields.Boolean(string='Quick Maintenance',required=False,default=False)
    allow_maintenance_expense_billing = fields.Boolean(required=False,default=False)
    journal_id = fields.Many2one('account.journal', string='Bill Journal', required=True,domain=[("type", "=", "purchase")])
    account_id = fields.Many2one('account.account', string='Expense Account', required=True)
    notified_accountant_ids = fields.Many2many(comodel_name='res.users',string='Notified Accountants')

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



