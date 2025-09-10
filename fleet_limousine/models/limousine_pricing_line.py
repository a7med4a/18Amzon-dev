from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class LimousinePricingLine(models.Model):
    _name = 'limousine.pricing.line'
    _description = "Limousine Pricing Line"
    _check_company_auto = True

    pricing_id = fields.Many2one('limousine.pricing')
    driver_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], tracking=True, default='internal')
    daily_rate = fields.Float(tracking=True)
    is_friday_free = fields.Boolean(default=False, tracking=True)
    company_id = fields.Many2one(related='pricing_id.company_id', store=True)

    @api.constrains('pricing_id', 'driver_type')
    def _check_unique_driver_type_per_pricing(self):
        """Ensure only one internal and one external driver type per pricing"""
        for record in self:
            # Check if there's already a line with the same driver type in the same pricing
            existing_lines = self.search([
                ('pricing_id', '=', record.pricing_id.id),
                ('driver_type', '=', record.driver_type),
                ('id', '!=', record.id)
            ], limit=1)

            if existing_lines:
                raise ValidationError(
                    _("A pricing line with driver type '%s' already exists for this pricing. "
                      "You can only have one internal and one external driver type per pricing.")
                    % record.driver_type
                )
