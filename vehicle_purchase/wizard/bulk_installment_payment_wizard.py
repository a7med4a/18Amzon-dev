from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BulkInstallmentPaymentWizard(models.TransientModel):
    _name = 'bulk.installment.payment.wizard'
    _description = 'Bulk Installment Payment Wizard'

    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    payment_lines = fields.One2many('bulk.installment.payment.line', 'wizard_id', string="Payment Lines")



    def action_pay(self):
        for line in self.payment_lines:
            po = line.purchase_order_id
            amount_to_pay = line.amount

            if not po or amount_to_pay <= 0:
                continue

            paid = 0
            for installment in po.installment_board_ids.filtered(lambda i: i.state != 'paid'):
                if paid >= amount_to_pay:
                    break
                remaining = installment.remaining_amount
                to_pay = min(remaining, amount_to_pay - paid)
                installment.paid_amount += to_pay
                paid += to_pay
                installment._compute_state()
            payment = self.env['account.payment'].create({
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': po.vendor_id.id,
                'journal_id': self.journal_id.id,
                'amount': amount_to_pay,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'memo': f"Bulk payment for {po.name}",
                'company_id': po.company_id.id,
                'date': fields.Date.today(),
                'state': 'draft',
                'vehicle_po_id': po.id,
            })

            payment.action_validate()


class BulkInstallmentPaymentLine(models.TransientModel):
    _name = 'bulk.installment.payment.line'
    _description = 'Bulk Installment Payment Line'

    wizard_id = fields.Many2one('bulk.installment.payment.wizard', required=True, ondelete="cascade")
    purchase_order_id = fields.Many2one('vehicle.purchase.order', string="PO", required=True)
    amount = fields.Float(string="Amount to Pay", required=True)

    allowed_po_ids = fields.Many2many(comodel_name="vehicle.purchase.order",compute="_cal_allowed_po_ids" )

    remaining_amount = fields.Float(string='PO Total Remaining', compute="_compute_remaining_amount",)

    @api.constrains('amount')
    def _check_editable_and_total_validation(self):
        for rec in self:
            if rec.amount > 0 and rec.purchase_order_id and rec.amount> rec.remaining_amount:
                raise ValidationError(f"You cannot set amount more than Remaining amount in po#{rec.purchase_order_id.name}.")


    @api.depends('purchase_order_id')
    def _compute_remaining_amount(self):
        for line in self:
            instalments = self.env['installments.board'].sudo().search(
                [('state', '!=', 'paid'),('vehicle_purchase_order_id', '=', line.purchase_order_id.id)])
            line.remaining_amount = sum(instalments.mapped('remaining_amount'))

    @api.depends('wizard_id')
    def _cal_allowed_po_ids(self):
        for line in self:
            po_ids =[]
            print("line ==> ",line)
            if line.wizard_id and line.wizard_id.partner_id:
                instalments = self.env['installments.board'].sudo().search([('vendor_id','=',line.wizard_id.partner_id.id),('state','!=','paid'),('vehicle_purchase_order_id.state','=','confirmed')])
                po_ids = instalments.mapped('vehicle_purchase_order_id').ids
                print("instalments ==> ", instalments)
                print("po_ids ==> ", po_ids)
            line.allowed_po_ids=[(6,0,po_ids)]
        pass
