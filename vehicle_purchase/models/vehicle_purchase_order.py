
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

from datetime import date
import io
import xlsxwriter
import base64
from datetime import datetime, date, timedelta

class VehiclePurchaseOrder(models.Model):
    _name = 'vehicle.purchase.order'
    _description='Vehicle Purchase Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="name"

    name = fields.Char(string="Name",readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    description = fields.Text( string="Description",required=False)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    payment_method = fields.Selection(
        string='Payment Method',
        selection=[('cash', 'Cash'),
                   ('settlement', 'Settlement'), ],
        required=False, )
    vehicle_purchase_quotation_id = fields.Many2one('vehicle.purchase.quotation', string='PO')
    vehicle_purchase_order_line_ids=fields.One2many('vehicle.purchase.order.line','vehicle_purchase_order_id')
    installment_board_ids=fields.One2many('installments.board','vehicle_purchase_order_id')
    account_payment_ids=fields.One2many('account.payment','vehicle_po_id')
    account_payment_count=fields.Integer(compute="_compute_account_payment_count")
    total_without_tax = fields.Float( string='UnTaxed Amount',compute="_compute_total_without_tax")
    tax_15 = fields.Float( string='Tax 15%',compute="_compute_tax_15")
    total_include_tax = fields.Float( string='Total Tax')
    total_vehicle_tax = fields.Float( string='Total Vehicles Cost',compute="_compute_total_vehicle_tax")
    total_advanced_payment = fields.Float( string='Total Advanced Payment',compute="_compute_total_advanced_payment")
    total_financial_amount = fields.Float( string='Total Financing Amount',compute="_compute_total_financial_amount")
    total_interest_cost = fields.Float( string='Total interest Cost',compute="_compute_total_interest_cost")
    total_installment_cost = fields.Float( string='Total installment Cost ',compute="_compute_total_installment_cost")
    number_of_installment = fields.Integer( string='Number of Installment')
    installment_cost = fields.Integer( string='Installment Cost',compute="_compute_installment_cost")
    date = fields.Date(string='Date',required=False)
    is_advanced_payment_paid = fields.Boolean(string='Advanced Payment Paid',default=False)
    vehicle_ids=fields.One2many('fleet.vehicle','po_id')
    bill_id = fields.Many2one(comodel_name="account.move", string="Bill", required=False, )
    vehicle_count=fields.Integer(compute="_compute_vehicle_count")
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('under_review', 'Under Review'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancelled', 'Cancelled'), ],
        default='draft',copy=False)




    installment_status = fields.Selection(
            selection=[
                ('not_paid', 'Not Paid'),
                ('partial_paid', 'Partial Paid'),
                ('paid', 'Paid')
            ],
            string="Installment Status",
            compute="_compute_installment_status",
            store=False
        )

    installment_status_class = fields.Char(compute="_compute_installment_status_helper")
    installment_status_tooltip = fields.Char(compute="_compute_installment_status_helper")

    def _compute_installment_status(self):
        for rec in self:
            paid = rec.installment_board_ids.filtered(lambda i: i.state != 'paid')
            not_paid = rec.installment_board_ids.filtered(lambda i: i.state != 'not_paid')
            partial_paid = rec.installment_board_ids.filtered(lambda i: i.state != 'partial_paid')
            if not_paid and not paid and not partial_paid:
                rec.installment_status = 'not_paid'
            elif paid and not not_paid and not partial_paid:
                rec.installment_status = 'paid'
            elif paid and not_paid or partial_paid:
                rec.installment_status = 'partial_paid'
            else:
                rec.installment_status = ''

    @api.depends('installment_status')
    def _compute_installment_status_helper(self):
            for rec in self:
                if rec.installment_status == 'not_paid':
                    rec.installment_status_class = 'bg-danger text-white'
                    rec.installment_status_tooltip = 'No payments made yet'
                elif rec.installment_status == 'partial_paid':
                    rec.installment_status_class = 'bg-warning text-dark'
                    rec.installment_status_tooltip = 'Some installments are still unpaid'
                elif rec.installment_status == 'paid':
                    rec.installment_status_class = 'bg-success text-white'
                    rec.installment_status_tooltip = 'All installments are fully paid'
                else:
                    rec.installment_status_class = 'bg-secondary text-white'
                    rec.installment_status_tooltip = 'Installment status unknown'


    def action_export_installments(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Installments')

        sheet.write(0, 0, 'ID(Not Change)')
        sheet.write(0, 1, 'Date')
        sheet.write(0, 2, 'Amount')

        for idx, line in enumerate(self.installment_board_ids, start=1):
            sheet.write(idx, 0, line.id or '')
            sheet.write(idx, 1, str(line.date or ''))
            sheet.write(idx, 2, line.amount or 0.0)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'installments.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': 'vehicle.purchase.order',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.purchase.order.seq')
        return super().create(vals_list)

    def action_under_review(self):
        for rec in self:
            if not rec.vendor_id :
                raise ValidationError(_(f'Please ,Add Vendor to request validate'))
            rec.state='under_review'
    def action_confirm(self):
        for rec in self:
            rec.state='confirmed'
    def action_refuse(self):
        for rec in self:
            rec.state='refused'
    def action_cancel(self):
        for rec in self:
            rec.state='cancelled'
    def action_reset_draft(self):
        for rec in self:
            rec.state='draft'

    @api.depends("vehicle_purchase_order_line_ids", "vehicle_purchase_order_line_ids.admin_fees","vehicle_purchase_order_line_ids.quantity",
                 "vehicle_purchase_order_line_ids.vehicle_cost", "vehicle_purchase_order_line_ids.shipping_cost",
                 "vehicle_purchase_order_line_ids.plate_fees", "vehicle_purchase_order_line_ids.insurance_cost")
    def _compute_total_without_tax(self):
        for po in self:
            total_without_tax = 0
            for line in po.vehicle_purchase_order_line_ids:
                total_without_tax += (line.admin_fees + line.vehicle_cost + line.shipping_cost + line.plate_fees + line.insurance_cost)*line.quantity
            po.total_without_tax = total_without_tax

    @api.depends("vehicle_purchase_order_line_ids", "vehicle_purchase_order_line_ids.tax_cost","vehicle_purchase_order_line_ids.quantity",)
    def _compute_tax_15(self):
        for po in self:
            tax_15 = 0
            for line in po.vehicle_purchase_order_line_ids:
                tax_15 += line.tax_cost * line.quantity
            po.tax_15 = tax_15

    @api.depends("total_without_tax", "total_without_tax",)
    def _compute_total_vehicle_tax(self):
        for po in self:
            po.total_vehicle_tax = po.total_without_tax + po.tax_15

    @api.depends("vehicle_purchase_order_line_ids", "vehicle_purchase_order_line_ids.financing_amount_per_model")
    def _compute_total_financial_amount(self):
        for po in self:
            po.total_financial_amount = sum(po.vehicle_purchase_order_line_ids.mapped('financing_amount_per_model'))

    @api.depends("vehicle_purchase_order_line_ids", "vehicle_purchase_order_line_ids.advanced_payment_per_model")
    def _compute_total_advanced_payment(self):
        for po in self:
            po.total_advanced_payment = sum(po.vehicle_purchase_order_line_ids.mapped('advanced_payment_per_model'))

    @api.depends("vehicle_purchase_order_line_ids", "vehicle_purchase_order_line_ids.interest_cost_per_model")
    def _compute_total_interest_cost(self):
        for po in self:
            po.total_interest_cost = sum(po.vehicle_purchase_order_line_ids.mapped('interest_cost_per_model'))

    @api.depends("total_interest_cost", "total_financial_amount")
    def _compute_total_installment_cost(self):
        for po in self:
            po.total_installment_cost = po.total_interest_cost + po.total_financial_amount

    @api.depends("total_installment_cost", "number_of_installment")
    def _compute_installment_cost(self):
        for po in self:
            if po.number_of_installment > 0:
                po.installment_cost = po.total_installment_cost / po.number_of_installment
            else:
                po.installment_cost = 0
    
    @api.depends("account_payment_ids")
    def _compute_account_payment_count(self):
        for po in self:
            po.account_payment_count = len(po.account_payment_ids)

    @api.depends("vehicle_ids")
    def _compute_vehicle_count(self):
        for po in self:
            po.vehicle_count = len(po.vehicle_ids)

    def action_create_installment_board(self):
        for rec in self:
            if  rec.number_of_installment <1 or not rec.date :
                raise ValidationError(_(f'Date and number_of_installment is required'))
            first_installment = rec.date
            for installment in range(1, rec.number_of_installment + 1):
                self.env['installments.board'].create({
                    'amount': rec.installment_cost,
                    'date': first_installment + relativedelta(months=installment),
                    'vehicle_purchase_order_id': rec.id
                })

    def action_create_bill(self):
        account_move_obj = self.env['account.move']
        for po in self:
            if not po.vehicle_ids:
                raise ValidationError("No vehicle found!")
            config = self.env["bill.config.settings"].sudo().search([('is_bill','=',True)], order="id desc", limit=1)

            if not config:
                raise ValidationError("No bill configuration found!")
            bill_lines = []
            for vehicle in po.vehicle_ids:
                vehicle_po = vehicle.vehicle_purchase_order_line_ids
                # price = 1 + 2 + 3 + 4 + 5 + 9
                price = vehicle_po.vehicle_cost+vehicle_po.shipping_cost+vehicle_po.admin_fees+vehicle_po.insurance_cost +vehicle_po.plate_fees+vehicle_po.interest_cost
                extra_fees = vehicle_po.plate_fees+vehicle_po.insurance_cost
                bill_lines.append((0, 0, {
                    'vehicle_id': vehicle.id,
                    'account_id': config.account_id.id,
                    'quantity': 1,
                    'price_unit': price,
                    'extra_fees': extra_fees,
                    'tax_ids': [(6, 0, config.tax_ids.ids)],
                }))

            bill_vals = {
                'move_type': 'in_invoice',
                'partner_id': po.vendor_id.id,
                'journal_id': config.journal_id.id,
                'invoice_line_ids': bill_lines,
                'amount_tax': po.total_vehicle_tax ,
                'currency_id': self.env.company.currency_id.id,
                'vpo_id': self.id,
            }
            bill = account_move_obj.sudo().create(bill_vals)
            po.bill_id = bill.id

            po.message_post(
                body=f"Created Bill: {po.vendor_id.name} for PO# {po.name}",
                subtype_xmlid="mail.mt_comment")
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': bill.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {

                },
            }

    def action_create_advance_payment(self):
            return {
                'type': 'ir.actions.act_window',
                'name': _('Pay'),
                'res_model': 'vehicle.purchase.payment.register',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                'default_pay_type': 'advance',
                'default_amount': self.total_advanced_payment,
            },
            }

    def action_create_installment_payment(self):
        for rec in self:
            if not rec.is_advanced_payment_paid and rec.total_advanced_payment != 0:
                 raise ValidationError(_(f'Calculate Advanced payment first'))
            return {
                'type': 'ir.actions.act_window',
                'name': _('Pay'),
                'res_model': 'vehicle.purchase.payment.register',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                'default_pay_type': 'installment',
            },
            }

    def action_create_vehicle(self):
        for rec in self:
            for line in rec.vehicle_purchase_order_line_ids:
                quantity=line.quantity
                while quantity > 0 :
                    vehicle_id = self.env['fleet.vehicle'].create({'po_id': rec.id, 'model_id': line.model_id.id,
                                                                   'vehicle_purchase_order_line_ids': [(6, 0, [line.id])],
                                                                   'state_id': self.env.ref('fleet_status.fleet_vehicle_state_under_preparation').id})
                    for vehicle in vehicle_id.vehicle_purchase_order_line_ids :
                        vehicle.vehicle_id = vehicle_id.id
                    rec.vehicle_ids = [(4, vehicle_id.id)]
                    quantity -=1

    def action_view_vehicle(self):
        for rec in self:
            action = self.env['ir.actions.actions']._for_xml_id('fleet.fleet_vehicle_action')
            action['domain']=[('po_id','=',rec.id)]
            return action

    def action_view_payments(self):
        for rec in self:
            action = self.env['ir.actions.actions']._for_xml_id('account.action_account_payments_payable')
            action['domain']=[('vehicle_po_id','=',rec.id)]
            return action

    def action_view_bills(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': rec.bill_id.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {

                },
            }

