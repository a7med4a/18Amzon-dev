from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    blacklist_status = fields.Selection(string="Blacklist Status", selection=[
        ("running", "Running"),
        ("warning", "Warning"),
        ("blocked", "Blocked")], required=False, default="running", readonly=True,store=True)
    blacklist_reason = fields.Text(string='Blacklist Reason', readonly=True)
    blacklist_history_ids = fields.One2many('res.partner.blacklist.history', 'partner_id', string='Blacklist History')
