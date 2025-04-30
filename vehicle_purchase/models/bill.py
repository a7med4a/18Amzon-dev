from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    extra_fees = fields.Monetary(
        string="Another Fees",
        currency_field='currency_id',
        default=0.0,
        help="Additional fees included in the subtotal, not included in tax base."
    )
class AccountMove(models.Model):
    _inherit = 'account.move'

    vpo_id = fields.Many2one(comodel_name="vehicle.purchase.order", string="Vehicle Purchase Order", required=False, )
    is_vehicle_purchase = fields.Boolean(string="Is Vehicle Purchase Order", default=False)

    def action_register_payment(self):
        if self.is_vehicle_purchase:
            raise ValidationError("You can't register payment for vehicle purchase order")
        res = super(AccountMove, self).action_register_payment()
        return res

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        resault = super(AccountMove,self)._prepare_product_base_line_for_taxes_computation(product_line)
        resault['extra_fees'] = product_line.extra_fees
        return resault

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # Check if the move is a vendor bill linked to a PO
        if self.move_type == 'in_invoice' and self.vpo_id:
            self.reconcile_advance_payments()
        return res

    def reconcile_advance_payments(self):
        payments = self.env['account.payment'].search([
            ('vehicle_po_id', '=', self.vpo_id.id),
            ('state', '=', 'paid'),
        ])
        print("payments ==>",payments)
        self.write({'matched_payment_ids':[(6,0,payments.ids)]})
        for payment in payments:
            payment.write({'reconciled_bill_ids': [(6, 0, self.ids)]})
        bill_line = self.line_ids.filtered(
            lambda l: l.account_id == self.partner_id.property_account_payable_id
                      and not l.reconciled
        )
        print("bill_line ==>", bill_line)
        if not bill_line or not payments:
            return

        total_payment_amount = sum(payments.mapped('amount'))
        bill_amount = abs(bill_line.balance)

        for payment in payments:
            payment_line = payment.move_id.line_ids.filtered(
                lambda l: l.account_id == payment.journal_id.default_account_id
                          and not l.reconciled
            )
            print("payment_line ==>", payment_line)
            if payment_line:
                (bill_line + payment_line).reconcile()

        # Check if the bill is fully paid
        if total_payment_amount >= bill_amount:
            self._compute_payments_widget_to_reconcile_info()
            if bill_line.full_reconcile_id:
                self.state = 'posted'  # Ensure bill is marked as Paid
        else:
            self._compute_payments_widget_to_reconcile_info()  # Update partial payment status

class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        vehicle =base_line.get('vehicle_id',False)
        extra_fees =base_line.get('extra_fees',0.0)
        vehicle_po = vehicle.vehicle_purchase_order_line_ids
        pov_tax_cost = vehicle_po.tax_cost
        price_unit_after_discount = (base_line['price_unit'] )* (1 - (base_line['discount'] / 100.0))

        taxes_computation = base_line['tax_ids']._get_tax_details(
            price_unit=price_unit_after_discount,
            quantity=base_line['quantity'],
            precision_rounding=base_line['currency_id'].rounding,
            rounding_method=rounding_method or company.tax_calculation_rounding_method,
            product=base_line['product_id'],
            special_mode=base_line['special_mode'],
        )
        rate = base_line['rate']
        tax_details = base_line['tax_details'] = {
            'raw_total_excluded_currency': taxes_computation['total_excluded'],
            'raw_total_excluded': taxes_computation['total_excluded'] / rate if rate else 0.0,
            'raw_total_included_currency': taxes_computation['total_included'],
            'raw_total_included': taxes_computation['total_included'] / rate if rate else 0.0,
            'taxes_data': [],
        }


        if company.tax_calculation_rounding_method == 'round_per_line':
            tax_details['raw_total_excluded'] = company.currency_id.round(tax_details['raw_total_excluded'])
            tax_details['raw_total_included'] = company.currency_id.round(tax_details['raw_total_included'])
        for tax_data in taxes_computation['taxes_data']:
            if extra_fees>0.0:
                tax_data['tax_amount'] = pov_tax_cost
            tax_amount = tax_data['tax_amount'] / rate if rate else 0.0
            base_amount = tax_data['base_amount'] / rate if rate else 0.0
            if company.tax_calculation_rounding_method == 'round_per_line':
                tax_amount = company.currency_id.round(tax_amount)
                base_amount = company.currency_id.round(base_amount)
            tax_details['taxes_data'].append({
                **tax_data,
                'raw_tax_amount_currency': tax_data['tax_amount'],
                'raw_tax_amount': tax_amount,
                'raw_base_amount_currency': tax_data['base_amount'],
                'raw_base_amount': base_amount,
            })
