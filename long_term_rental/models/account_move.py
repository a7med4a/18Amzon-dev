# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command


class AccountMove(models.Model):
    _inherit = 'account.move'

    term_long_rental_contract_id = fields.Many2one(
        'long.term.rental.contract', string='Long Term Rental Contract')
    additional_supplement_service_line_id = fields.Many2one(
        'additional.supplementary.services.line')
    contract_installment_line_id = fields.Many2one(
        'contract.installment.line')
