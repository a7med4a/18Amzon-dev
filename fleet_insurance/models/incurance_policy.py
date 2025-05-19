from email.policy import default

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import date
import io
import xlsxwriter
import base64
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _description = 'Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['policy_lines_ids.plate_number']

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default="New")
    description = fields.Text(string="Description")
    insurance_company = fields.Many2one('res.partner', string="Insurance Company", required=True,
                                        domain=[('company_type', '=', 'company'), ('is_company', '=', True)])
    insurance_type = fields.Selection([
        ('third_party', 'Third Party'),
        ('full', 'Full'),
    ], required=True, string="Insurance Type", default="third_party")
    insurance_number = fields.Char(string="Insurance Number")
    insurance_journal_id = fields.Many2one("account.journal", string="Insurance Journal",domain=[("type", "=", "purchase")])
    refund_insurance_journal_id = fields.Many2one('account.journal', string="Refund Insurance Journal")
    company = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today)
    end_date = fields.Date(string="End Date", required=True)
    policy_lines_ids = fields.One2many('insurance.policy.line', 'policy_id', string="Policy Lines")
    show_create_bill = fields.Boolean(string='show_create_bill')
    show_cancel_button=fields.Boolean(string='show_cancel_button',default=False,compute="_compute_show_cancel_button")
    total_policy_amount = fields.Float(string="Total Policy Amount", compute="_compute_total_policy_amount")
    status = fields.Selection([
        ('quotation', 'Quotation'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], default="quotation", string="Status", tracking=True)
    vendor_bill_id = fields.Many2one('account.move')
    vendor_bill_ids = fields.One2many('account.move', 'insurance_policy_id', string="Vendor Bills")
    note = fields.Html(
        string='Note',
        required=False)
    category_id = fields.Many2many(related='insurance_company.category_id', string="Category", readonly=False)
    account_payable = fields.Many2one(related='insurance_company.property_account_payable_id', string='Account Payable',
                                      readonly=False)
    cancel_insurance_policy_ids = fields.One2many('cancel.insurance.policy', 'insurance_policy_id')
    has_plat_number = fields.Char(string='Plate Number (Search)',compute='_compute_has_plat_chassis_number',store=True)
    has_vin_sn = fields.Char(string='Chassis Number (Search)',compute='_compute_has_plat_chassis_number',store=True)

    @api.depends('policy_lines_ids.plat_number','policy_lines_ids.vin_sn')
    def _compute_has_plat_chassis_number(self):
        for rec in self:
            if rec.policy_lines_ids :
                plate_values = [str(plate) for plate in rec.policy_lines_ids.mapped('plat_number') if plate]
                rec.has_plat_number = ', '.join(plate_values) if plate_values else False
                vin_sn_values = [str(vin) for vin in rec.policy_lines_ids.mapped('vin_sn') if vin]
                rec.has_vin_sn = ', '.join(vin_sn_values) if vin_sn_values else False
            else:
                rec.has_plat_number = ''
                rec.has_vin_sn = ''

    @api.depends('policy_lines_ids', 'policy_lines_ids.bill_status','status')
    def _compute_show_cancel_button(self):
        for rec in self:
            if rec.status in ['under_review', 'approved','expired']:
                if not rec.policy_lines_ids :
                    rec.show_cancel_button = True
                else:
                    rec.show_cancel_button = True
                    for line in rec.policy_lines_ids:
                        if line.bill_status == "true":
                            rec.show_cancel_button = False
                            break
            else :
                rec.show_cancel_button = False


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('insurance.policy') or 'New'

        return super(InsurancePolicy, self).create(vals_list)

    def write(self, values):
        res = super().write(values)
        for rec in self:
            if ('policy_lines_ids' in values) or ('status' in values):
                bill_status_found = any(line.bill_status == "false" for line in rec.policy_lines_ids)
                rec.show_create_bill = bill_status_found
                for line in rec.policy_lines_ids:
                    line.update_insurance_line_status()
            if rec.status in ['under_review', 'approved']:
                for line in rec.policy_lines_ids:
                    line.check_insurance_amount()

        return res

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date <= record.start_date:
                raise ValidationError("End Date must be greater than Start Date!")

    def action_view_insurance_bills(self):
        if self.vendor_bill_ids :
            return {
                'name': 'Vendor Bills',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'domain': [('id','in',self.vendor_bill_ids.ids)],
                'view_mode': 'list,form',
            }
        else :
            raise ValidationError(_("No Bills Created for this Policy!"))

    def action_view_termination_logs(self):
        return {
            'name': 'Termination Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'termination.log',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('police_id', '=', self.id)],
        }

    def action_insurance_credit_note(self):
        config = self.env["insurance.config.settings"].search([('company_id','=',self.company.id)], order="id desc", limit=1)
        if not config:
            raise ValidationError("No configuration found For this company!")
        return {
            'name': 'Credit Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('insurance_policy_id', '=', self.id)],
            'context':{
                'default_journal_id': config.refund_insurance_journal_id.id,
            }
        }

    def action_create_bill(self):
        account_move_obj = self.env['account.move']
        for policy in self:
            if not policy.policy_lines_ids:
                raise ValidationError("No policy lines found!")
            else:
                if policy.status in ['under_review', 'approved']:
                    for line in policy.policy_lines_ids:
                        line.check_insurance_amount()
            if not policy.insurance_company:
                raise ValidationError("No insurance company specified!")
            bill_lines = []
            config = self.env["insurance.config.settings"].search([('company_id','=',policy.company.id)], order="id desc", limit=1)
            if not config:
                raise ValidationError("No configuration found For this company!")
            if policy.policy_lines_ids and config:
                if not policy.vendor_bill_ids or not policy.vendor_bill_ids.filtered(lambda x: x.state == 'draft'):
                    print("policy.policy_lines_ids")
                    for line in policy.policy_lines_ids.filtered(lambda x: x.bill_status == "false"):
                        analytic_data = {line.vehicle_id.analytic_account_id.id: 100}
                        bill_lines.append((0, 0, {
                            'vehicle_id': line.vehicle_id.id,
                            'insurance_policy_line_id': line.id,
                            'account_id': config.insurance_expense_account_id.id,
                            'quantity': 1,
                            'price_unit': line.insurance_amount,
                            'tax_ids': [(6, 0, config.tax_ids.ids)],
                            'analytic_distribution': analytic_data,
                            'deferred_start_date': line.start_date,
                            'deferred_end_date': line.end_date,
                        }))
                    bill_vals = {
                        'move_type': 'in_invoice',
                        'partner_id': policy.insurance_company.id,
                        'insurance_policy_id': policy.id,
                        'is_insurance_bill': True,
                        'journal_id': config.insurance_journal_id.id,
                        'invoice_line_ids': bill_lines,
                        'currency_id': self.env.company.currency_id.id,
                    }
                    bill = account_move_obj.sudo().create(bill_vals)
                    if bill:
                        policy.vendor_bill_ids = [(4, bill.id)]
                        policy.show_create_bill = False
                        for line in policy.policy_lines_ids:
                            line.bill_status = "true"
                    policy.message_post(body=f"Created Bill: {bill.name} for {policy.insurance_company.name}",
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
                else:
                    draft_bills_id=policy.vendor_bill_ids.filtered(lambda line: line.state == "draft")
                    vendor_bill_id=draft_bills_id[0]
                    bill_lines=self.prepare_bill_lines()
                    vendor_bill_id.write({"invoice_line_ids": bill_lines})
                    policy.show_create_bill = False
                    for line in policy.policy_lines_ids:
                        line.bill_status = "true"
                    policy.message_post(
                        body=f"Created Bill: {vendor_bill_id.name} for {policy.insurance_company.name}",
                        subtype_xmlid="mail.mt_comment")
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.move',
                        'res_id': vendor_bill_id.id,
                        'view_mode': 'form',
                        'target': 'current',
                        'context': {

                        },
                    }
        return True


    def prepare_bill_lines(self):
        bill_lines = []
        config = self.env["insurance.config.settings"].search([('company_id','=',self.company.id)], order="id desc", limit=1)
        if not config:
            raise ValidationError("No configuration found For this company!")
        status_false_policy = self.policy_lines_ids.filtered(lambda line: line.bill_status == "false")
        print("status_false_policy",status_false_policy)
        for line in status_false_policy:
            analytic_data = {line.vehicle_id.analytic_account_id.id: 100}
            bill_lines.append((0, 0, {
                'vehicle_id': line.vehicle_id.id,
                'insurance_policy_line_id': line.id,
                'account_id': config.insurance_expense_account_id.id,
                'quantity': 1,
                'price_unit': line.insurance_amount,
                'analytic_distribution': analytic_data,
                'tax_ids': [(6, 0, config.tax_ids.ids)],
                'deferred_start_date': line.start_date,
                'deferred_end_date': line.end_date,
            }))
        return bill_lines

    def action_approve(self):
        for record in self:
            if not record.policy_lines_ids :
                raise ValidationError(_("No policy lines to approve,please add at least one line!"))
            else:
                for police_line in record.policy_lines_ids:
                    police_line.check_insurance_amount()
            record.status = 'approved'

    def action_request_validation(self):
        for record in self:
            if record.policy_lines_ids:
                for police_line in record.policy_lines_ids:
                    police_line.check_insurance_amount()
            record.status = 'under_review'

    def action_terminate(self):
        return {
            'name': 'Terminate Policy',
            'type': 'ir.actions.act_window',
            'res_model': 'insurance.policy.terminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_policy_id': self.id},
        }

    def action_cancel(self):
        for record in self:
            record.status = 'cancelled'

    def action_draft(self):
        for record in self:
            record.status = 'quotation'

    def action_print_report(self):
        for rec in self:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet("Vehicles Report")
            bold_format_header = workbook.add_format({
                'bold': True,
                'bg_color': '#CCCCCC',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 21
            })
            bold_format_arabic = workbook.add_format({
                'bold': True,
                'bg_color': '#CCCCCC',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 13
            })
            bold_format = workbook.add_format({
                'bold': True,
                'bg_color': '#CCCCCC',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 10
            })

            border_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', })
            worksheet.set_column(0, 0, 500)
            worksheet.merge_range(0, 0, 1, 10, "Vehicles Report", bold_format_header)

            worksheet.set_row(4, 25)
            worksheet.set_row(5, 25)
            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 2, 15)
            worksheet.set_column(3, 3, 20)
            worksheet.set_column(4, 4, 15)
            worksheet.set_column(5, 5, 20)
            worksheet.set_column(6, 6, 20)
            worksheet.set_column(7, 7, 15)
            worksheet.set_column(8, 8, 20)
            worksheet.set_column(9, 9, 15)
            worksheet.set_column(10, 9, 15)
            worksheet.set_column(11, 9, 15)

            arabic_headers = [
                "التسلسسل", "الموديل", "الطراز", "رقم الهيكل", "رقم البطاقة الجمركية",
                "الرقم التسلسسلي", "رقم اللوحة", "اللون", "القيمة السوقية", "اسم المالك ", "رقم هوية المالك"
            ]
            headers = [
                "NO", "Model", "Model Year", "Chassis Number", "Card Number",
                "Serial Number", "License Plate", "Color", "Purchase Market Value", "Owner Name", "Owner ID"
            ]

            for col_num, header in enumerate(arabic_headers):
                worksheet.write(4, col_num, header, bold_format_arabic)

            for col_num, header in enumerate(headers):
                worksheet.write(5, col_num, header, bold_format)

            vehicles = rec.policy_lines_ids
            print("vehicles", vehicles)
            row = 6

            for index, vehicle in enumerate(vehicles, start=1):
                worksheet.write(row, 0, index, border_format)
                worksheet.write(row, 1, vehicle.vehicle_id.model_id.name or "", border_format)
                worksheet.write(row, 2, vehicle.vehicle_id.model_year or "", border_format)
                worksheet.write(row, 3, vehicle.vehicle_id.vin_sn or "", border_format)
                worksheet.write(row, 4, vehicle.vehicle_id.card_number or "", border_format)
                worksheet.write(row, 5, vehicle.vehicle_id.serial_number or "", border_format)
                worksheet.write(row, 6, vehicle.vehicle_id.license_plate or "", border_format)
                color_value2 = vehicle.vehicle_id.vehicle_color2 or ""
                if color_value2.startswith('#') and len(color_value2) == 7:
                    color_format = workbook.add_format({'border': 1, 'bg_color': color_value2})
                    worksheet.write(row, 7, "", color_format)
                worksheet.write(row, 8, vehicle.purchase_market_value or 0.0, border_format)
                worksheet.write(row, 9, vehicle.vehicle_id.owner_name or "", border_format)
                worksheet.write(row, 10, vehicle.vehicle_id.owner_id or "", border_format)
                row += 1
            print("vehicles", vehicles)

            workbook.close()
            output.seek(0)
            excel_file = base64.b64encode(output.read())
            output.close()
            print("vehicles", vehicles)

            attachment = self.env['ir.attachment'].create({
                'name': 'Vehicles_Report.xlsx',
                'datas': excel_file,
                'res_model': 'insurance.policy',
                'res_id': rec.id,
                'type': 'binary',
            })

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }

    def action_export_sample(self):
        for rec in self:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet("Policy Lines")

            bold_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
            border_format = workbook.add_format({'border': 1, 'align': 'center'})

            headers = [
                "ID","Chassis Number", "Purchase Market Value",
                "Insurance Rate", "Minimum Insurance Rate", "Start Date",
                "Endurance Rate", "Endurance Customer"
            ]
            worksheet.write_row(0, 0, headers, bold_format)
            worksheet.set_column(0, len(headers) - 1, 25)

            for row, line in enumerate(rec.policy_lines_ids, start=1):
                worksheet.write_row(row, 0, [
                    line.id or 0,
                    line.vin_sn or "N/A",
                    line.purchase_market_value or 0.0,
                    line.insurance_rate or 0.0,
                    line.minimum_insurance_rate or 0.0,
                    str(line.start_date) or "",
                    line.endurance_rate or 0.0,
                    line.endurance_customer or 0.0
                ], border_format)

            workbook.close()
            output.seek(0)

            attachment = self.env['ir.attachment'].create({
                'name': 'Insurance_Policy_Lines.xlsx',
                'datas': base64.b64encode(output.read()),
                'res_model': 'insurance.policy',
                'res_id': rec.id,
                'type': 'binary',
            })
            return {'type': 'ir.actions.act_url', 'url': f'/web/content/{attachment.id}?download=true',
                    'target': 'self'}

    def action_import_vehicle(self):
        self.ensure_one()
        for rec in self :
            if rec.status in ['under_review', 'approved']:
                for line in rec.policy_lines_ids:
                    line.check_insurance_amount()
        return {
            'name': 'Import Vehicle',
            'type': 'ir.actions.act_window',
            'res_model': 'import.vehicle',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_policy_id': self.id,
            },
        }

    def unlink(self):
        for rec in self:
            if rec.status not in  ["cancelled","quotation"]:
                raise ValidationError("Cannot delete insurance policy !")
        return super().unlink()

    @api.depends("policy_lines_ids")
    def _compute_total_policy_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.policy_lines_ids:
                total_amount += line.insurance_amount
            rec.total_policy_amount = total_amount

    def copy(self, default=None):
        default = default or {}
        default['status'] = 'quotation'
        new_policy = super(InsurancePolicy, self).copy(default)
        if new_policy.end_date:
            new_policy.end_date = new_policy.end_date + relativedelta(years=1) + timedelta(days=1)
            new_policy.start_date = new_policy.end_date - relativedelta(years=1)
        return new_policy

    @api.model
    def update_insurance_status(self):
        today = date.today()
        policies_not_expired = self.search([('status', 'not in', ('expired','cancelled'))])
        for rec in policies_not_expired:
            if rec.end_date and rec.end_date < today:
                rec.status = 'expired'
                rec.policy_lines_ids.write({'insurance_status': 'expired'})
            else:
                for line in rec.policy_lines_ids:
                    line.update_insurance_line_status()



