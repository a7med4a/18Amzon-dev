# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError
from datetime import date


class LongTermPricingRequest(models.Model):
    _name = 'long.term.pricing.request'
    _description = 'Long Term Pricing Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'


    name = fields.Char(string="Name",readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company.id,
                                 domain=lambda self: [
                                     ('id', 'in', self.env.user.company_ids.ids)], string='Company', required=True)
    description = fields.Text(string="Description",required=False)
    long_term_pricing_request_line_ids=fields.One2many(comodel_name='long.term.pricing.request.line', inverse_name='long_term_pricing_request_id', string='Long Term Pricing Request Line')
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', "Draft"), ('under_review', "Under Review"), (
        'confirmed', "Confirmed"),('refused', "Refused"), ('cancelled', "Cancelled")], string="State", default='draft', tracking=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('long.term.pricing.request.seq')
        return super().create(vals_list)



    def action_under_review(self):
        for rec in self:
            if not rec.long_term_pricing_request_line_ids :
                raise ValidationError("Please Add Request line First")
            for line in rec.long_term_pricing_request_line_ids:
                if line.rental_pricing_monthly <= 0:
                    raise ValidationError("Rental Pricing(Monthly) must be greater than 0")
            rec.state = 'under_review'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
    def action_expired(self):
        for rec in self:
            if rec.long_term_pricing_request_line_ids:
                for line in rec.long_term_pricing_request_line_ids:
                    line.pricing_status = 'expired'


class LongTermPricingRequestLine(models.Model):
    _name = 'long.term.pricing.request.line'
    _description = 'Long Term Pricing Request Line'


    long_term_pricing_request_id = fields.Many2one(comodel_name='long.term.pricing.request', string='Long Term Pricing Request')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle',required=True, string='Vehicle',
                                 domain=lambda self: [('usage_type', '=', 'long_term'),('company_id', '=', self.env.company.id),
                                                      ('id', 'not in',self.env['long.term.pricing.request.line'].search([
                                                           ('long_term_pricing_request_id.state', 'in',
                                                            ('draft', 'under_review', 'confirmed'))]).mapped('vehicle_id').ids)])
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',related='vehicle_id.model_id', string='Vehicle Model')
    rental_pricing_monthly=fields.Float(string="Rental Price (Monthly)",required=True)
    vehicle_status = fields.Selection([('excellent','Excellent'),('good','Good'),('accident','Accident')],required=True, string='Vehicle Status',default='excellent')
    pricing_status = fields.Selection([('running','Running'),('expired','Expired')],required=True, string='Pricing Status',default='running')

    @api.constrains('vehicle_id')
    def _check_vehicle_id(self):
        for record in self:
            long_term_request_line = self.env["long.term.pricing.request.line"].search(
                [("vehicle_id", "=", record.vehicle_id.id),("pricing_status", "=", 'running'),("long_term_pricing_request_id", "=", record.long_term_pricing_request_id.id)])
            if len(long_term_request_line) > 1:
                raise ValidationError(
                    _(f"Vehicle already has an active long term Request number( {long_term_request_line[0].long_term_pricing_request_id.name} )!")
                )


    def action_running(self):
        for rec in self:
            rec.pricing_status = 'running'

    def action_expired(self):
        for rec in self:
            rec.pricing_status = 'expired'

class vehicle_info(models.Model):
    _inherit = 'fleet.vehicle'

    usage_type = fields.Selection(
        selection=[('rental', 'Rental'), ('limousine', 'Limousine'), ('long_term', 'Long Term')],
        string='Usage Type')

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