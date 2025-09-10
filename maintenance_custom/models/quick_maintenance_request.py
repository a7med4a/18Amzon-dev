# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from lxml import etree

DAYS_reverse = {'Monday': '0',
                'Tuesday': '1',
                'Wednesday': '2',
                'Thursday': '3',
                'Friday': '4',
                'Saturday': '5',
                'Sunday': '6'}

class QuickMaintenanceRequest(models.Model):
    _name = 'quick.maintenance.request'
    _description = "Quick Maintenance Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Quick Maintenance Request Number', readonly=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,readonly=True,default=lambda self: self.env.company)
    branch_id = fields.Many2one('res.branch', string='Branch',default=lambda self: self.env.branch,readonly=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team',tracking=True,required=True)
    member_ids = fields.Many2many('res.users',related="maintenance_team_id.member_ids", tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', store=True)
    request_description = fields.Text(string="Request Description", required=True)
    maintenance_team_branch_domain = fields.Binary(string="Maintenance Team Branch domain", help="Dynamic domain used for Team",compute="_compute_maintenance_team_branch_domain")
    vehicle_branch_domain = fields.Binary(compute="_compute_vehicle_branch_domain")
    state = fields.Selection([('draft', "Draft"), ('waiting_approve', "Waiting Approve"), ('opened', "Opened"), (
        'repaired', "Repaired"), ('cancelled', "Cancelled")], string="State", default='draft', tracking=True)
    technicians_ids = fields.Many2many('hr.employee', tracking=True)
    schedule_date = fields.Datetime(string="Schedule Date", default=fields.Datetime.now)
    open_date = fields.Datetime(string="Open Date", readonly=True)
    close_date = fields.Datetime(string="Close Date", readonly=True)
    duration = fields.Float(string="Duration", compute="_compute_duration")
    technicians_cost = fields.Float(string="Technicians Cost", compute="_compute_technicians_cost")
    spare_parts_cost = fields.Float(string="Spare Parts Cost", compute="_compute_spare_parts_cost")
    component_ids = fields.One2many(comodel_name='quick.maintenance.request.component',
                                    inverse_name='quick_maintenance_request_id', string='Components', required=False)
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='quick_maintenance_request_id',string="Transfer")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('quick.maintenance.request.seq')
        return super().create(vals_list)

    def action_request_maintenance(self):
        for rec in self:
            users=self.env.ref('maintenance_custom.group_quick_maintenance_request').users
            for user in users:
                self.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                    note=f"Please Approve quick request number {rec.name}",
                    user_id=user.id,
                    date_deadline=rec.schedule_date
                )
            rec.state='waiting_approve'

    def action_approve(self):
        for rec in self:
            rec.open_date = fields.Datetime.now()
            open_shift = self.get_current_shift(rec.open_date)
            if not open_shift:
                raise ValidationError(_('No shift is working right now'))
            if not rec.technicians_ids:
                raise ValidationError(_('Please Add Technicians Before Approve Request'))
            if not rec.schedule_date:
                raise ValidationError(_('Please Add schedule date Before Approve Request'))
            rec.state='opened'

    def action_close(self):
        for rec in self:
            rec.close_date = fields.Datetime.now()
            close_shift = self.get_current_shift(rec.close_date)
            if not close_shift:
                raise ValidationError(_('No shift is working right now'))
            if rec.component_ids and any(rec.component_ids.filtered(lambda component: component.picking_status == 'in_progress')) or any(
                    rec.component_ids.filtered(lambda component: component.spart_part_request == 'pending')):
                raise ValidationError(_('Picking Status must be Done or Cancelled before closing Quick maintenance Request'))
            rec.state='repaired'

    def action_cancel(self):
        for rec in self:
            rec.state='cancelled'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


    @api.depends("branch_id")
    def _compute_maintenance_team_branch_domain(self):
        for maintenance in self:
            domain=[]
            if maintenance.branch_id:
                # Filter teams that allow this branch
                allowed_team_ids = self.env['maintenance.team'].search([
                    ('is_quick_maintenance', '=', True),
                    ('allowed_branch_ids', 'in', maintenance.branch_id.id)
                ]).ids

                domain += [('id', 'in', allowed_team_ids)]
            maintenance.maintenance_team_branch_domain = domain
            
    @api.depends("branch_id")
    def _compute_vehicle_branch_domain(self):
        for maintenance in self:
            domain=[('active','=',True),('state_id.type','not in',('stolen','sold','total_loss','under_maintenance'))]
            if maintenance.branch_id:
                domain += [('branch_id','=',maintenance.branch_id.id)]
            maintenance.vehicle_branch_domain = domain
            
    def _time_to_float(self, dt):
        """Convert a datetime object to a float representing hours (e.g., 14:30 -> 14.5)."""
        if not dt:
            return 0.0
        hours = dt.hour
        minutes = dt.minute
        return hours + minutes / 60.0

    def get_current_shift(self, date):
        for rec in self:
            open_date = date + timedelta(hours=3)
            day_name = open_date.strftime("%A")
            day_of_week = DAYS_reverse.get(day_name)
            open_time_float = self._time_to_float(open_date)
            if day_of_week is None:
                return False

            shifts = rec.maintenance_team_id.maintenance_shift_id.maintenance_shift_line_ids
            current_shift = shifts.filtered(lambda
                                                shift: shift.type != 'day_off' and shift.dayofweek == day_of_week and shift.hour_from <= open_time_float and shift.hour_to >= open_time_float)

            return current_shift
        return False

    def action_view_transfers(self):
        for rec in self :
            if rec.transfer_ids:
                action = self.env['ir.actions.actions']._for_xml_id('maintenance_custom.action_picking_tree_all_from_quick_maintenance')
                action['domain'] = [('id', 'in', rec.transfer_ids.ids)]
                return action
            else:
                raise ValidationError(_("No RFQ Created for this PR Request!"))
        return True

    def create_stock_transfer(self):
        for rec in self:
            if not rec.component_ids:
                raise ValidationError(_('No component found to Request Spare Parts'))

            if rec.transfer_ids and all([component.spart_part_request != 'pending' for component in rec.component_ids]):
                raise ValidationError(_('You have already requested Spare Parts'))

            picking_type = rec.maintenance_team_id.delivery_operation_id

            if not picking_type:
                raise UserError('No transfer operation type found,Please add operation at maintenance team ')

            # Create stock picking (transfer)
            picking_vals = {
                'picking_type_id': picking_type.id,
                'quick_maintenance_request_id': rec.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'state': 'draft',
                'origin': rec.name,
                'company_id': self.env.company.id,
            }
            picking = self.env['stock.picking'].create(picking_vals)
            for line in rec.component_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                move_vals = {
                    'picking_id': picking.id,
                    'quick_maintenance_request_component_id': line.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.demand_qty,
                    'product_uom': line.uom_id.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'name': rec.name,
                    'state': 'draft',
                }
                self.env['stock.move'].create(move_vals)

            picking.action_confirm()
            if picking:
                for component in rec.component_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                    component.spart_part_request = 'done'

    @api.depends('open_date', 'close_date')
    def _compute_duration(self):
        for rec in self:
            rec.duration = 0
            if rec.open_date and rec.open_date and rec.state == 'repaired':
                open_shift = self.get_current_shift(rec.open_date)
                close_shift = self.get_current_shift(rec.close_date)
                if open_shift and close_shift:
                    open_time = self._time_to_float(rec.open_date)
                    close_time = self._time_to_float(rec.close_date)
                    if open_shift.id == close_shift.id:
                        rec.duration = (close_time - open_time)
                    else:
                        rec.duration = (open_shift.hour_to - open_time) + (close_time - close_shift.hour_from)

    @api.depends('technicians_ids', 'technicians_ids.cost_per_hour', 'duration')
    def _compute_technicians_cost(self):
        for rec in self:
            rec.technicians_cost = sum((emp.cost_per_hour * rec.duration) for emp in rec.technicians_ids)

    @api.depends('technicians_ids')
    def _compute_spare_parts_cost(self):
        for rec in self:
            picking_moves = rec.transfer_ids
            stock_valuation_layer = picking_moves.move_ids.stock_valuation_layer_ids
            rec.spare_parts_cost = abs(sum((layer.value) for layer in stock_valuation_layer))

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError(
                _("You can't delete QMR which is not in Draft State"))
        return super().unlink()

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        admin=self.env.user.has_group('maintenance_custom.group_quick_maintenance_request')
        if view_type == 'form' and not admin and self.env.user.has_group('maintenance_custom.group_quick_maintenance_requester'):
            doc = etree.XML(res['arch'])
            for btn in doc.xpath("//button"):
                btn.set("invisible", "1")
            for mr in doc.xpath("//button[@name='action_request_maintenance']"):
                mr.set("invisible", "state != 'draft'")
            res['arch'] = etree.tostring(doc, encoding='unicode')

        return res