class InsurancePolicyLine(models.Model):
    _name = 'insurance.policy.line'
    _rec_name = "vehicle_id"

    policy_id = fields.Many2one('insurance.policy', string="Insurance Policy")
    vehicle_id = fields.Many2one('fleet.vehicle',compute="_compute_vehicle_id", string="Vehicle",default=False,required=True, domain=[("active", "=", True)])
    plat_number = fields.Char(string="Plat number", related='vehicle_id.license_plate', store=True)
    vin_sn = fields.Char(string="Chassis Number", store=True)
    model = fields.Char(string="Model", related='vehicle_id.model_id.name', store=True)
    purchase_market_value = fields.Float(string="Purchase Market Value")
    insurance_rate = fields.Float(string="Insurance Rate", required=True)
    insurance_amount = fields.Float(string="Insurance Amount", compute="_compute_insurance_amount", store=True,default=None)
    minimum_insurance_rate = fields.Float(string="Minimum Insurance Rate", required=True,default=None)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", related="policy_id.end_date", required=True)
    endurance_rate = fields.Float(string="Endurance Rate")
    endurance_customer = fields.Float(string="Endurance Customer")
    daily_rate = fields.Float(string="Daily Rate", compute="_compute_daily_rate")
    insurance_duration = fields.Float(compute="_compute_insurance_duration")
    bill_status = fields.Selection([
        ('false', 'False'),
        ('true', 'True'), ], default="false", readonly=True, string="Bill Status")
    insurance_status = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired')
    ], string="Insurance Status", default="draft",copy=False, required=True, store=True)

    @api.depends('vin_sn')
    def _compute_vehicle_id(self):
        for rec in self:
            rec.vehicle_id = self.env['fleet.vehicle'].search([('vin_sn', '=', rec.vin_sn)], limit=1)
    @api.constrains('start_date')
    def _check_start_date(self):
        for record in self:
            if record.start_date > record.policy_id.end_date or record.start_date < record.policy_id.start_date:
                raise ValidationError(
                    "Start Date in Policy Lines must be greater than or equal to the Start Date in the Insurance Policy!"
                )

    def check_insurance_amount(self):
        """Validate that all required insurance-related fields have values greater than zero."""
        fields_to_check = {
            'insurance_amount': _("Insurance Amount must be greater than 0!"),
            'minimum_insurance_rate': _("Insurance Amount Rate must be greater than 0!"),
            'purchase_market_value': _("Purchase Market Value must be greater than 0!"),
            'insurance_rate': _("Insurance Rate must be greater than 0!"),
            'endurance_rate': _("Endurance Rate must be greater than 0!"),
            'endurance_customer': _("Endurance Customer must be greater than 0!"),
        }
        for record in self:
            for field, error_msg in fields_to_check.items():
                if getattr(record, field, 0) <= 0:
                    raise ValidationError(error_msg)


    @api.constrains('vehicle_id')
    def _check_vehicle_id(self):
        for record in self:
            insurance_policy = self.env["insurance.policy.line"].search(
                [("vehicle_id", "=", record.vehicle_id.id), ("insurance_status", "in", ("draft", "running")), ])
            if len(insurance_policy) > 1:
                raise ValidationError(
                    _(f"Vehicle already has an active insurance policy number( {insurance_policy[0].policy_id.name} )!")
                )

    @api.depends('purchase_market_value', 'insurance_rate', 'minimum_insurance_rate')
    def _compute_insurance_amount(self):
        for record in self:
            calculated_amount = record.purchase_market_value * (record.insurance_rate)
            record.insurance_amount = max(calculated_amount, record.minimum_insurance_rate)

    @api.depends('start_date', 'end_date', 'minimum_insurance_rate', 'insurance_amount')
    def _compute_daily_rate(self):
        for record in self:
            if record.start_date and record.end_date:
                days = (record.end_date - record.start_date).days
                record.daily_rate = record.insurance_amount / days if days > 0 else 0
            else:
                record.daily_rate = 0
    @api.depends('start_date', 'end_date')
    def _compute_insurance_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                days = (record.end_date - record.start_date).days
                record.insurance_duration = days
            else:
                record.insurance_duration = 0

    @api.model
    def update_insurance_line_status(self):
        today = date.today()
        policy_lines = self.search([])
        for rec in policy_lines:
            if rec.end_date and rec.end_date < today:
                rec.insurance_status = 'expired'
            elif rec.start_date and rec.insurance_status == 'draft' and rec.start_date <= today:
                rec.insurance_status = 'running'


    def unlink(self):
        for rec in self:
            if rec.bill_status == "true":
                raise ValidationError("Cannot delete a True Bill status insurance policy line!")
        return super().unlink()


class CancelInsurancePolicy(models.TransientModel):
    _name = "cancel.insurance.policy"
    _description = "Cancel Insurance Policy"

    from_month = fields.Integer(string='From',required=True)
    to_month = fields.Integer(string='To',required=True)
    percentage = fields.Float(string='Percentage(%)',required=True)
    insurance_policy_id = fields.Many2one('insurance.policy', string="Insurance Policy", required=True)

    @api.constrains('from_month', 'to_month', 'percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.from_month > rec.to_month:
                raise ValidationError("From Month must be less than To Month!")
            elif rec.from_month < 1 or rec.to_month < 1:
                raise ValidationError("From Month and To Month must be greater than 0!")
            elif rec.percentage < 0:
                raise ValidationError("Percentage must be greater than 0!")