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
    _description = "Maintenance Job Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Job Order Number', readonly=True, tracking=True)
    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance Request Number',
                                             required=True, tracking=True)
    repair_task_ids = fields.Many2many('workshop.repair.task', string="Repair Tasks")
    vehicle_id = fields.Many2one('fleet.vehicle', related="maintenance_request_id.vehicle_id", string='Vehicle',
                                 readonly=True, store=True)
    plate_number = fields.Char(related="vehicle_id.license_plate", string="Plate Number")
    vin_sn = fields.Char(string="Chassis Number", related='vehicle_id.vin_sn')
    maintenance_workshop_id = fields.Many2one(comodel_name='maintenance.workshop', string='Maintenance Workshop',
                                              required=True)
    workshop_type = fields.Selection(related="maintenance_workshop_id.type")
    job_order_creation_date = fields.Datetime(string='Job Order Creation', required=False, copy=False, tracking=True)
    job_order_start_date = fields.Datetime(string='Job Order Start', required=False, copy=False, tracking=True)
    job_order_close_date = fields.Datetime(string='Job Order Close', required=False, copy=False, tracking=True)
    duration = fields.Float(string="Duration", compute="_compute_duration")
    technicians_ids = fields.Many2many('hr.employee', tracking=True)
    technicians_cost = fields.Float(string="Technicians Cost", compute="_compute_technicians_cost")
    spare_parts_cost = fields.Float(string="Spare Parts Cost", compute="_compute_spare_parts_cost")
    component_ids = fields.One2many(comodel_name='maintenance.job.order.component',
                                    inverse_name='maintenance_job_order_id', string='Components', required=False)
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='maintenance_job_order_id',
                                   string="Transfer")
    note = fields.Text(string="Job Order Notes", required=False)
    state = fields.Selection([('under_process', "Under Process"), ('in_progress', "In Progress"), (
        'repaired', "Repaired"), ('cancelled', "Cancelled")], string="State", default='under_process', tracking=True)
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)

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

    @api.depends('technicians_ids', 'technicians_ids.cost_per_hour', 'duration')
    def _compute_technicians_cost(self):
        for rec in self:
            rec.technicians_cost = sum((emp.cost_per_hour * rec.duration) for emp in rec.technicians_ids)

    @api.depends('technicians_ids')
    def _compute_spare_parts_cost(self):
        for rec in self:
            picking_moves = rec.transfer_ids
            stock_valuation_layer = picking_moves.move_ids.stock_valuation_layer_ids
            rec.spare_parts_cost = sum((layer.value) for layer in stock_valuation_layer)

    def action_in_progress(self):
        for rec in self:
            rec.job_order_start_date = fields.Datetime.now()
            open_shift = self.get_current_shift(rec.job_order_start_date)
            if not open_shift:
                raise ValidationError(_('No shift is working right now'))
            if rec.maintenance_request_id.stage_type != 'opened':
                raise ValidationError(_('Maintenance Request must be in opened state to start job order'))
            rec.state = 'in_progress'

    def action_repaired(self):
        for rec in self:
            rec.job_order_close_date = fields.Datetime.now()
            close_shift = self.get_current_shift(rec.job_order_close_date)
            if not close_shift:
                raise ValidationError(_('No shift is working right now'))
            if any(rec.component_ids.filtered(lambda component: component.picking_status == 'in_progress')) or any(
                    rec.component_ids.filtered(lambda component: component.spart_part_request == 'pending')):
                raise ValidationError(_('Picking Status must be Done or Cancelled before closing job order'))
            if not rec.technicians_ids:
                raise ValidationError(_('Please add technicians before closing job order'))
            rec.state = 'repaired'

    def action_cancelled(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_set_to_under_process(self):
        for rec in self:
            if rec.transfer_ids and any(rec.transfer_ids.filtered(lambda x: x.state != 'cancel')):
                raise ValidationError(
                    _('Transfer must be in cancelled before setting job order to under process'))
            rec.component_ids.write({'spart_part_request':'pending'})
            rec.state = 'under_process'
            rec.job_order_start_date = False

    def action_request_spare_parts(self):
        """
        Request spare parts for maintenance job order using Odoo's standard procurement system.
        This method creates procurement orders for each component that needs spare parts,
        utilizing warehouse routes and stock rules to generate proper stock movements.
        """
        for rec in self:
            if not rec.component_ids:
                raise ValidationError(_('No component found to Request Spare Parts'))

            if rec.transfer_ids and all([component.spart_part_request != 'pending' for component in rec.component_ids]):
                raise ValidationError(_('You have already requested Spare Parts'))

            # Get the route from maintenance team
            route = rec.maintenance_request_id.maintenance_team_id.route_id
            if not route:
                raise ValidationError(_('No route defined for the maintenance team'))

            # Create or get procurement group
            if not rec.procurement_group_id:
                rec.procurement_group_id = self.env['procurement.group'].create({
                    'name': rec.name,
                    'move_type': 'direct',
                    'partner_id': self.env.company.partner_id.id,
                })

            procurement_group = rec.procurement_group_id

            # Get destination location from the route's last rule
            destination_location = False
            if route.rule_ids:
                destination_location = route.rule_ids[-1].location_dest_id

            if not destination_location:
                raise ValidationError(_('Could not determine destination location from route'))

            procurements = []
            errors = []

            # Create procurement values for each component
            for component in rec.component_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                # Get the product from product_id (product.template)
                product_variant = component.product_id.product_variant_id
                if not product_variant:
                    errors.append(_('No product variant found for %s') % component.product_id.name)
                    continue

                # Create procurement values - corrected format for Odoo 18
                values = {
                    'group_id': procurement_group,
                    'maintenance_job_order_id': rec.id,
                    'maintenance_request_id': rec.maintenance_request_id.id,
                    'job_order_component_id': component.id,
                    'date_planned': fields.Datetime.now(),
                    'product_id': product_variant,
                    'product_qty': component.demand_qty,
                    'product_uom': component.uom_id,
                    'location_id': destination_location,
                    'name': rec.name,
                    'origin': rec.maintenance_request_id.name,
                    'company_id': rec.maintenance_request_id.company_id or self.env.company,
                    'route_ids': route,  # Corrected format for many2many field
                }

                # Add to procurements list in the correct format for Odoo 18
                procurements.append(self.env['procurement.group'].Procurement(
                    product_variant,
                    component.demand_qty,
                    component.uom_id,
                    destination_location,
                    rec.name,
                    rec.maintenance_request_id.name,
                    rec.maintenance_request_id.company_id or self.env.company,
                    values
                ))

            # If there are errors, raise them
            if errors:
                raise ValidationError('\n'.join(errors))

            # Run procurements with the correct format
            if procurements:
                self.env['procurement.group'].run(procurements)

                # Mark components as requested
                for component in rec.component_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                    component.spart_part_request = 'done'

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

            shifts = rec.maintenance_request_id.maintenance_team_id.maintenance_shift_id.maintenance_shift_line_ids
            current_shift = shifts.filtered(lambda
                                                shift: shift.type != 'day_off' and shift.dayofweek == day_of_week and shift.hour_from <= open_time_float and shift.hour_to >= open_time_float)

            return current_shift
        return False


class MaintenanceJobOrderComponent(models.Model):
    _name = 'maintenance.job.order.component'
    _description = "Maintenance Job Order Component"

    maintenance_job_order_id = fields.Many2one(comodel_name='maintenance.job.order')
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
                                                 ('cancelled', 'Cancelled'), ], required=False, default="in_progress",
                                      compute="_compute_picking_status")
    product_category_domain = fields.Binary(string="Product Category domain",
                                            help="Dynamic domain used for Product Category",
                                            compute="_compute_product_category_domain")

    def _compute_picking_status(self):
        for component in self:
            picking_moves = component.maintenance_job_order_id.transfer_ids
            if picking_moves:
                move_lines= picking_moves[-1].move_line_ids
                done_qty = sum(move_lines.mapped('qty_done'))
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

    @api.depends('maintenance_job_order_id', 'maintenance_job_order_id.maintenance_workshop_id',
                 'maintenance_job_order_id.maintenance_workshop_id.workshop_product_category_ids', )
    def _compute_product_category_domain(self):
        for component in self:
            domain = []
            if component.maintenance_job_order_id:
                domain.append(('id', 'in',
                               component.maintenance_job_order_id.maintenance_workshop_id.workshop_product_category_ids.mapped(
                                   'product_category').ids))
            component.product_category_domain = domain

    def unlink(self):
        if self.spart_part_request == 'done':
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

    def _get_new_picking_values(self):
        """Override to add maintenance fields to new pickings"""
        vals = super(StockMove, self)._get_new_picking_values()

        # Check if this move is related to a maintenance job order
        if self.group_id and self.group_id.name:
            # Try to find the maintenance job order
            job_order = self.env['maintenance.job.order'].search([
                ('procurement_group_id', '=', self.group_id.id)
            ], limit=1)

            if job_order:
                vals.update({
                    'maintenance_job_order_id': job_order.id,
                    'maintenance_request_id': job_order.maintenance_request_id.id,
                    'origin': job_order.maintenance_request_id.name,
                })

        return vals


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        """Override to properly link stock moves to maintenance job orders"""
        res = super(ProcurementGroup, self)._run_scheduler_tasks(use_new_cursor=use_new_cursor, company_id=company_id)

        # Link stock moves to job order components
        if use_new_cursor:
            self.env.cr.commit()

        return res

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        """Override to add maintenance fields to stock moves"""
        move_values = super(ProcurementGroup, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin, company_id, values)

        # Add job order component if present in values
        if values.get('job_order_component_id'):
            move_values['job_order_component_id'] = values['job_order_component_id']

        return move_values
