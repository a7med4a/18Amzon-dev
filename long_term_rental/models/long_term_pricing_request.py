# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class LongTermPricingRequest(models.Model):
    _name = 'long.term.pricing.request'
    _description = 'Long Term Pricing Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Name", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.companies.ids)])
    description = fields.Text(string="Description", required=False)
    long_term_pricing_request_line_ids = fields.One2many(
        comodel_name='long.term.pricing.request.line', inverse_name='long_term_pricing_request_id', string='Long Term Pricing Request Line')
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', "Draft"), ('under_review', "Under Review"), (
        'confirmed', "Running"), ('expired', 'Expired'), ('refused', "Refused"), ('cancelled', "Cancelled")], string="State", default='draft', tracking=True)
    is_all_pricing_lines_expired = fields.Boolean(
        string="All Pricing Lines Expired", compute="_compute_is_all_pricing_lines_expired", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'long.term.pricing.request.seq')
        return super().create(vals_list)

    @api.depends('long_term_pricing_request_line_ids.pricing_status')
    def _compute_is_all_pricing_lines_expired(self):
        for rec in self:
            if rec.long_term_pricing_request_line_ids:
                all_expired = all(
                    line.pricing_status == 'expired' for line in rec.long_term_pricing_request_line_ids)
                rec.is_all_pricing_lines_expired = all_expired
            else:
                rec.is_all_pricing_lines_expired = False

    def send_group_branch_route_manager_notification(self):
        # send activity to group_branch_route_manager
        self.ensure_one()
        group_pricing_request_manager = self.env.ref(
            'long_term_rental.group_pricing_request_manager')
        if group_pricing_request_manager:
            for user in group_pricing_request_manager.users:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary=_('Pricing Request Approval Needed'),
                    note=_(
                        'Pricing Request %s is waiting for approval.') % self.name,
                    date_deadline=fields.Date.context_today(self),
                    res_model='long.term.pricing.request',
                    res_id=self.id
                )

    def _get_related_activities(self):
        domain = [
            ('res_model', '=', 'long.term.pricing.request'),
            ('activity_type_id', '=', self.env.ref(
                'mail.mail_activity_data_todo').id),
            ('res_id', 'in', self.ids),
            ('user_id', 'in', self.env.ref(
                'long_term_rental.group_pricing_request_manager').users.ids)
        ]

        activities = self.env['mail.activity'].search(domain)
        return activities

    def action_under_review(self):
        for rec in self:
            if not rec.long_term_pricing_request_line_ids:
                raise ValidationError("Please Add Request line First")
            for line in rec.long_term_pricing_request_line_ids:
                if line.rental_pricing_monthly <= 0:
                    raise ValidationError(
                        "Rental Pricing(Monthly) must be greater than 0")
            rec.send_group_branch_route_manager_notification()
            rec.state = 'under_review'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_confirm(self):
        for rec in self:
            rec._get_related_activities().action_feedback()
            rec.state = 'confirmed'

    def action_refuse(self):
        for rec in self:
            rec._get_related_activities().action_feedback()
            rec.state = 'refused'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_expired(self):
        for rec in self:
            if rec.long_term_pricing_request_line_ids:
                for line in rec.long_term_pricing_request_line_ids:
                    line.pricing_status = 'expired'
        self.write({'state': 'expired'})

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise ValidationError(
                    _("You cannot delete a Long Term Pricing Request that is not in draft state."))
        return super().unlink()


