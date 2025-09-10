# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.account.models import company
from odoo.exceptions import UserError, ValidationError
import io
import xlsxwriter
import base64


class ContractFinesDiscountWiz(models.TransientModel):
    _name = 'branch.transaction.report'
    _description = 'Branch Transaction Report'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    company_id = fields.Many2one(
        'res.company', string='Company', domain=lambda self: [('id', 'in', self.env.companies.ids)], required=True)
    area_id = fields.Many2one(
        'res.area', string='Area')
    branch_ids = fields.Many2many('res.branch', string='Branch')
    branch_domain = fields.Binary(
        string="Route Branch domain", compute="_compute_branch_domain")

    include_draft_cancel = fields.Boolean('Include Draft and Cancel Payment')

    @api.depends("area_id")
    def _compute_branch_domain(self):
        for rec in self:
            if rec.area_id:
                domain = [
                    ('area_id', '=', rec.area_id.id), ('id', 'in', self.env.user.branch_ids.ids), ('branch_type', '=', 'rental')]
            else:
                domain = [('id', '=', False)]
            rec.branch_domain = domain

    def get_payment_type_totals(self, matched_transactions):
        return {
            dict(matched_transactions._fields['payment_type_selection'].selection).get(payment_type) or 'غير معين':
            sum(matched_transactions.filtered(
                lambda t: t.payment_type_selection == payment_type).mapped('amount'))
            for payment_type in matched_transactions.mapped('payment_type_selection')
        }

    def get_totals_dict(self, matched_transactions):
        total_received = sum(abs(t.filtered(
            lambda t: t.payment_type == 'inbound').amount_company_currency_signed)for t in matched_transactions)
        total_sent = sum(abs(t.filtered(
            lambda t: t.payment_type == 'outbound').amount_company_currency_signed)for t in matched_transactions)
        total_bank_amount = sum(abs(t.filtered(
            lambda t: t.journal_id.type == 'bank').amount_company_currency_signed)for t in matched_transactions)
        total_cash_amount = sum(abs(t.filtered(
            lambda t: t.journal_id.type == 'cash').amount_company_currency_signed)for t in matched_transactions)

        return {
            'total_received': total_received,
            'total_sent': total_sent,
            'net': total_received - total_sent,
            'total_bank_amount': total_bank_amount,
            'total_cash_amount': total_cash_amount,
            'currency_id': matched_transactions.company_currency_id[0] if matched_transactions.company_currency_id else False,
            'payment_type_totals': self.get_payment_type_totals(matched_transactions)
        }

    def action_print_pdf_report(self):
        self.ensure_one()
        return self.env.ref('rental_contract.action_report_branch_transaction').report_action(self.id)

    def action_print_excel_report(self):
        self.ensure_one()
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
        total_format = workbook.add_format({
            'bg_color': '#CCCCCC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 10
        })

        border_format = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter', })
        worksheet.set_column(0, 0, 500)
        worksheet.merge_range(
            0, 0, 1, 10, "تقرير السندات", bold_format_header)

        worksheet.set_row(4, 25)
        worksheet.set_row(5, 25)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 3, 20)
        worksheet.set_column(4, 4, 25)
        worksheet.set_column(5, 5, 20)
        worksheet.set_column(6, 6, 20)
        worksheet.set_column(7, 7, 15)
        worksheet.set_column(8, 8, 20)
        worksheet.set_column(9, 9, 15)
        worksheet.set_column(10, 10, 25)
        worksheet.set_column(11, 11, 15)

        arabic_headers = ["التاريخ", "العميل",
                          "رقم اللوحة", "نوع السند", "نوع الحركة", "اليومية", "طريقة التحصيل / السداد", "مبلغ القبض", "مبلغ الصرف", "حاله الدفعه", "الفرع"]
        arabic_headers.reverse()
        for col_num, header in enumerate(arabic_headers):
            worksheet.write(4, col_num, header, bold_format_arabic)
        row = 5
        matched_transactions = self.env['account.payment'].get_matched_branch_transaction(
            report_obj=self)
        totals_dict = self.get_totals_dict(matched_transactions)
        for transaction in matched_transactions:
            transaction = transaction.with_context(lang='ar_001')
            worksheet.write(
                row, 0, transaction.branch_id.name, border_format)
            state = dict(transaction._fields['state'].selection).get(
                transaction.state)
            worksheet.write(
                row, 1, state, border_format)
            worksheet.write(
                row, 2, ('%.2f' % (transaction.amount) + ' ' + transaction.currency_id.symbol) if transaction.payment_type == 'outbound' else 0.0, border_format)
            worksheet.write(
                row, 3, ('%.2f' % (transaction.amount) + ' ' + transaction.currency_id.symbol) if transaction.payment_type == 'inbound' else 0.0, border_format)
            worksheet.write(
                row, 4, transaction.payment_method_line_id.name, border_format)
            worksheet.write(
                row, 5, transaction.journal_id.name, border_format)
            payment_type_selection = dict(transaction._fields['payment_type_selection'].selection).get(
                transaction.payment_type_selection)
            worksheet.write(
                row, 6, payment_type_selection, border_format)
            payment_type = dict(transaction._fields['payment_type'].selection).get(
                transaction.payment_type)
            worksheet.write(
                row, 7, payment_type, border_format)
            worksheet.write(
                row, 8, transaction.rental_contract_id.vehicle_id.license_plate, border_format)
            worksheet.write(
                row, 9, transaction.partner_id.name, border_format)
            worksheet.write(
                row, 10, transaction.date.strftime('%Y-%m-%d'), border_format)
            row += 1
        row += 1
        company_currency = totals_dict.get('currency_id')
        worksheet.write(
            row, 10, 'اجمالى المقبوضات', total_format)
        worksheet.write(
            row, 9, '%.2f' % (totals_dict.get('total_received')) + ' ' + company_currency.symbol, border_format)
        row += 1
        worksheet.write(
            row, 10, 'اجمالى المصروفات', total_format)
        worksheet.write(
            row, 9, '%.2f' % (totals_dict.get('total_sent')) + ' ' + company_currency.symbol, border_format)
        row += 1
        worksheet.write(
            row, 10, 'اجمالى صافى الرصيد', total_format)
        worksheet.write(
            row, 9, '%.2f' % (totals_dict.get('net')) + ' ' + company_currency.symbol, border_format)
        row += 1
        worksheet.write(
            row, 10, 'اجمالي الحركات الغير نقدية', total_format)
        worksheet.write(
            row, 9, '%.2f' % (totals_dict.get('total_bank_amount')) + ' ' + company_currency.symbol, border_format)
        row += 1
        worksheet.write(
            row, 10, 'اجمالي النقدي', total_format)
        worksheet.write(
            row, 9, '%.2f' % (totals_dict.get('total_cash_amount')) + ' ' + company_currency.symbol, border_format)
        row += 2
        for payment_type_selection in totals_dict.get('payment_type_totals'):
            worksheet.write(
                row, 10, payment_type_selection, total_format)
            worksheet.write(
                row, 9, '%.2f' % (totals_dict.get('payment_type_totals').get(payment_type_selection)) + ' ' + company_currency.symbol, border_format)
            row += 1
        workbook.close()
        output.seek(0)
        excel_file = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'branch_transaction_report.xlsx',
            'datas': excel_file,
            'res_model': 'branch.transaction.report',
            'res_id': self.id,
            'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
