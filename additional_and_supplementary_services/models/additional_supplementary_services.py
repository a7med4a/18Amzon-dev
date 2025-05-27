
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
    contract_type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
        domain=lambda self: [('id', 'in', self.env.companies.ids)])


    @api.constrains('price')
    def _check_price(self):
        for rec in self:
            if rec.price <= 0:
                raise ValidationError(
                    _('The Price of Service must be more than 0 '))