class LongTermPricingRequestLine(models.Model):
    _name = 'long.term.pricing.request.line'
    _description = 'Long Term Pricing Request Line'

    long_term_pricing_request_id = fields.Many2one(
        comodel_name='long.term.pricing.request', string='Long Term Pricing Request')
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle', required=True, string='Vehicle')
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                               related='vehicle_id.model_id', string='Vehicle Model')
    rental_pricing_monthly = fields.Float(
        string="Rental Price (Monthly)", required=True)
    vehicle_status = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'), (
        'accident', 'Accident')], required=True, string='Vehicle Status', default='excellent')
    pricing_status = fields.Selection([('draft', "Draft"), ('under_review', "Under Review"), (
        'confirmed', "Running"), ('expired', 'Expired'), ('refused', "Refused"), ('cancelled', "Cancelled")], compute="_compute_pricing_status", store=True, string='Pricing Status', default='draft')
    vehicle_domain = fields.Binary(
        string="In Branch domain", help="Dynamic domain used for the in branch", compute="_compute_vehicle_domain")

    down_payment = fields.Float(
        'Down Payment', default=0.0, help="Down payment for the vehicle")
    installment_no = fields.Integer(
        'Installment No', default=0, help="Number of installments for the vehicle")
    monthly_day_price = fields.Float('Monthly Day Price', default=0.0,
                                     help="Monthly day price for the vehicle")
    vehicle_cost = fields.Float(
        'Vehicle Cost', default=0.0, help="Cost of the vehicle for long term rental", compute="_compute_vehicle_cost", store=True)

    @api.depends('long_term_pricing_request_id.state')
    def _compute_pricing_status(self):
        for record in self:
            if record.long_term_pricing_request_id.state == 'draft':
                record.pricing_status = 'draft'
            elif record.long_term_pricing_request_id.state == 'under_review':
                record.pricing_status = 'under_review'
            elif record.long_term_pricing_request_id.state == 'confirmed':
                record.pricing_status = 'confirmed'
            elif record.long_term_pricing_request_id.state == 'expired':
                record.pricing_status = 'expired'
            elif record.long_term_pricing_request_id.state == 'refused':
                record.pricing_status = 'refused'
            elif record.long_term_pricing_request_id.state == 'cancelled':
                record.pricing_status = 'cancelled'

    @api.depends('vehicle_id', 'long_term_pricing_request_id')
    def _compute_vehicle_domain(self):
        running_vehicle_ids = self.env['long.term.pricing.request.line'].search([
            ('pricing_status', 'in',
             ('draft', 'under_review', 'confirmed'))
        ]).mapped('vehicle_id').ids
        for rec in self:
            domain = [('usage_type', '=', 'long_term'), ('company_id', '=', rec.long_term_pricing_request_id.company_id.id), ('branch_id.branch_type', '=', 'long_term'),
                      ('id', 'not in', running_vehicle_ids + rec.long_term_pricing_request_id.long_term_pricing_request_line_ids.mapped('vehicle_id').ids)]
            rec.vehicle_domain = domain

    @api.depends('rental_pricing_monthly', 'installment_no', 'down_payment')
    def _compute_vehicle_cost(self):
        for record in self:
            record.vehicle_cost = (
                record.rental_pricing_monthly * record.installment_no) + record.down_payment

    @api.constrains('vehicle_id')
    def _check_vehicle_id(self):
        for record in self:
            long_term_request_line = self.env["long.term.pricing.request.line"].search(
                [("vehicle_id", "=", record.vehicle_id.id), ("pricing_status", "=", 'confirmed'), ("long_term_pricing_request_id", "=", record.long_term_pricing_request_id.id)])
            if len(long_term_request_line) > 1:
                raise ValidationError(
                    _(f"Vehicle already has an active long term Request number( {long_term_request_line[0].long_term_pricing_request_id.name} )!")
                )

    def action_confirmed(self):
        for rec in self:
            rec.pricing_status = 'confirmed'

    def action_expired(self):
        for rec in self:
            rec.pricing_status = 'expired'


class vehicle_info(models.Model):
    _inherit = 'fleet.vehicle'

    usage_type = fields.Selection(
        selection=[('rental', 'Rental'), ('limousine', 'Limousine'),
                   ('long_term', 'Long Term')],
        string='Usage Type')

    def write(self, vals):
        if 'usage_type' in vals:
            for record in self:
                if record.usage_type == 'long_term':
                    long_term_contracts = self.env['long.term.rental.contract'].search([
                        ('vehicle_id', '=', record.id),
                        ('state', 'in', ['draft', 'opened'])
                    ])
                    if long_term_contracts:
                        raise ValidationError(
                            _(f"This vehicle is already associated with an active long term contract. {','.join(long_term_contracts.mapped('name'))}."))
                elif record.usage_type == 'rental':
                    rental_contracts = self.env['rental.contract'].search([
                        ('vehicle_id', '=', record.id),
                        ('state', 'in', ['draft', 'opened'])
                    ])
                    if rental_contracts:
                        raise ValidationError(
                            _(f"This vehicle is already associated with an active rental contract. {','.join(rental_contracts.mapped('name'))}."))
        return super().write(vals)


class Branch(models.Model):
    _inherit = 'res.branch'
    _description = 'Branches'

    branch_type = fields.Selection([
        ('rental', 'Rental'),
        ('limousine', 'Limousine'),
        ('workshop', 'Workshop'),
        ('administration', 'Administration'),
        ('long_term', 'Long Term')
    ], string='Branch Type')