class VehiclePurchaseOrderLine(models.Model):
    _name = 'vehicle.purchase.order.line'
    _description='Vehicle Purchase Order Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="model_id"


    model_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string='Model',
        required=True,readonly=True)
    quantity = fields.Float(
        string='Quantity',
        required=True)
    color = fields.Char(
        string='Color',
        required=False)
    vehicle_purchase_order_id = fields.Many2one(comodel_name='vehicle.purchase.order')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle')
    vehicle_cost = fields.Float(string='Vehicle Cost',readonly=True)
    shipping_cost = fields.Float(string='Shipping Cost')
    admin_fees = fields.Float(string='Admin fees')
    plate_fees = fields.Float(string='Plate Fees')
    insurance_cost = fields.Float(string='Insurance Cost')
    tax_ids = fields.Many2many('account.tax', string='Taxes',domain=[('type_tax_use','=','purchase')])
    tax_cost = fields.Float(string='Tax Cost',compute="_compute_tax_cost")
    total = fields.Float(string='Total',compute="_compute_total_per_model")
    total_per_model = fields.Float(string='Total Per Model',compute="_compute_total_per_model")
    advanced_payment_per_model = fields.Float(string='Advanced Payment Per Model')
    advanced_payment = fields.Float(string='Advanced Payment',compute="_compute_advanced_payment")
    financing_amount_per_model = fields.Float(string='Financing Amount Per Model',compute="_compute_financing_amount_per_model")
    financing_amount = fields.Float(string='Financing Amount ',compute="_compute_financing_amount_per_model")
    interest_rate = fields.Float(string='Interest(%)')
    interest_cost_per_model = fields.Float(string='Interest Cost Per Model',compute="_compute_interest_cost_per_model")
    interest_cost = fields.Float(string='Interest Cost',compute="_compute_interest_cost_per_model")
    ownership_value = fields.Float(string='Ownership Value')


    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_(f'Quantity must be more than 0'))



    # @api.depends('quantity','unit_price')
    # def _compute_total_amount(self):
    #     for rec in self:
    #         rec.total_amount = rec.quantity * rec.unit_price
    #
    @api.depends('shipping_cost','vehicle_cost','admin_fees','insurance_cost','tax_ids')
    def _compute_tax_cost(self):
        for rec in self:
            total_line_tax_percentage = sum(rec.tax_ids.mapped('amount'))
            if total_line_tax_percentage :
                rec.tax_cost= (rec.shipping_cost + rec.vehicle_cost + rec.admin_fees + rec.insurance_cost) * (total_line_tax_percentage / 100)
            else:
                rec.tax_cost = 0

    @api.depends('quantity', 'shipping_cost', 'vehicle_cost', 'admin_fees', 'insurance_cost', 'tax_cost', 'plate_fees')
    def _compute_total_per_model(self):
        for rec in self:
            rec.total_per_model = rec.quantity * (rec.shipping_cost + rec.vehicle_cost + rec.admin_fees + rec.insurance_cost+rec.plate_fees+rec.tax_cost)
            rec.total = rec.shipping_cost + rec.vehicle_cost + rec.admin_fees + rec.insurance_cost+rec.plate_fees+rec.tax_cost

    @api.depends('quantity', 'advanced_payment_per_model')
    def _compute_advanced_payment(self):
        for rec in self:
            rec.advanced_payment = rec.advanced_payment_per_model / rec.quantity

    @api.depends('total_per_model', 'advanced_payment_per_model')
    def _compute_financing_amount_per_model(self):
        for rec in self:
            rec.financing_amount_per_model = rec.total_per_model - rec.advanced_payment_per_model
            rec.financing_amount = rec.financing_amount_per_model / rec.quantity

    @api.depends('financing_amount_per_model', 'interest_rate')
    def _compute_interest_cost_per_model(self):
        for rec in self:
            rec.interest_cost_per_model = rec.financing_amount_per_model * rec.interest_rate/100.0
            rec.interest_cost= rec.interest_cost_per_model / rec.quantity

