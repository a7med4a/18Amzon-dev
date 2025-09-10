from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    property_account_receivable_id = fields.Many2one(related='company_id.property_account_receivable_id', readonly=False)
    category_id = fields.Many2many(related='company_id.category_id', readonly=False)

    # Shifts configuration fields
    limousine_full_day_from = fields.Float(related='company_id.limousine_full_day_from', readonly=False)
    limousine_full_day_to = fields.Float(related='company_id.limousine_full_day_to', readonly=False)
    limousine_half_day_from = fields.Float(related='company_id.limousine_half_day_from', readonly=False)
    limousine_half_day_to = fields.Float(related='company_id.limousine_half_day_to', readonly=False)
    limousine_free_day_from = fields.Float(related='company_id.limousine_free_day_from', readonly=False)
    limousine_free_day_to = fields.Float(related='company_id.limousine_free_day_to', readonly=False)
