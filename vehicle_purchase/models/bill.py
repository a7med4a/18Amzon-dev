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

    vpo_id = fields.Many2one(comodel_name="vehicle.purchase.order", string="Vehicle Purchase Order", required=False)
    is_vehicle_purchase = fields.Boolean(string="Is Vehicle Purchase Order", default=False)

    def action_register_payment(self):
        if self.is_vehicle_purchase:
            raise ValidationError("You can't register payment for vehicle purchase order")
        res = super(AccountMove, self).action_register_payment()
        return res

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        result = super(AccountMove, self)._prepare_product_base_line_for_taxes_computation(product_line)
        result['extra_fees'] = product_line.extra_fees
        return result

    def action_post(self):
        """Override the confirm action to auto-reconcile advance payments."""
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type == 'in_invoice' and move.vpo_id:
                advance_payments = self.env['account.payment'].search([
                    ('vehicle_po_id', '=', self.vpo_id.id),
                    ('partner_id', '=', self.partner_id.id),
                    ('reconciled_bill_ids', '=', False),
                    ('state', '=', 'paid'),
                ])
                move.reconcile_advance_payments(advance_payments)
                move._compute_amount()
        return res

    def reconcile_advance_payments(self,advance_payments):
        """Reconcile advance payments with the current invoice."""

        print("advance_payments ==> ", advance_payments)

        if advance_payments:
            invoice_line = self.line_ids.filtered(
                lambda line: line.account_id.account_type == 'liability_payable' and not line.reconciled
            )
            print("invoice_line ==> ", invoice_line)

            for payment in advance_payments:
                payment_lines = payment.move_id.line_ids
                print("payment_lines ==> ", payment_lines)

                outstanding_line = payment_lines.filtered(
                    lambda line: line.account_id.account_type == 'liability_payable' and not line.reconciled
                )
                print("outstanding_line ==> ", outstanding_line)

                if outstanding_line and invoice_line:
                    print("Outstanding Line Balance ==> ", outstanding_line.balance)
                    print("Invoice Line Balance ==> ", invoice_line.balance)
                    print("Outstanding Line Currency ==> ", outstanding_line.currency_id.name)
                    print("Invoice Line Currency ==> ", invoice_line.currency_id.name)

                    if outstanding_line.currency_id and invoice_line.currency_id and \
                            outstanding_line.currency_id.id != invoice_line.currency_id.id:
                        print("Currency mismatch detected!")
                        continue

                    reconcile_amount = min(abs(outstanding_line.balance), abs(invoice_line.balance))
                    print("Reconcile Amount ==> ", reconcile_amount)

                    try:
                        # Create partial reconciliation
                        partial_reconcile = self.env['account.partial.reconcile'].create({
                            'debit_move_id': outstanding_line.id if outstanding_line.balance > 0 else invoice_line.id,
                            'credit_move_id': outstanding_line.id if outstanding_line.balance < 0 else invoice_line.id,
                            'amount': reconcile_amount,
                            'debit_amount_currency': reconcile_amount if outstanding_line.balance > 0 else (
                                reconcile_amount if invoice_line.balance > 0 else 0.0),
                            'credit_amount_currency': reconcile_amount if invoice_line.balance < 0 else (
                                reconcile_amount if outstanding_line.balance < 0 else 0.0),
                            'debit_currency_id': outstanding_line.currency_id.id or self.currency_id.id,
                            'credit_currency_id': invoice_line.currency_id.id or self.currency_id.id,
                        })
                        print("Partial Reconciliation Created ==> ", partial_reconcile)

                        # Link the payment to the invoice
                        self.payment_ids = [(4, payment.id)]
                        payment.reconciled_invoice_ids = [(4, self.id)]
                        # Update matched_payment_ids to ensure the Payments button appears
                        self.matched_payment_ids = [(4, payment.id)]
                        print("Payment Linked to Invoice and Matched ==> ", payment.name)

                    except Exception as e:
                        print("Reconciliation Failed: ", str(e))

            print("Reconciliation Done *********")

class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        vehicle = base_line.get('vehicle_id', False)
        extra_fees = base_line.get('extra_fees', 0.0)
        vehicle_po = vehicle.vehicle_purchase_order_line_ids
        pov_tax_cost = vehicle_po.tax_cost
        price_unit_after_discount = (base_line['price_unit']) * (1 - (base_line['discount'] / 100.0))

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
            if extra_fees > 0.0:
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