class InstallmentBoard(models.Model):
    _name = 'installments.board'
    _description='InstallmentBoard'

    date = fields.Date(
        string='Date',
        required=False)
    amount = fields.Float(string='Amount')
    paid_amount = fields.Float(string='Paid Amount')
    remaining_amount = fields.Float(string='Remaining Amount',compute="_compute_remaining_amount",store=True)
    state = fields.Selection(
        string='State',
        selection=[('not_paid', 'Not Paid'),
                   ('paid', 'Paid'),('partial_paid', ' Partial Paid'), ],default='not_paid',compute="_compute_state",store=True)
    vehicle_purchase_order_id = fields.Many2one(comodel_name='vehicle.purchase.order')

    order_name = fields.Char(related='vehicle_purchase_order_id.name', string='Order Reference', store=True)
    vendor_id = fields.Many2one(related='vehicle_purchase_order_id.vendor_id', string='Customer', store=True)


    @api.depends('amount','paid_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.amount - rec.paid_amount
    @api.depends('amount','paid_amount','remaining_amount')
    def _compute_state(self):
        for rec in self:
            if rec.remaining_amount == 0 :
                rec.state = 'paid'
            elif rec.paid_amount > 0 and rec.remaining_amount > 0 :
                rec.state = 'partial_paid'
            else:
                rec.state = 'not_paid'


    @api.constrains('amount')
    def _check_editable_and_total_validation(self):
        if self._context.get('create_from_btn'):
            return
        for rec in self:
            if rec.paid_amount > 0 and rec.amount != rec._origin.amount:
                raise ValidationError("You cannot modify this installment amount because it has already been partially or fully paid.")

        if self and self[0].vehicle_purchase_order_id:
            order = self[0].vehicle_purchase_order_id
            all_installments = self.env['installments.board'].search([
                ('vehicle_purchase_order_id', '=', order.id)
            ])
            total = sum(line.amount for line in all_installments)
            expected = order.number_of_installment * order.installment_cost

            if abs(total - expected) > 0.01:
                raise ValidationError(
                    f"Total of installments ({total:.2f}) must equal original amount: {expected:.2f}"
                )