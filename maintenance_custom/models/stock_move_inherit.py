# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMoveInherit(models.Model):
    _inherit = "stock.move"


    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
        }

        svl = self.env['stock.valuation.layer'].browse(svl_id)
        if svl.account_move_line_id.analytic_distribution:
            analytic_distribution = svl.account_move_line_id.analytic_distribution
        elif self.quick_maintenance_request_component_id.quick_maintenance_request_id.vehicle_id :
            analytic_distribution = {self.quick_maintenance_request_component_id.quick_maintenance_request_id.vehicle_id.analytic_account_id.id :100}
        else :
            analytic_distribution={}

        rslt = {
            'credit_line_vals': {
                **line_vals,
                'balance': -credit_value,
                'account_id': credit_account_id,
                'analytic_distribution': svl.account_move_line_id.analytic_distribution if svl.account_move_line_id.analytic_distribution else {},
            },
            'debit_line_vals': {
                **line_vals,
                'balance': debit_value,
                'account_id': debit_account_id,
                'analytic_distribution': analytic_distribution,
            },
        }
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.env.context.get('price_diff_account')
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

            rslt['price_diff_line_vals'] = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'balance': -diff_amount,
                'ref': description,
                'partner_id': partner_id,
                'account_id': price_diff_account.id,
            }
        return rslt
