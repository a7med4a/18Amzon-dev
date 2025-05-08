from odoo import models, fields, api
ACCOUNT_DOMAIN = [('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'off_balance'))]

class BillConfigSettings(models.Model):
    _name = 'bill.config.settings'
    _description = 'Bill Default Settings'
    _rec_name='journal_id'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([('company_id','=',self.env.company.id)],order="id desc",limit=1)
        if config:
            field_names = [
                'journal_id', 'account_id', 'is_bill',
            ]
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field]
                for field in field_names
            })
            result['tax_ids'] = [(6, 0, config.tax_ids.ids)]
        return result


    journal_id = fields.Many2one("account.journal", string="Bill Journal",required=True,domain=[("type", "=", "purchase")])
    account_id = fields.Many2one("account.account", string="Account for lines",required=True,domain=ACCOUNT_DOMAIN)
    tax_ids = fields.Many2many('account.tax',string="Taxes",domain="[('type_tax_use', '=', 'purchase')]",)
    is_bill = fields.Boolean(string="Use for bills", required=True )
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company.id,
                                 domain=lambda self: [
                                     ('id', 'in', self.env.user.company_ids.ids)], string='Company', required=True)

    @api.model_create_multi
    def create(self, values):
        res=False
        for vals in values:
            config = self.env["bill.config.settings"].search([('company_id','=',vals['company_id'])], order="id desc", limit=1)
            if config:
                config.write(vals)
                res= config
            else:
                res = super().create(vals)
        return res
