# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request',string='Maintenance Request Number',required=False)
    account_id = fields.Many2one(comodel_name='account.account')

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list=vals_list)
        for move in moves:
            if move.maintenance_request_id and move.maintenance_request_id.maintenance_team_id.allow_maintenance_expense_billing and move.invoice_line_ids:
                activity_vals=[]
                for user_id in move.maintenance_request_id.maintenance_team_id.notified_accountant_ids:
                    activity_vals.append({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'automated': True,
                        'note': f"Please Confirm Bill number {move.name} and pay it",
                        'user_id': user_id.id,
                        'res_id': move.maintenance_request_id.id,
                        'res_model_id': self.env['ir.model'].search(
                            [('model', '=', 'maintenance.request')]).id,
                    })
                self.env['mail.activity'].create(activity_vals)
                for line in move.invoice_line_ids:
                    line.analytic_distribution={move.maintenance_request_id.vehicle_id.analytic_account_id.id: 100}
                    line.vehicle_id=move.maintenance_request_id.vehicle_id.id
        return moves