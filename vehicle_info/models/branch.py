# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Branch(models.Model):
    _inherit = 'branch.master.configuration'
    
    vehicle_ids = fields.One2many(
        'fleet.vehicle', 'branch_id', string='Related Vehicles')
    
    def unlink(self):
        for branch in self:
            if branch.vehicle_ids:
                raise ValidationError(_("You can't delete branch related to vehicles"))
        return super().unlink()
