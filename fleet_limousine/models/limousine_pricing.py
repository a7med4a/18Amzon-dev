from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LimousinePricing(models.Model):
    _name = "limousine.pricing"
    _description = "Limousine Pricing"
    _inherit = ['mail.thread']
    _rec_name = 'model_id'
    _check_company_auto = True

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expire', 'Expired'),
        ('cancel', 'Cancelled'),
    ], copy=False, tracking=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    model_id = fields.Many2one('fleet.vehicle.model', tracking=True, required=True)
    pricing_line_ids = fields.One2many('limousine.pricing.line', 'pricing_id')

    @api.constrains('state')
    def _check_unique_active_draft_pricing(self):
        """Ensure only one pricing can be in draft or active state"""
        for record in self:
            if record.state in ['draft', 'active']:
                # Check if there's any other record for the same model in draft or active state
                existing_records = self.search(
                    [('state', 'in', ['draft', 'active']), ('model_id', '=', record.model_id.id),
                     ('id', '!=', record.id)], limit=1)
                if existing_records:
                    existing_record = existing_records[0]
                    raise ValidationError(_("Only one pricing can be in Draft or Active state at a time." ""
                                            "There is already an existing pricing for model %s in %s state.") %
                                          (existing_record.model_id.display_name, existing_record.state))

    def action_active(self):
        """Change state to Active"""
        self.write({'state': 'active'})

    def action_expire(self):
        """Change state to Expired"""
        self.write({'state': 'expire'})

    def action_cancel(self):
        """Change state to Cancelled"""
        self.write({'state': 'cancel'})

    def action_draft(self):
        """Reset state to Draft"""
        self.write({'state': 'draft'})
