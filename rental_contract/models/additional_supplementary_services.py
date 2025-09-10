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
    is_open_km = fields.Boolean('Open KM', copy=False, default=False)

    @api.constrains('type')
    def _check_internal_authorization_type_duplicate(self):
        for rec in self.filtered(lambda service: service._name == 'additional.supplementary.services'):
            if rec.type == 'internal_authorization' and self.search([('type', '=', 'internal_authorization'), ('id', '!=', rec.id), ('company_id', '=', rec.company_id.id)]):
                raise ValidationError(
                    _("Only One Record allowed to be Internal Authorization"))
            if rec.type == 'external_authorization' and self.search([('type', '=', 'external_authorization'), ('id', '!=', rec.id), ('company_id', '=', rec.company_id.id)]):
                raise ValidationError(
                    _("Only One Record allowed to be External Authorization"))

    @api.onchange('type')
    def _onchange_type(self):
        if self.type in ['external_authorization', 'internal_authorization']:
            self.calculation = 'once'
        if self.type in ['internal_authorization']:
            self.calculation_type = 'fixed'
