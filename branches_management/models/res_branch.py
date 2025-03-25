# -*- coding: utf-8 -*-
##########################################################################


from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError



class ResBranch(models.Model):
    _name = "res.branch"
    _description = "Branches"
    _order = 'name'

    @api.model
    def _get_user_currency(self):
        return self.env['res.currency.rate'].search([('rate', '=', 1)], limit=1).currency_id

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self._get_user_currency())
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, related="company_id.partner_id")
    user_ids = fields.Many2many('res.users', 'res_branch_users_rel', 'bid', 'user_id', string='Accepted Users')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state', string="Fed. State")
    country_id = fields.Many2one('res.country', string="Country")
    area_id = fields.Many2one('res.area',
                              string='Area', domain="[('state_id', '=', state_id)]")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The branch name must be unique !')
    ]

    @api.onchange('state_id')
    def _onchange_state(self):
        self.country_id = self.state_id.country_id

    def on_change_country(self, country_id):
        # This function is called from account/models/chart_template.py, hence decorated with `multi`.
        self.ensure_one()
        currency_id = self._get_user_currency()
        if country_id:
            currency_id = self.env['res.country'].browse(country_id).currency_id
        return {'value': {'currency_id': currency_id.id}}

    @api.onchange('country_id')
    def _onchange_country_id_wrapper(self):
        res = {'domain': {'state_id': []}}
        if self.country_id:
            res['domain']['state_id'] = [('country_id', '=', self.country_id.id)]
        values = self.on_change_country(self.country_id.id)['value']
        for fname, value in values.items():
            setattr(self, fname, value)
        return res

    def copy(self, default=None):
        raise UserError(_('Duplicating a branch is not allowed. Please create a new branch instead.'))

    @api.model_create_multi
    def create(self, vals):
        branch = super(ResBranch, self).create(vals)
        # The write is made on the user to set it automatically in the multi branch group.
        if branch.company_id in self.env.user.company_ids:
            self.env.user.write({'branch_ids': [(4, branch.id)]})
        return branch
