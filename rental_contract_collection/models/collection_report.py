
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CollectionReport(models.Model):
    _name = 'collection.action.report'
    _description = 'Collection Report'

    name = fields.Char('name')
    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', required=True)
    partner_id = fields.Many2one(
        'res.partner', related='rental_contract_id.partner_id', string='Customer', store=True)
    communication_date = fields.Date('Communication  Date')
    contact_type_id = fields.Many2one(
        'collection.contact.type', string='Contact Type')
    contact_result_id = fields.Many2one(
        'collection.contact.result', string='Contact Result')
    notes = fields.Char('Notes')

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        for contract in contracts:
            # Set Report Name
            contract.name = self.env['ir.sequence'].next_by_code(
                'collection.report.seq')
        return contracts
