# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class NaqlCancelContractWizard(models.TransientModel):
    _name = 'sta.cancel.contract.wizard'
    _description = 'Cancel Naql Contract'

    sta_contract_id = fields.Many2one(
        'sta.contract',
        string='Naql Contract',
        required=True,
        help='Naql contract to cancel'
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
    
    cancellation_reason = fields.Text(
        string='Cancellation Reason',
        required=True,
        help='Reason for cancelling the contract'
    )

    def action_cancel_contract(self):
        """Cancel the contract in Naql system"""
        self.ensure_one()
        
        if not self.sta_contract_id.sta_contract_number:
            raise UserError(_('Contract must be created in Naql system first.'))
        
        if self.sta_contract_id.sta_status in ['cancelled', 'closed']:
            raise UserError(_('Contract is already cancelled or closed.'))
        
        from ..controllers.sta_api_controller import NaqlAPIController
        
        try:
            api_controller = NaqlAPIController()
            result = api_controller.cancel_contract(
                self.sta_contract_id.sta_contract_number,
                self.cancellation_reason
            )
            
            if result.get('success'):
                self.sta_contract_id.write({
                    'sta_status': 'cancelled',
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                    'error_message': False,
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Contract cancelled successfully in Naql system.'),
                        'type': 'success',
                    }
                }
            else:
                self.sta_contract_id.write({
                    'sta_status': 'error',
                    'error_message': result.get('error'),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                raise UserError(_('Failed to cancel contract: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error cancelling Naql contract: {str(e)}")
            self.sta_contract_id.write({
                'sta_status': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error cancelling contract: %s') % str(e))

