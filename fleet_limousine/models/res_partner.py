from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    limousine_driver = fields.Boolean(default=False)
    driver_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], tracking=True, default='internal')
    driver_state = fields.Selection([
        ('free', 'Free'),
        ('busy', 'Busy'),
        ('warning', 'Warning'),
        ('blocked', 'Blocked')
    ], tracking=True, default='free')

    @api.model
    def default_get(self, fields):
        defaults = super(ResPartner, self).default_get(fields)
        if self.env.context.get('default_limousine_driver', False):
            defaults['property_account_receivable_id'] = self.env.company.property_account_receivable_id.id
            defaults['category_id'] = [(6, 0, self.env.company.category_id.ids)]
        return defaults
