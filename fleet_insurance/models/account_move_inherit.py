from datetime import datetime
from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from odoo.osv import expression

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    insurance_policy_id = fields.Many2one('insurance.policy', string="Insurance Policy Reference", readonly=True)
    insurance_policy_ids = fields.One2many('insurance.policy', 'vendor_bill_id', string="Vendor Bills")
    is_insurance_bill = fields.Boolean(string='Is Insurance Bill', readonly=True)
    is_insurance_credit_note = fields.Boolean(string='Is Insurance credit note', readonly=True)

    def unlink(self):
        for rec in self:
            if rec.insurance_policy_ids:
                for policy in rec.insurance_policy_ids:
                    policy.show_create_bill = True
                    for line in policy.policy_lines_ids:
                        line.bill_status = "false"
        return super().unlink()

class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    insurance_policy_line_id = fields.Many2one('insurance.policy.line', string="Insurance Policy")

    def unlink(self):
        for line in self:
        # policy.show_create_bill = True
            if line.insurance_policy_line_id:
                line.insurance_policy_line_id.bill_status = "false"
                line.move_id.insurance_policy_id.show_create_bill = True
        return super().unlink()