# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MaintenanceShift(models.Model):
    _name = 'maintenance.shift'
    _description="Maintenance Shift"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='5',tracking=True)
    hour_from = fields.Float(string='Work from', required=True, index=True,
                             help="Start and End time of working.\n"
                                  "A specific value of 24:00 is interpreted as 23:59:59.999999.",tracking=True)
    hour_to = fields.Float(string='Work to', required=True,tracking=True)
    duration_hours = fields.Float(compute='_compute_duration_hours', string='Duration (hours)',tracking=True)
    workshop_id=fields.Many2one('maintenance.workshop', string='Workshop', required=True)

    @api.depends('hour_from', 'hour_to')
    def _compute_duration_hours(self):
        for shift in self:
            shift.duration_hours = shift.hour_to - shift.hour_from

    @api.constrains('hour_from', 'hour_to')
    def _check_hours(self):
        for shift in self:
            if shift.hour_from >= shift.hour_to:
                raise ValidationError(_("Start time must be before end time."))
            if shift.hour_from < 0 or shift.hour_from > 24 or shift.hour_to < 0 or shift.hour_to > 24:
                raise ValidationError(_("Hours must be between 0 and 24."))

    @api.constrains('dayofweek')
    def _check_dayofweek(self):
        for shift in self:
            if shift.dayofweek not in ['0', '1', '2', '3', '5', '6']:
                raise ValidationError(_("Friday is a day off for maintenance."))

