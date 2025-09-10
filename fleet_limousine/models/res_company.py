from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    property_account_receivable_id = fields.Many2one(
        comodel_name='account.account',
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
        help="This account will be used as the default receivable account for the driver",
        ondelete='restrict'
    )
    category_id = fields.Many2many(
        comodel_name='res.partner.category',
        string='Tags'
    )

    # Shifts configuration fields
    limousine_full_day_from = fields.Float(string='Full Day From')
    limousine_full_day_to = fields.Float(string='Full Day To')
    limousine_half_day_from = fields.Float(string='Half Day From')
    limousine_half_day_to = fields.Float(string='Half Day To')
    limousine_free_day_from = fields.Float(string='Free Day From')
    limousine_free_day_to = fields.Float(string='Free Day To')
