
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import date
import io
import xlsxwriter
import base64
from datetime import datetime, date, timedelta


class VehiclePurchaseQuotation(models.Model):
    _name = 'vehicle.purchase.quotation'
    _description='Vehicle Purchase Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="name"

    name = fields.Char(string="Name",readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    description = fields.Text( string="Description",required=False)
    expiration_date = fields.Datetime(string="RFQ Expiration Date", default=fields.Datetime.now,required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    vehicle_purchase_id = fields.Many2one('vehicle.purchase', string='PR Request', readonly=True , required=True)
    vehicle_purchase_quotation_line_ids=fields.One2many('vehicle.purchase.quotation.line','vehicle_purchase_quotation_id')
    vehicle_purchase_order_ids=fields.One2many('vehicle.purchase.order','vehicle_purchase_quotation_id')
    total_without_tax = fields.Float( string='Total Without Tax',compute="_compute_total_amount")
    total_include_tax = fields.Float( string='Total Tax',compute="_compute_total_amount")
    total_tax = fields.Float( string='Total Include Tax',compute="_compute_total_amount")
    vehicle_purchase_order_count = fields.Integer(
        string='Vehicle_purchase_quotation_count',
        compute="_compute_vehicle_purchase_quotation_count")
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('under_review', 'Under Review'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancelled', 'Cancelled'), ],
        default='draft',copy=False)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.purchase.quotation.seq')
        return super().create(vals_list)


    def action_under_review(self):
        for rec in self:
            if not rec.vendor_id :
                raise ValidationError(_(f'Please ,Add Vendor to request validate'))
            if any(rec.vehicle_purchase_quotation_line_ids.mapped('unit_price')) <= 0:
                raise ValidationError(_(f'Unit price must be more than 0'))

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

    @api.depends("vehicle_purchase_quotation_line_ids","vehicle_purchase_quotation_line_ids.total_amount", "vehicle_purchase_quotation_line_ids.amount_taxed")
    def _compute_total_amount(self):
        for rfq in self:
            rfq.total_without_tax = sum(rfq.vehicle_purchase_quotation_line_ids.mapped('total_amount'))
            rfq.total_include_tax = sum(rfq.vehicle_purchase_quotation_line_ids.mapped('amount_taxed'))
            rfq.total_tax = rfq.total_include_tax - rfq.total_without_tax

    @api.depends("vehicle_purchase_order_ids")
    def _compute_vehicle_purchase_quotation_count(self):
        for rfq in self:
            rfq.vehicle_purchase_order_count =len(rfq.vehicle_purchase_order_ids)

    def action_create_po(self):
        for rec in self:
            po_vals=self.po_lines_prepare()
            po=self.env['vehicle.purchase.order'].create({
                "company_id":rec.company_id.id,
                "vendor_id":rec.vendor_id.id,
                "description":rec.description,
                "vehicle_purchase_quotation_id":rec.id,
                "vehicle_purchase_order_line_ids":[(0,0,val) for val in po_vals],
            })
            rec.vehicle_purchase_order_ids =[(4,po.id)]
            if rec.vehicle_purchase_order_ids:
                return {
                    'name': 'PO',
                    'type': 'ir.actions.act_window',
                    'res_model': 'vehicle.purchase.order',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rec.vehicle_purchase_order_ids.ids)],
                }
            else:
                raise ValidationError(_("No PO Created for this RFQ!"))


    def po_lines_prepare(self):
        po_lines = []
        for line in self.vehicle_purchase_quotation_line_ids:
            po_lines.append({
                'model_id':line.model_id.id,
                'quantity':line.quantity,
                'color':line.color,
                'vehicle_cost':line.unit_price,
                'tax_ids':[(6,0,line.tax_ids.ids)],
            })
        return po_lines

    def action_view_vehicle_purchase_order(self):
        for rec in self:
            if rec.vehicle_purchase_order_ids:
                return {
                    'name': 'PO',
                    'type': 'ir.actions.act_window',
                    'res_model': 'vehicle.purchase.order',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rec.vehicle_purchase_order_ids.ids)],
                }
            else:
                raise ValidationError(_("No PO Created for this RFQ!"))

class VehiclePurchaseQuotationLine(models.Model):
    _name = 'vehicle.purchase.quotation.line'
    _description='Vehicle Purchase Quotation Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="model_id"


    model_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string='Model',
        required=True)
    quantity = fields.Float(
        string='Quantity',
        required=True)
    color = fields.Char(
        string='Color',
        required=False)
    vehicle_purchase_quotation_id = fields.Many2one(comodel_name='vehicle.purchase.quotation')
    vehicle_purchase_line_id = fields.Many2one(comodel_name='vehicle.purchase.line')
    unit_price = fields.Float(
        string='Unit Price',
        required=True,default=0)
    total_amount = fields.Float(
        string='Total',
        compute="_compute_total_amount")
    tax_ids = fields.Many2many('account.tax', string='Taxes',domain=[('type_tax_use','=','purchase')])
    amount_taxed = fields.Float(
        string='Amount',
        compute="_compute_amount_taxed")

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_(f'Quantity must be more than 0'))
            if rec.quantity > rec.vehicle_purchase_line_id.quantity:
                raise ValidationError(_(f'Quantity must be less than PR Request Quantity'))



    @api.depends('quantity','unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.quantity * rec.unit_price

    @api.depends('quantity','unit_price','total_amount','tax_ids')
    def _compute_amount_taxed(self):
        for rec in self:
            total_line_tax_percentage = sum(rec.tax_ids.mapped('amount'))
            if total_line_tax_percentage :
                rec.amount_taxed= rec.total_amount * (1 + (total_line_tax_percentage / 100))
            else:
                rec.amount_taxed = rec.total_amount

