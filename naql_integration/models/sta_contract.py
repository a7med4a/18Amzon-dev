# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class NaqlContract(models.Model):
    _name = 'sta.contract'
    _description = 'Naql Contract Integration'
    _order = 'create_date desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True
    )
    
    rental_contract_id = fields.Many2one(
        'rental.contract',
        string='Rental Contract',
        required=True,
        ondelete='cascade',
        help='Related rental contract in Odoo'
    )
    
    sta_contract_number = fields.Char(
        string='Naql Contract Number',
        help='Contract number assigned by Naql system'
    )
    
    sta_status = fields.Selection([
        ('draft', 'Draft'),
        ('created', 'Created'),
        ('saved', 'Saved'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
        ('error', 'Error'),
    ], string='Naql Status', default='draft', tracking=True)
    
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        help='Last synchronization date with Naql'
    )
    
    sta_response_log = fields.Text(
        string='Naql Response Log',
        help='Log of responses from Naql API for debugging'
    )
    
    operator_id = fields.Char(
        string='Operator ID',
        help='ID of the operator who created the contract'
    )
    
    working_branch_id = fields.Many2one(
        'sta.branch',
        string='Working Branch',
        help='Naql branch where the contract is processed'
    )
    
    receive_branch_id = fields.Many2one(
        'sta.branch',
        string='Receive Branch',
        help='Naql branch where vehicle is received'
    )
    
    return_branch_id = fields.Many2one(
        'sta.branch',
        string='Return Branch',
        help='Naql branch where vehicle is returned'
    )
    
    rent_policy_id = fields.Many2one(
        'sta.rent.policy',
        string='Rent Policy',
        help='Naql rental policy applied to this contract'
    )
    
    otp_sent = fields.Boolean(
        string='OTP Sent',
        default=False,
        help='Whether OTP has been sent for this contract'
    )
    
    vehicle_owner_id_version = fields.Integer(
        string='Vehicle Owner ID Version',
        default=1,
        help='Version of vehicle owner ID'
    )
    
    error_message = fields.Text(
        string='Error Message',
        help='Last error message from Naql API'
    )

    @api.depends('rental_contract_id', 'sta_contract_number')
    def _compute_name(self):
        for record in self:
            if record.sta_contract_number:
                record.name = f"Naql-{record.sta_contract_number}"
            elif record.rental_contract_id:
                record.name = f"Naql-{record.rental_contract_id.name}"
            else:
                record.name = "New Naql Contract"

    def action_create_sta_contract(self):
        """Create contract in Naql system"""
        self.ensure_one()
        if not self.rental_contract_id:
            raise UserError(_('Please select a rental contract first.'))
        
        if self.sta_status != 'draft':
            raise UserError(_('Contract can only be created from draft status.'))
        
        # Import here to avoid circular imports
        from ..controllers.sta_api_controller import NaqlAPIController
        
        try:
            api_controller = NaqlAPIController()
            result = api_controller.create_contract(self)
            
            if result.get('success'):
                self.write({
                    'sta_status': 'created',
                    'sta_contract_number': result.get('contract_number'),
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                    'error_message': False,
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Contract created successfully in Naql system.'),
                        'type': 'success',
                    }
                }
            else:
                self.write({
                    'sta_status': 'error',
                    'error_message': result.get('error'),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                raise UserError(_('Failed to create contract: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error creating Naql contract: {str(e)}")
            self.write({
                'sta_status': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error creating contract: %s') % str(e))

    def action_send_otp(self):
        """Send OTP for contract verification"""
        self.ensure_one()
        if not self.sta_contract_number:
            raise UserError(_('Contract must be created in Naql first.'))
        
        from ..controllers.sta_api_controller import NaqlAPIController
        
        try:
            api_controller = NaqlAPIController()
            result = api_controller.send_otp(self.sta_contract_number)
            
            if result.get('success'):
                self.write({
                    'otp_sent': True,
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('OTP sent successfully.'),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Failed to send OTP: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error sending OTP: {str(e)}")
            raise UserError(_('Error sending OTP: %s') % str(e))

    def action_save_sta_contract(self):
        """Save complete contract details to Naql"""
        self.ensure_one()
        if self.sta_status not in ['created', 'draft']:
            raise UserError(_('Contract can only be saved from created or draft status.'))
        
        from ..controllers.sta_api_controller import NaqlAPIController
        
        try:
            api_controller = NaqlAPIController()
            result = api_controller.save_contract(self)
            
            if result.get('success'):
                self.write({
                    'sta_status': 'saved',
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                    'error_message': False,
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Contract saved successfully in Naql system.'),
                        'type': 'success',
                    }
                }
            else:
                self.write({
                    'sta_status': 'error',
                    'error_message': result.get('error'),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                raise UserError(_('Failed to save contract: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error saving Naql contract: {str(e)}")
            self.write({
                'sta_status': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error saving contract: %s') % str(e))

    def action_cancel_contract(self):
        """Open wizard to cancel contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Naql Contract'),
            'res_model': 'sta.cancel.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sta_contract_id': self.id}
        }

    def action_suspend_contract(self):
        """Open wizard to suspend contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Suspend Naql Contract'),
            'res_model': 'sta.suspend.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sta_contract_id': self.id}
        }

    def action_close_contract(self):
        """Open wizard to close contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Close Naql Contract'),
            'res_model': 'sta.close.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sta_contract_id': self.id}
        }

    @api.model
    def create(self, vals):
        """Override create to set default operator_id"""
        if not vals.get('operator_id'):
            # You can set a default operator_id here based on current user or company settings
            vals['operator_id'] = self.env.user.partner_id.vat or '1028558326'  # Default fallback
        return super().create(vals)


class RentalContract(models.Model):
    _inherit = 'rental.contract'

    sta_contract_ids = fields.One2many(
        'sta.contract',
        'rental_contract_id',
        string='Naql Contracts',
        help='Related Naql contracts'
    )
    
    sta_contract_count = fields.Integer(
        string='Naql Contracts Count',
        compute='_compute_sta_contract_count'
    )

    @api.depends('sta_contract_ids')
    def _compute_sta_contract_count(self):
        for record in self:
            record.sta_contract_count = len(record.sta_contract_ids)

    def action_view_sta_contracts(self):
        """View related Naql contracts"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Naql Contracts'),
            'res_model': 'sta.contract',
            'view_mode': 'tree,form',
            'domain': [('rental_contract_id', '=', self.id)],
            'context': {'default_rental_contract_id': self.id}
        }

    def action_create_sta_contract(self):
        """Create new Naql contract for this rental contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Naql Contract'),
            'res_model': 'sta.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_rental_contract_id': self.id}
        }

