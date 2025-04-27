from odoo import models, fields
from odoo.exceptions import ValidationError
import base64
import xlrd

class InstallmentsImportWizard(models.TransientModel):
    _name = 'installments.import.wizard'
    _description = 'Import Installments from Excel'

    file = fields.Binary(string="Excel File", required=True)

    def import_excel(self):
        try:
            data = base64.b64decode(self.file)
            book = xlrd.open_workbook(file_contents=data)
            sheet = book.sheet_by_index(0)
            total = 0.0
            row_data={}
            order = self.env['vehicle.purchase.order'].browse(
                self._context.get('active_id'))
            expected = order.number_of_installment * order.installment_cost

            for row in range(1, sheet.nrows):
                external_id_raw = sheet.cell(row, 0).value
                # external_id = str(external_id_raw).strip()
                amount = float(sheet.cell(row, 2).value)
                row_data[external_id_raw]=amount
                total += amount
            if abs(total - expected) > 0.01:
                raise ValidationError(
                    f"Total of installments ({total:.2f}) must equal original amount: {expected:.2f}"
                )
            else:
                for line in row_data:
                    record = self.env['installments.board'].browse(int(line))
                    amount = row_data[line]
                    if record and record._name == 'installments.board' and record.paid_amount == 0:
                        record.with_context({'create_from_btn': True}).write({'amount': amount})
                        # record.amount = amount


        except Exception as e:
            raise ValidationError(f"Failed to import file: {str(e)}")
