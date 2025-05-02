from odoo import fields, models

class ResPartnerBlacklistHistory(models.Model):
    _name = 'res.partner.blacklist.history'
    _description = 'Customer Blacklist History'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)
    action = fields.Selection(selection=[
        ("blocked", "Blocked"),
        ("unblocked", "UnBlocked")
    ], string="Action", required=True)
    type = fields.Selection(selection=[
        ("running", "Running"),
        ("warning", "Warning"),
        ("blocked", "Blocked"),
        ("unblocked", "UnBlocked")
    ], string="Type", required=True)
    reason = fields.Text(string='Reason')
