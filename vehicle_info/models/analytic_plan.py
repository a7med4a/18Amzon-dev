# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'
    
    is_vehicle = fields.Boolean('Is Vehicle')
    
    def unlink(self):
        if self.filtered(lambda plan: plan.get_external_id().get(plan.id) == 'vehicle_info.vehicle_analytic_plan'):
            raise ValidationError(
                _("You can't delete Analytic Plan related to vehicles"))
        return super().unlink()
