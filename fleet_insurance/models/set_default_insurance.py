from odoo import models, fields, api

class InsuranceConfigSettings(models.Model):
    _name = 'insurance.config.settings'
    _description = 'Insurance Default Settings'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.search([('company_id','=',self.env.company.id)],order="id desc",limit=1)
        if config:
            field_names = [
                'insurance_journal_id', 'insurance_expense_account_id',
                'account_pay_id', 'refund_insurance_account_id',
                'refund_insurance_journal_id', 'tax'
            ]
            result.update({
                field: config[field].id if isinstance(config[field], models.Model) else config[field]
                for field in field_names
            })
            result['category_id'] = [(6, 0, config.category_id.ids)]
        return result

    insurance_journal_id = fields.Many2one("account.journal", string="Insurance Journal",required=True,domain=[("type", "=", "purchase")])
    insurance_expense_account_id = fields.Many2one("account.account",required=True,string="Insurance Expense Account")
    account_pay_id = fields.Many2one("account.account", string="A/P Account",required=True,domain=[("account_type", "=", "liability_payable")])
    refund_insurance_account_id = fields.Many2one("account.account",required=True,string="Refund Insurance Account")
    refund_insurance_journal_id = fields.Many2one("account.journal",required=True,string="Refund Insurance Journal")
    category_id = fields.Many2many('res.partner.category',string="Tags")
    tax = fields.Integer(string="Tax")
    tax_ids = fields.Many2many('account.tax',string="Taxes")
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company.id,
                                 domain=lambda self: [
                                     ('id', 'in', self.env.user.company_ids.ids)], string='Company', required=True)

    @api.model_create_multi
    def create(self, values):
        res=False
        for vals in values:
            config = self.env["insurance.config.settings"].search([('company_id','=',vals['company_id'])], order="id desc", limit=1)
            if config:
                config.write(vals)
                res= config
            else:
                res = super().create(vals)
        return res



