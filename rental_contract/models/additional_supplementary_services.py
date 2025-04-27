# additional.supplementary.services
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AdditionalSupplementaryServices(models.Model):
    _inherit = 'additional.supplementary.services'

    type = fields.Selection(
        selection_add=[('internal_authorization', 'Internal Authorization'),
                       ('external_authorization', 'External Authorization')],
        ondelete={'internal_authorization': 'set additional', 'external_authorization': 'set additional'})
    account_id = fields.Many2one('account.account', string='account', required=True,
                                 domain="[('account_type', 'in', ['income', 'income_other'])]")

    @api.constrains('type')
    def _check_internal_authorization_type_duplicate(self):
        for rec in self.filtered(lambda service: service._name == 'additional.supplementary.services'):
            if self.search([('type', '=', 'internal_authorization'), ('id', '!=', rec.id)]):
                raise ValidationError(
                    _("Only One Record allowed to be Internal Authorization"))
