# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.account.models import company
from odoo.exceptions import UserError, ValidationError


class ContractFinesDiscountWiz(models.TransientModel):
    _name = 'rental.contract.fines.discount.wiz'
    _description = 'Rental Contract Fines and Discount Wizard'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Rental Contract', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', related="rental_contract_id.company_id")
    type = fields.Selection([
        ('fine', 'Fine'),
        ('discount', 'Discount'),
    ], string='Type', required=True)
    lines = fields.One2many(
        'rental.contract.fines.discount.wiz.line', 'wizard_id', string='Lines')

    def add_fines_discount(self):
        """
        This method is called when the user clicks the "Add" button in the wizard.
        It adds the selected fines and discounts to the rental contract.
        """
        if not self.rental_contract_id:
            raise UserError(_('Please select a rental contract.'))

        allowed_journal_ids = self.rental_contract_id.vehicle_branch_id.sales_journal_ids
        branch_analytic_account_ids = self.rental_contract_id.vehicle_branch_id.analytic_account_ids
        if not allowed_journal_ids:
            raise ValidationError(
                _(f"Add Sales Journals To {self.rental_contract_id.vehicle_branch_id.name}"))
        if not branch_analytic_account_ids:
            raise ValidationError(
                _(f"Add Analytic Accounts To {self.rental_contract_id.vehicle_branch_id.name}"))

        item_vals_list = []
        fines_discount_line_ids = []
        analytic_data = {
            self.rental_contract_id.vehicle_id.analytic_account_id.id: 100,
            branch_analytic_account_ids[0].id: 100
        }

        for line in self.lines:
            price_unit = line.config_id.price
            if self.rental_contract_id.tax_percentage:
                price_unit = price_unit / \
                    (1 + (self.rental_contract_id.tax_percentage / 100))

            item_vals_list.append((0, 0, {
                'name': line.config_id.name + ' / ' + line.name,
                'account_id': line.config_id.account_id.id,
                'quantity': 1,
                'price_unit': price_unit,
                'analytic_distribution': analytic_data,
                'tax_ids': [(6, 0, line.tax_ids.ids)]
            }))

            # Create a new line in the rental contract
            fines_discount_line_ids.append((0, 0, {
                'name': line.name,
                'price': line.config_id.price,
                'fines_discount_id': line.config_id.id,
                'type': self.type,
            }))

        entry_vals = {
            'move_type': 'out_invoice' if self.type == 'fine' else 'out_refund',
            'rental_contract_id': self.rental_contract_id.id,
            'invoice_date': fields.Date.today(),
            'journal_id': allowed_journal_ids[0].id,
            'partner_id': self.rental_contract_id.partner_id.id,
            'invoice_line_ids': item_vals_list,
            'currency_id': self.rental_contract_id.company_currency_id.id,
        }

        account_move_id = self.env['account.move'].sudo().create(entry_vals)
        account_move_id.action_post()

        self.rental_contract_id.write(
            {'fines_discount_line_ids': fines_discount_line_ids})

        return {'type': 'ir.actions.act_window_close'}


class ContractFinesDiscountWizLine(models.TransientModel):
    _name = 'rental.contract.fines.discount.wiz.line'
    _description = 'Rental Contract Fines and Discount Wizard Line'

    wizard_id = fields.Many2one(
        'rental.contract.fines.discount.wiz', string='Wizard Reference')
    config_id = fields.Many2one(
        'contract.fines.discount.config', string='Configuration', required=True,domain="[('contract_type', '=', 'rental')]")
    price = fields.Float(
        string='Price', related='config_id.price', readonly=True)
    name = fields.Char(string='Description', required=True)
    tax_ids = fields.Many2many(
        'account.tax', string='taxes', related="config_id.tax_ids")
