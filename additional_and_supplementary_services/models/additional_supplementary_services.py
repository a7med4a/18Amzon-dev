
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AdditionalSupplementaryServices(models.Model):
    _name = 'additional.supplementary.services'
    _description = 'Additional Supplementary Services'

    name = fields.Char(required=True)
    type = fields.Selection(
        selection=[('additional', 'Additional'), ('supplementary', 'Supplementary')], required=True)
    calculation = fields.Selection(
        selection=[('once', 'Once'), ('repeated', 'Repeated')], required=True)
    price = fields.Float(required=True)

    @api.constrains('price')
    def _check_price(self):
        for rec in self:
            if rec.price <= 0:
                raise ValidationError(
                    _('The Price of Service must be more than 0 '))