class QuickMaintenanceRequestComponent(models.Model):
    _name = 'quick.maintenance.request.component'
    _description = "Quick Maintenance Request Component"

    quick_maintenance_request_id = fields.Many2one(comodel_name='quick.maintenance.request')
    product_category_id = fields.Many2one(comodel_name='product.category', string='Product Category', required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)
    uom_id = fields.Many2one("uom.uom", related='product_id.uom_id', string="Unit Of Measure",
                             export_string_translation=False)
    demand_qty = fields.Float(string="Demand")
    done_qty = fields.Float(string="Done Quantity",compute="_compute_picking_status")
    spart_part_request = fields.Selection(string='Spart part Request',
                                          selection=[('pending', 'Pending'), ('done', 'Done'), ], required=False,
                                          default="pending")
    picking_status = fields.Selection(string='Picking Status',
                                      selection=[('in_progress', 'In Progress'), ('done', 'Done'),
                                                 ('cancelled', 'Cancelled'),], required=False, default="in_progress",
                                      compute="_compute_picking_status")
    product_domain = fields.Binary(string="Product domain",compute="_compute_product_domain")


    def _compute_picking_status(self):
        for component in self:
            picking_moves = component.quick_maintenance_request_id.transfer_ids
            print("picking_moves ===> ",picking_moves)
            if picking_moves:
                move_lines= picking_moves[-1].move_line_ids
                done_qty = sum(move_lines.mapped('quantity'))
                print(">>>>>>>>>>>>>>>>>>>done_qty",done_qty)
                if all([move.state == 'done' for move in picking_moves]):
                    component.picking_status = 'done'
                    component.done_qty = done_qty

                elif all([move.state == 'cancel' for move in picking_moves]):
                    component.picking_status = 'cancelled'
                    component.done_qty = 0

                else:
                    component.picking_status = 'in_progress'
                    component.done_qty = 0
            else:
                component.picking_status = 'in_progress'
                component.done_qty = 0


    def unlink(self):
        if self.spart_part_request == 'done':
            raise ValidationError(
                _("You can't delete component which is already spare part requests"))
        return super().unlink()

    @api.depends('product_category_id','quick_maintenance_request_id','quick_maintenance_request_id.vehicle_id')
    def _compute_product_domain(self):
        for component in self:
            domain = [('categ_id', '=',component.product_category_id.id)]
            if component.quick_maintenance_request_id.vehicle_id:
                domain.append(('related_model_ids', 'in',
                               component.quick_maintenance_request_id.vehicle_id.model_id.id))
            component.product_domain = domain

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    quick_maintenance_request_id = fields.Many2one(comodel_name='quick.maintenance.request')

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)

        action_id = self.env.ref('maintenance_custom.action_picking_tree_all_from_quick_maintenance').id
        if view_type == 'form' and options.get('action_id') == action_id:
            doc = etree.XML(res['arch'])
            for btn in doc.xpath("//button"):
                btn.set("invisible", "1")
            for field in doc.xpath("//field"):
                field.set("readonly", "1")
            editable_fields = ["quantity", "move_ids_without_package"]
            for name in editable_fields:
                for node in doc.xpath(f"//field[@name='{name}']"):
                    node.set("readonly", "0")
            for lst in doc.xpath("//list"):
                lst.set("create", "0")
            res['arch'] = etree.tostring(doc, encoding='unicode')

        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    quick_maintenance_request_component_id = fields.Many2one(comodel_name='quick.maintenance.request.component')
