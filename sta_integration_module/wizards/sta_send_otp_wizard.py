# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class STASendOTPWizard(models.TransientModel):
    _name = 'sta.send.otp.wizard'
    _description = 'Send OTP for STA Contract'

    sta_contract_id = fields.Many2one(
        'sta.contract',
        string='STA Contract',
        required=True,
        help='STA contract to send OTP for'
    )
    
    contract_number = fields.Char(
        string='Contract Number',
        related='sta_contract_id.sta_contract_number',
        readonly=True
    )
    
    current_status = fields.Selection(
        string='Current Status',
        related='sta_contract_id.sta_status',
        readonly=True
    )

    def action_send_otp(self):
        """Send OTP for the contract"""
        self.ensure_one()
        
        if not self.sta_contract_id.sta_contract_number:
            raise UserError(_('Contract must be created in STA system first.'))
        
        try:
            result = self.sta_contract_id.action_send_otp()
            return result
        except Exception as e:
            raise UserError(_('Failed to send OTP: %s') % str(e))

