from odoo import models, fields, api

class DamageConfigSettings(models.Model):
    _name = 'damage.config.settings'
    _description = 'Damage Default Settings'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([],order="id desc",limit=1)
        if config:
            field_names = ['journal_id', 'damage_account_id','description']
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field] for field in field_names
            })
            result['tax_ids'] = [(6, 0, config.tax_ids.ids)]

        return result

    journal_id = fields.Many2one("account.journal", string="Journal",required=True,domain=[("type", "=", "sale")])
    damage_account_id = fields.Many2one("account.account",required=True,string="Damage Account")
    description = fields.Text(string="Description",required=True)
    tax_ids = fields.Many2many('account.tax',string="Taxes",domain=[("type_tax_use", "=", "sale")])

    @api.model_create_multi
    def create(self, values):
        config = self.env["damage.config.settings"].search([], order="id desc", limit=1)
        if config:
            config.write(values)
            return config
        return super().create(values)



