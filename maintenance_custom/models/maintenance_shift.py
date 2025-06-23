# -*- coding: utf-8 -*-
from email.policy import default

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MaintenanceShiftName(models.Model):
    _name = 'maintenance.shift.name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name")
    maintenance_shift_line_ids=fields.One2many('maintenance.shift','maintenance_shift_id')

class MaintenanceShift(models.Model):
    _name = 'maintenance.shift'
    _description="Maintenance Shift"


    name=fields.Char()
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='5',tracking=True)
    hour_from = fields.Float(string='Work from', index=True,
                             help="Start and End time of working.\n"
                                  "A specific value of 24:00 is interpreted as 23:59:59.999999.",tracking=True)
    hour_to = fields.Float(string='Work to', tracking=True)
    duration_hours = fields.Float(compute='_compute_duration_hours', string='Duration (hours)',tracking=True)
    maintenance_shift_id=fields.Many2one('maintenance.shift.name', string='Maintenance Shift')
    type = fields.Selection(string='Type',selection=[('work', 'Work'), ('day_off', 'Day Off'), ],
        required=True,default='work' )


    @api.depends('hour_from', 'hour_to')
    def _compute_duration_hours(self):
        for shift in self:
            shift.duration_hours = shift.hour_to - shift.hour_from

    @api.constrains('hour_from', 'hour_to')
    def _check_hours(self):
        for shift in self:
            if shift.hour_from >= shift.hour_to :
                raise ValidationError(_("Start time must be before end time."))
            if shift.hour_from < 0 or shift.hour_from > 24 or shift.hour_to < 0 or shift.hour_to > 24:
                raise ValidationError(_("Hours must be between 0 and 24."))

