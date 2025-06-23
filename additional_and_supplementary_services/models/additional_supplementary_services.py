
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
    calculation_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
    ], string='Calculation Type', default='fixed')
    price = fields.Float(required=False)
    percentage = fields.Float(string="Percentage %")
    contract_type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental')
    vehicle_model_ids = fields.Many2many(
        'fleet.vehicle.model', string='Vehicle Models')
    min_customer_age = fields.Float('Min Customer Age')
    max_customer_age = fields.Float('Max Customer Age')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
        domain=lambda self: [('id', 'in', self.env.companies.ids)])

    @api.constrains('price', 'calculation_type', 'percentage')
    def _check_price_percentage(self):
        for rec in self:
            if rec.calculation_type == 'fixed' and rec.price <= 0:
                raise ValidationError(
                    _('The Price of Service must be more than 0 '))
            elif rec.calculation_type == 'percentage' and (rec.percentage <= 0 or rec.percentage > 100):
                raise ValidationError(
                    _('The Percentage of Service must be more than 0 and less than or equal to 100'))
