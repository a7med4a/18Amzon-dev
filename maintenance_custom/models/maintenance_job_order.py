# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

DAYS_reverse = {'Monday': '0',
                'Tuesday': '1',
                'Wednesday': '2',
                'Thursday': '3',
                'Friday': '4',
                'Saturday': '5',
                'Sunday': '6'}

class MaintenanceJobOrder(models.Model):
    _name = 'maintenance.job.order'
    _description="Maintenance Job Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Job Order Number', readonly=True,tracking=True)
    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request',string='Maintenance Request Number',required=True,tracking=True)
    repair_task_ids = fields.Many2many('workshop.repair.task',string="Repair Tasks")
    vehicle_id=fields.Many2one('fleet.vehicle',related="maintenance_request_id.vehicle_id",string='Vehicle',readonly=True,store=True)
    plate_number=fields.Char(related="vehicle_id.license_plate",string="Plate Number")
    vin_sn = fields.Char(string="Chassis Number",related='vehicle_id.vin_sn')
    maintenance_workshop_id=fields.Many2one(comodel_name='maintenance.workshop',string='Maintenance Workshop',required=True)
    workshop_type=fields.Selection(related="maintenance_workshop_id.type")
    job_order_creation_date = fields.Datetime(string='Job Order Creation', required=False,copy=False,tracking=True)
    job_order_start_date = fields.Datetime(string='Job Order Start', required=False,copy=False,tracking=True)
    job_order_close_date = fields.Datetime(string='Job Order Close', required=False,copy=False,tracking=True)
    duration = fields.Float(string="Duration", compute="_compute_duration")
    technicians_ids = fields.Many2many('hr.employee',tracking=True)
    technicians_cost = fields.Float(string="Technicians Cost", compute="_compute_technicians_cost")
    spare_parts_cost = fields.Float(string="Spare Parts Cost", compute="_compute_spare_parts_cost")
    component_ids = fields.One2many(comodel_name='maintenance.job.order.component',inverse_name='maintenance_job_order_id',string='Components',required=False)
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='maintenance_job_order_id', string="Transfer")
    note = fields.Text(string="Job Order Notes", required=False)
    state = fields.Selection([('under_process', "Under Process"), ('in_progress', "In Progress"), (
        'repaired', "Repaired"),('cancelled', "Cancelled")], string="State", default='under_process',tracking=True)

    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.job.order.seq')
        return super().create(vals_list)

    @api.depends('job_order_start_date', 'job_order_close_date')
    def _compute_duration(self):
        for rec in self:
            rec.duration = 0
            if rec.job_order_start_date and rec.job_order_close_date and rec.state == 'repaired':
                open_shift = self.get_current_shift(rec.job_order_start_date)
                close_shift = self.get_current_shift(rec.job_order_close_date)
                if open_shift and close_shift:
                    open_time = self._time_to_float(rec.job_order_start_date)
                    close_time = self._time_to_float(rec.job_order_close_date)
                    if open_shift.id == close_shift.id:
                        rec.duration = (close_time - open_time)
                    else:
                        rec.duration = (open_shift.hour_to - open_time) + (close_time - close_shift.hour_from)

    @api.depends('technicians_ids','technicians_ids.cost_per_hour','duration')
    def _compute_technicians_cost(self):
        for rec in self :
            rec.technicians_cost = sum((emp.cost_per_hour * rec.duration) for emp in rec.technicians_ids)

    @api.depends('technicians_ids')
    def _compute_spare_parts_cost(self):
        for rec in self :
            rec.spare_parts_cost = 0


    def action_in_progress(self):
        for rec in self:
            rec.job_order_start_date=fields.Datetime.now()
            open_shift=self.get_current_shift(rec.job_order_start_date)
            if not open_shift:
                raise ValidationError(_('No shift is working right now'))
            rec.state='in_progress'

    def action_repaired(self):
        for rec in self:
            rec.job_order_close_date = fields.Datetime.now()
            close_shift = self.get_current_shift(rec.job_order_close_date)
            if not close_shift:
                raise ValidationError(_('No shift is working right now'))
            if any(rec.component_ids.filtered(lambda component:component.picking_status == 'in_progress')):
                raise ValidationError(_('Picking Status must be Done or Cancelled  before closing job order'))
            rec.state='repaired'

    def action_cancelled(self):
        for rec in self:
            rec.state='cancelled'

    def action_set_to_under_process(self):
        for rec in self:
            rec.state='under_process'

    def action_request_spare_parts(self):
        for rec in self:
            if not rec.component_ids:
                raise ValidationError(_('No component found to Request Spare Parts'))
            if rec.transfer_ids and all([component.spart_part_request != 'pending' for component in rec.component_ids]):
                raise ValidationError(_('You have already requested Spare Parts'))
            route=rec.maintenance_request_id.maintenance_team_id.route_id
            route_rules=route.rule_ids
            line_vals = []
            for component in rec.component_ids.filtered(lambda x:x.spart_part_request=='pending'):
                line_vals.append({
                    'product_id': component.product_id.id,
                    'product_uom': component.uom_id.id,
                    'product_uom_qty': component.demand_qty,
                    'job_order_component_id': component.id,
                    'name': rec.name,
                })
            number = 0
            for rule in route_rules:
                number +=1
                stock_picking=self.env['stock.picking'].create({'maintenance_request_id': rec.maintenance_request_id.id,
                                                  "maintenance_job_order_id": rec.id,
                                                  "picking_type_id": rule.picking_type_id.id,
                                                  "location_id": rule.location_src_id.id,
                                                  "location_dest_id": rule.location_dest_id.id,
                                                  "origin": rec.maintenance_request_id.name,
                                                  "state": "draft" if number==1 else "waiting",
                                                  "number":number,
                                                  "move_ids_without_package": [
                                                      (0, 0, {**vals, "location_id": rule.location_dest_id.id}) for vals in line_vals]})
                if stock_picking and number==1:
                    stock_picking.action_confirm()
                else:
                    stock_picking.write({'state':'waiting'})
            for component in rec.component_ids:
                component.spart_part_request='done'
            print(rec.maintenance_request_id.transfer_ids)


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

            shifts = rec.maintenance_request_id.maintenance_team_id.maintenance_shift_id.maintenance_shift_line_ids
            current_shift = shifts.filtered(lambda shift: shift.type != 'day_off' and shift.dayofweek == day_of_week and shift.hour_from <= open_time_float and shift.hour_to >= open_time_float)

            return current_shift
        return False



