# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CollectionSetting(models.Model):
    _name = 'collection.setting'
    _description = 'Collection Setting'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([], order="id desc", limit=1)
        if config:
            field_names = ['allowed_late_days']
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field] for field in field_names
            })
            result['rental_contract_status_ids'] = [
                (6, 0, config.rental_contract_status_ids.ids)]
            result['allowed_all_contract_user_ids'] = [
                (6, 0, config.allowed_all_contract_user_ids.ids)]
            result['allowed_own_contract_user_ids'] = [
                (6, 0, config.allowed_own_contract_user_ids.ids)]

        return result

    rental_contract_status_ids = fields.Many2many(
        'ir.model.fields.selection', string='Contract Status', domain=lambda self: [('field_id', '=', self.env.ref('rental_contract.field_rental_contract__state').id)])
    allowed_late_days = fields.Integer('Allowed Late Days')
    allowed_all_contract_user_ids = fields.Many2many(
        'res.users',
        relation='collection_setting_all_users',
        string='Allowed All Contracts')
    allowed_own_contract_user_ids = fields.Many2many(
        'res.users',
        relation='collection_setting_own_users',
        string='Allowed Own Contracts')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            config = self.search([], order="id desc", limit=1)
            if config:
                config.write(vals)
                return config
        return super().create(vals_list)


class CollectionContactType(models.Model):
    _name = 'collection.contact.type'
    _description = 'Contact Type'

    name = fields.Char('Name')


class CollectionContactResult(models.Model):
    _name = 'collection.contact.result'
    _description = 'Contact Result'

    name = fields.Char('Name')
