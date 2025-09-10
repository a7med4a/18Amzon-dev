# -*- coding: utf-8 -*-

from odoo import models, _, api


class ReportBranchTransaction(models.AbstractModel):
    _name = 'report.rental_contract.branch_transaction_template'
    _description = 'Branch Transaction Template'

    @api.model
    def _get_report_values(self, docids, data=None):

        report_obj = self.env['branch.transaction.report'].browse(docids)
        matched_transactions = self.env['account.payment'].get_matched_branch_transaction(
            report_obj=report_obj)
        totals_dict = report_obj.get_totals_dict(matched_transactions)

        return {
            'doc_ids': docids,
            'doc_model': self.env['branch.transaction.report'],
            'matched_transactions': matched_transactions,
            'totals_dict': totals_dict,
            'data': data,
            'docs': docids,
        }
