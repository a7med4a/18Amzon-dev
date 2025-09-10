from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LimousineContractTimesheet(models.Model):
    _name = 'limousine.contract.timesheet'
    _description = 'Limousine Contract Timesheet'
    _order = 'date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.companies.ids)])

    # Basic Fields
    date = fields.Date(string='Date')
    description = fields.Char(string='Description')

    # Relation Fields
    contract_id = fields.Many2one('limousine.contract', string='Contract', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True)

    # Time and Rate Fields
    time_spent = fields.Float(string='Time Spent', help="Time spent in days (1 = Full Day, 0.5 = Half Day)")
    time_spent_char = fields.Char(string='Time Spent', help="Time spent in days (1 = Full Day, 0.5 = Half Day)")
    daily_rate = fields.Float(string='Daily Rate')

    # Status Fields
    invoice_state = fields.Selection([
        ('waiting', 'Waiting'),
        ('invoiced', 'Invoiced')
    ], string='Invoice State', default='waiting')
