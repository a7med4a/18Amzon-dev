# -*- coding: utf-8 -*-

from odoo import models, fields, api
import pytz

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones,
                                  key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


class Company(models.Model):

    _inherit = 'res.company'

    tz = fields.Selection(_tzs, string="Time Zone", store=True,
                          compute="_compute_tz", inverse="_inverse_tz")

    @api.depends('partner_id', 'partner_id.tz')
    def _compute_tz(self):
        for rec in self:
            rec.tz = rec.parent_id.tz

    def _inverse_tz(self):
        for rec in self:
            rec.partner_id.tz = rec.tz
