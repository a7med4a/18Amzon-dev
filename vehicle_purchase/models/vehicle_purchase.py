
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import date
import io
import xlsxwriter
import base64
from datetime import datetime, date, timedelta


class VehiclePurchase(models.Model):
    _name = 'vehicle.purchase'
    _description='Vehicle Purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="name"

    name = fields.Char(string="Name",readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    description = fields.Text( string="Description",required=False)
    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now, readonly=True)
    request_by_id = fields.Many2one('res.users', string='Requested By', readonly=True,default=lambda self: self.env.user.id)
    expected_delivery_date = fields.Datetime(string="Expected Delivery Date", default=fields.Datetime.now)
    vehicle_purchase_line_ids=fields.One2many('vehicle.purchase.line','vehicle_purchase_id')
    vehicle_purchase_quotation_ids=fields.One2many('vehicle.purchase.quotation','vehicle_purchase_id')
    vehicle_purchase_quotation_count=fields.Integer(compute="_compute_vehicle_purchase_quotation_count")
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('under_review', 'Under Review'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancelled', 'Cancelled'), ],
        default='draft',copy=False )



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.purchase.seq')
        return super().create(vals_list)


    def action_under_review(self):
        for rec in self:
            if not rec.vehicle_purchase_line_ids :
                raise ValidationError(_("Please add line to request validation!"))
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

    def action_create_RFQ(self):
        for rec in self :
            rfq_vals=self.rfq_lines_prepare()
            rfq=self.env['vehicle.purchase.quotation'].create({
                "company_id":rec.company_id.id,
                "description":rec.description,
                "vehicle_purchase_id":rec.id,
                "vehicle_purchase_quotation_line_ids":[(0,0,val) for val in rfq_vals],
            })
            print(rfq)
            rec.vehicle_purchase_quotation_ids =[(4,rfq.id)]
            if rec.vehicle_purchase_quotation_ids:
                return {
                    'name': 'RFQ',
                    'type': 'ir.actions.act_window',
                    'res_model': 'vehicle.purchase.quotation',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rec.vehicle_purchase_quotation_ids.ids)],
                }
            else:
                raise ValidationError(_("No RFQ Created for this PR Request!"))
            
    def rfq_lines_prepare(self):
        for pr in self:
            vals=[]
            for line in pr.vehicle_purchase_line_ids :
                vals.append({
                    "model_id": line.model_id.id,
                    "quantity": line.quantity,
                    "color": line.color,
                    "vehicle_purchase_line_id": line.id,
                })
            return vals

    def action_view_RFQ(self):
        for rec in self :
            if rec.vehicle_purchase_quotation_ids:
                return {
                    'name': 'RFQ',
                    'type': 'ir.actions.act_window',
                    'res_model': 'vehicle.purchase.quotation',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rec.vehicle_purchase_quotation_ids.ids)],
                }
            else:
                raise ValidationError(_("No RFQ Created for this PR Request!"))
    @api.depends("vehicle_purchase_quotation_ids")
    def _compute_vehicle_purchase_quotation_count(self):
        for rec in self :
            if rec.vehicle_purchase_quotation_ids :
                rec.vehicle_purchase_quotation_count=len(rec.vehicle_purchase_quotation_ids)
            else:
                rec.vehicle_purchase_quotation_count = 0

class VehiclePurchaseLine(models.Model):
    _name = 'vehicle.purchase.line'
    _description='Vehicle Purchase Line'
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
    branch_ids = fields.Many2many(
        comodel_name='res.branch',
        string='Branches')
    vehicle_purchase_id = fields.Many2one(comodel_name='vehicle.purchase')


    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_(f'Quantity must be more than 0'))

