from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LimousineFinesConfig(models.Model):
    _name = "limousine.fines.config"
    _description = "Limousine Fines Config"
    _inherit = ['mail.thread']
    _check_company_auto = True

    name = fields.Char(string='Name', required=True)
    price = fields.Float(string='Price', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True,
                                 domain="[('account_type', 'in', ['income', 'income_other'])]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tax_ids = fields.Many2many('account.tax', string='taxes', domain="[('type_tax_use', '=', 'sale')]")
    edit_type = fields.Selection([
        ('allow', 'Allow'),
        ('disallow', 'Disallow')
    ], string='Edit Type', default='disallow')
