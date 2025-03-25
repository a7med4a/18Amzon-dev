# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class IndividualCustomerConfig(models.Model):
    _name = 'individual.customer.config'
    _description = 'Individual Customer Configration'
    _rec_name = 'account_receivable_id'


    category_id = fields.Many2many('res.partner.category', string='Tags')

    account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     ondelete='restrict')

    is_default = fields.Boolean(string="Set Default",  )

    @api.constrains('is_default')
    def _check_is_default(self):
        for record in self:
            if record.is_default:
                if self.search_count([('is_default', '=', True), ('id', '!=', record.id)]) > 0:
                    raise ValidationError("Only one record can be set as default.")



