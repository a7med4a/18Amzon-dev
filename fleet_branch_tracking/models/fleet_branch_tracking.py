# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetBranchTracking(models.Model):
    _name = 'fleet.branch.tracking'
    _description = 'Fleet Branch Tracking'
    _rec_name = "fleet_id"

    fleet_id = fields.Many2one('fleet.vehicle', string='Fleet', required=True)
    from_branch_id = fields.Many2one('res.branch', string='From')
    to_branch_id = fields.Many2one('res.branch', string='To')
    # todo: add m2o Field with ever selection if exist also add external_change key to context with True Value when update branch from other model and if for another record
    type = fields.Selection([
        ('manual', 'Manual'),
        ('route', 'Route'),
        ('rental', 'Rental')
    ], string='Type', required=True)

    ref = fields.Char('Ref', compute="_compute_ref", store=True)
    route_id = fields.Many2one('branch.route', string='Route')
    rental_id = fields.Many2one('rental.contract', string='Rental')

    @api.depends('route_id', 'rental_id')
    def _compute_ref(self):
        for rec in self:
            if rec.route_id:
                rec.ref = rec.route_id.name
            elif rec.rental_id:
                rec.ref = rec.rental_id.name

    @api.constrains('route_id', 'rental_id')
    def _check_exist_more_than_foreign_key(self):
        for rec in self:
            if rec.route_id and rec.rental_id:
                raise ValidationError(
                    _("You Can refer one branch tracking record to more than changing type create new record instead."))