class MaintenanceJobOrderComponent(models.Model):
    _name = 'maintenance.job.order.component'
    _description="Maintenance Job Order Component"

    maintenance_job_order_id = fields.Many2one(comodel_name='maintenance.job.order')
    product_category_id = fields.Many2one(comodel_name='product.category',string='Product Category',required=True)
    product_id=fields.Many2one(comodel_name='product.template',string='Product',required=True)
    uom_id = fields.Many2one("uom.uom",related='product_id.uom_id', string="Unit Of Measure", export_string_translation=False)
    demand_qty=fields.Float(string="Demand")
    done_qty=fields.Float(string="Done Quantity")
    spart_part_request = fields.Selection(string='Spart part Request',selection=[('pending', 'Pending'),('done', 'Done'),],required=False,default="pending" )
    picking_status = fields.Selection(string='Picking Status',selection=[('in_progress', 'In Progress'),('done', 'Done'),('cancelled', 'Cancelled'),],required=False,default="in_progress" )
    product_category_domain = fields.Binary(string="Product Category domain", help="Dynamic domain used for Product Category",compute="_compute_product_category_domain")

    @api.depends('maintenance_job_order_id','maintenance_job_order_id.maintenance_workshop_id','maintenance_job_order_id.maintenance_workshop_id.workshop_product_category_ids',)
    def _compute_product_category_domain(self):
        for component in self:
            domain=[]
            if component.maintenance_job_order_id:
                print(component.maintenance_job_order_id.maintenance_workshop_id.workshop_product_category_ids.mapped('product_category').ids)
                domain.append(('id','in',component.maintenance_job_order_id.maintenance_workshop_id.workshop_product_category_ids.mapped('product_category').ids))
            component.product_category_domain=domain

    def unlink(self):
        if self.spart_part_request=='done':
            raise ValidationError(
                _("You can't delete component which is already spare part requests"))
        return super().unlink()

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request')
    maintenance_job_order_id = fields.Many2one(comodel_name='maintenance.job.order')
    number = fields.Integer(
        string='Number', 
        required=False)


                


class StockMove(models.Model):
    _inherit = 'stock.move'

    job_order_component_id = fields.Many2one(comodel_name='maintenance.job.order.component')

