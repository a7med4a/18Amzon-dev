# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CollectionAction(models.TransientModel):
    _name = 'collection.action.wiz'
    _description = 'Collection Action Wiz'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract')
    communication_date = fields.Date(
        'Communication  Date', default=fields.Datetime.now)
    contact_type_id = fields.Many2one(
        'collection.contact.type', string='Contact Type')
    contact_result_id = fields.Many2one(
        'collection.contact.result', string='Contact Result')
    notes = fields.Char('Notes')
    collector_user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string='Collector')
    create_on_date = fields.Datetime('Created On', default=fields.Datetime.now)

    def action_confirm(self):
        vals_list = []
        for rec in self:
            vals_list.append(
                {
                    'rental_contract_id': rec.rental_contract_id.id,
                    'contact_type_id': rec.contact_type_id.id,
                    'contact_result_id': rec.contact_result_id.id,
                    'communication_date': rec.communication_date,
                    'notes': rec.notes,
                }
            )
        self.env['collection.action.report'].create(vals_list)
