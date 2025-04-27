from odoo import models, fields, api
ACCOUNT_DOMAIN = [('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'off_balance'))]

class BillConfigSettings(models.Model):
    _name = 'bill.config.settings'
    _description = 'Bill Default Settings'
    _rec_name='journal_id'

    journal_id = fields.Many2one("account.journal", string="Bill Journal",required=True,domain=[("type", "=", "purchase")])
    account_id = fields.Many2one("account.account", string="Account for lines",required=True,domain=ACCOUNT_DOMAIN)
    tax_ids = fields.Many2many('account.tax',string="Taxes",domain="[('type_tax_use', '=', 'purchase')]",)
    is_bill = fields.Boolean(string="Use for bills", required=True )
