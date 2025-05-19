from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InsurancePolicyTerminationLog(models.Model):
    _name = 'termination.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id= fields.Many2one('fleet.vehicle',string="Chassis Number",readonly=True)
    police_id= fields.Many2one('insurance.policy',string="Insurance Policy Reference",readonly=True)
    police_line_id= fields.Many2one('insurance.policy.line')
    stop_date = fields.Date(string="Stop Date", required=True)
    estimated_refunded_amount = fields.Float(string="Estimated Refunded Amount",readonly=True)
    actual_refunded_amount = fields.Float(string="Actual Refunded Amount",tracking=True)
    termination_details = fields.Text(string="Termination Details")
    type = fields.Selection(string='Type',selection=[('refunded', 'Refunded'), ('cancel', 'Cancellation'), ],readonly=True)
    from_month = fields.Integer(string='From',readonly=True)
    to_month = fields.Integer(string='To',readonly=True)
    percentage = fields.Float(string='Percentage(%)',readonly=True)
    credit_note_status = fields.Selection([
        ('true', 'True'),
        ('false', 'False'),],default="false",readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated')]
        , string="Status", default='draft',tracking=True)

    @api.onchange("stop_date")
    def recompute_estimated_refunded_amount(self):
        for rec in self :
            rec.estimated_refunded_amount=((rec.police_line_id.end_date - rec.stop_date).days) * rec.police_line_id.daily_rate


    def action_cancel(self):
        for record in self:
            record.status = 'cancelled'

    def terminate(self):
        for record in self:
            if record.status == "draft" :
                record.status = 'terminated'
                record.police_line_id.insurance_status='terminated'

    def action_draft(self):
        for record in self:
            record.status = 'draft'

    def action_create_credit_note(self):
        config = self.env["insurance.config.settings"].search([('company_id','=',self.env.company.id)], order="id desc", limit=1)
        if not config:
            raise ValidationError("No configuration found For this company!")
        account_move_obj = self.env['account.move']
        credit_lines_vals = []
        partner_id = 0
        insurance_policy_id=0
        for rec in self:
            if rec.credit_note_status == "false" and rec.status == "terminated":
                analytic_data = {rec.vehicle_id.analytic_account_id.id: 100}
                credit_lines_vals.append({
                    'vehicle_id': rec.vehicle_id.id,
                    'account_id': config.refund_insurance_account_id.id,
                    'quantity': 1,
                    'price_unit': rec.actual_refunded_amount,
                    'analytic_distribution': analytic_data,
                    'tax_ids': [(6, 0, config.tax_ids.ids)],
                })
                partner_id = rec.police_id.insurance_company.id
                insurance_policy_id = rec.police_id.id
        if credit_lines_vals:
            credit_vals = {
                'move_type': 'in_refund',
                'partner_id': partner_id,
                'insurance_policy_id': insurance_policy_id,
                'is_insurance_credit_note':True,
                'invoice_line_ids': [(0, 0, line) for line in credit_lines_vals],
                'currency_id': self.env.company.currency_id.id,
            }
            credit = account_move_obj.create(credit_vals)
            if credit:
                self.write({'credit_note_status': 'true'})
