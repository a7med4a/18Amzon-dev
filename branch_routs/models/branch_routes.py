# -*- coding: utf-8 -*-

from ast import Raise
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BranchRoute(models.Model):
    _name = 'branch.route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Branch Routes'

    name = fields.Char(required=False, string="Branch Route Sequence")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
    destination_type = fields.Selection([
        ('branch', 'Branch'), ('workshop', 'WorkShop')], string='Destination Type', required=True)
    source_branch_id = fields.Many2one(
        'res.branch', string='Source', required=True, default=lambda self: self.env.branch)
    destination_branch_id = fields.Many2one(
        'res.branch', string='Destination', required=True)
    transfer_type = fields.Selection([
        ('driver', 'By Driver'),
        ('amazon', 'Amazon Truck'),
        ('outsource', 'Third Party Truck')
    ], string='Transfer Type', required=True)
    driver_employee_id = fields.Many2one(
        'hr.employee', string='Driver Name', domain="[('is_driver', '=', True)]")
    truck_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Truck', domain="[('is_truck', '=', True)]", copy=False)
    third_party_partner_id = fields.Many2one(
        'res.partner', string='Shipping Company', domain="[('is_third_party', '=', True)]")
    approve_date = fields.Datetime('Approve Date', copy=False)
    close_date = fields.Datetime('Close Date', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('exit_done', 'Exit Done'),
        ('entry_done', 'Entry Done'),
        ('cancel', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    vehicle_route_ids = fields.One2many(
        'vehicle.route', 'branch_route_id', string='Vehicle Route')
    active = fields.Boolean('active', default=True, copy=False)

    # smart buttons fields
    exist_permit_count = fields.Integer(
        compute="_compute_exist_permit_count")
    entry_permit_count = fields.Integer(
        compute="_compute_entry_permit_count")

    # Helping fields
    destination_branch_domain = fields.Binary(
        string="tag domain", help="Dynamic domain used for the destination branch", compute="_compute_destination_branch_domain")
    source_branch_domain = fields.Binary(
        string="tag domain", help="Dynamic domain used for the destination branch", compute="_compute_source_branch_domain")
    disable_create_vehicle_line = fields.Boolean(
        compute="_compute_disable_create_vehicle_line")
    all_vehicle_exit_done = fields.Boolean(
        compute="_compute_all_vehicle_exit_done")
    all_vehicle_entry_done = fields.Boolean(
        compute="_compute_all_vehicle_entry_done")

    @api.depends('vehicle_route_ids', 'vehicle_route_ids.exit_checklist_status')
    def _compute_exist_permit_count(self):
        for route in self:
            route.exist_permit_count = len(route.vehicle_route_ids.filtered(
                lambda vehicle_route: vehicle_route.exit_checklist_status in ['under_check', 'in_transfer']))

    @api.depends('vehicle_route_ids', 'vehicle_route_ids.entry_checklist_status')
    def _compute_entry_permit_count(self):
        for route in self:
            route.entry_permit_count = len(route.vehicle_route_ids.filtered(
                lambda vehicle_route: vehicle_route.entry_checklist_status in ['in_transfer', 'done']))

    @api.depends('destination_type', 'source_branch_id')
    def _compute_destination_branch_domain(self):
        for route in self:
            domain = [('id', '!=', route.source_branch_id.id),
                      ('company_id', '=', route.company_id.id)]
            if route.destination_type == 'branch':
                domain.append(('branch_type', 'in', ['rental', 'limousine']))
            elif route.destination_type == 'workshop':
                domain.append(('branch_type', '=', 'workshop'))
            route.destination_branch_domain = domain

    @api.depends('destination_branch_id')
    def _compute_source_branch_domain(self):
        for route in self:
            domain = [('id', '!=', route.destination_branch_id.id),
                      ('company_id', '=', route.company_id.id)]
            route.source_branch_domain = domain

    @api.depends('vehicle_route_ids', 'transfer_type')
    def _compute_disable_create_vehicle_line(self):
        for route in self:
            route.disable_create_vehicle_line = len(
                route.vehicle_route_ids) and route.transfer_type == 'driver'

    @api.depends('vehicle_route_ids', 'vehicle_route_ids.exit_checklist_status')
    def _compute_all_vehicle_exit_done(self):
        for route in self:
            route.all_vehicle_exit_done = all(
                vehicle_route.exit_checklist_status == 'in_transfer' for vehicle_route in route.vehicle_route_ids)

    @api.depends('vehicle_route_ids', 'vehicle_route_ids.entry_checklist_status')
    def _compute_all_vehicle_entry_done(self):
        for route in self:
            route.all_vehicle_entry_done = all(
                vehicle_route.entry_checklist_status == 'done' for vehicle_route in route.vehicle_route_ids)

    @api.constrains('source_branch_id', 'destination_branch_id')
    def _check_source_destination_branch_id(self):
        for route in self:
            if route.source_branch_id == route.destination_branch_id:
                raise ValidationError(
                    _("Source and destination Location can't be the same"))

    @api.onchange('transfer_type')
    def _onchange_transfer_type(self):
        self.driver_employee_id = False
        self.truck_vehicle_id = False
        self.third_party_partner_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'branch.routs.seq')
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            if not rec.vehicle_route_ids:
                raise ValidationError(
                    _("You can't approve route with empty vehicles"))
        self.vehicle_route_ids.action_branch_approve()
        self.write({'state': 'approved', 'approve_date': fields.Datetime.now()})

    def action_exit_done(self):
        self.vehicle_route_ids.action_branch_exit_done()
        self.write({'state': 'exit_done'})

    def action_entry_done(self):
        self.vehicle_route_ids.action_branch_entry_done()
        self.write(
            {'state': 'entry_done', 'close_date': fields.Datetime.now()})

    def action_button_cancel(self):
        self.vehicle_route_ids.action_branch_button_cancel()
        self.write({'state': 'cancel'})

    def action_button_draft(self):
        self.vehicle_route_ids.action_branch_button_draft()
        self.write({'state': 'draft'})

    def unlink(self):
        if any(rec.state != 'draft' for rec in self):
            raise ValidationError(_("Only Draft Record Can Be deleted"))
        return super().unlink()
