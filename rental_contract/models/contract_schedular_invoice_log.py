# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RentalContractInvoiceLog(models.Model):
    _name = 'rental.contract.schedular.invoice.log'
    _description = 'Rental Contract Schedular Invoice Log'

    rental_contract_id = fields.Many2one(
        'rental.contract', string='Contract', ondelete="cascade", required=True)

    date_from = fields.Datetime('Date From', required=True)
    date_to = fields.Datetime('Date To', required=True)

    actual_days = fields.Integer('Actual Days')
    actual_hours = fields.Integer('Actual Hours')
    current_days = fields.Integer('Current Hours')
    current_hours = fields.Integer('Current Hours')

    invoice_ids = fields.One2many(
        'account.move', 'invoice_log_id', string='invoices')
    invoice_id = fields.Many2one(
        'account.move', string='Related Invoice', compute="_compute_invoice_id", store=True, ondelete="restrict")

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from_to(self):
        for log in self:
            if log.date_from and log.date_to:
                day_hour_dict = log.rental_contract_id.get_day_hour(
                    log.date_from, log.date_to)
                log.actual_days = day_hour_dict.get('actual_days')
                log.actual_hours = day_hour_dict.get('actual_hours')
                log.current_days = day_hour_dict.get('current_days')
                log.current_hours = day_hour_dict.get('current_hours')
            else:
                log.actual_days = 0
                log.actual_hours = 0
                log.current_days = 0
                log.current_hours = 0

    def create_invoice(self):
        invoice_vals_list = []

        for log in self:
            day_hour_dict = log.rental_contract_id.get_day_hour(
                log.date_from, log.date_to)
            day_hour_dict.update(
                {'date_from': log.date_from, 'date_to': log.date_to})
            invoice_vals = log.rental_contract_id._prepare_invoice_vals_from_dates(
                day_hour_dict)
            if invoice_vals:
                invoice_vals.update({'invoice_log_id': log.id})
                invoice_vals_list.append(invoice_vals)

        invoices = self.env['account.move'].create(invoice_vals_list)
        invoices.action_post()

    @api.depends('invoice_ids')
    def _compute_invoice_id(self):
        for log in self:
            log.invoice_id = log.invoice_ids[0] if log.invoice_ids else False
