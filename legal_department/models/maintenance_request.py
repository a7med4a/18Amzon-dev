# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaintenanceRequestInherit(models.Model):
    _inherit = 'maintenance.request'

    @api.depends("maintenance_team_id")
    def _compute_vehicle_domain(self):
        for maintenance in self:
            domain = [('id', 'not in', self.env['maintenance.request'].search([('stage_type', 'in', ('new', 'under_approval', 'opened'))]).mapped(
                'vehicle_id').ids), ('company_id', '=', self.env.company.id), ('branch_id.branch_type', '=', 'workshop'), ('police_alert_state', '=', False)]
            if maintenance.maintenance_team_id:
                domain.append(
                    ('branch_id', '=', maintenance.maintenance_team_id.allowed_branch_id.id))
            maintenance.vehicle_domain = domain
