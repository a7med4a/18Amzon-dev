from odoo import http
from odoo.http import request
import io
import xlsxwriter

class InstallmentsExportController(http.Controller):

    @http.route('/download/installments/<int:po_id>', auth='user', type='http')
    def download_installments(self, po_id, **kwargs):
        po = request.env['vehicle.purchase.order'].sudo().browse(po_id)
        if not po.exists():
            return request.not_found()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Installments')

        headers = ['External ID', 'Date', 'Amount']
        for col, h in enumerate(headers):
            sheet.write(0, col, h)

        for row, line in enumerate(po.installment_board_ids, start=1):
            xml_id = request.env['ir.model.data']._xmlid_from_record(line)
            sheet.write(row, 0, xml_id or '')
            sheet.write(row, 1, str(line.date or ''))
            sheet.write(row, 2, line.amount or 0.0)

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="installments.xlsx"'),
            ]
        )
