# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class STARentPolicy(models.Model):
    _name = 'sta.rent.policy'
    _description = 'STA Rent Policy Integration'
    _order = 'name'

    name = fields.Char(
        string='Policy Name',
        required=True,
        help='Name of the rental policy in STA system'
    )
    
    sta_policy_id = fields.Integer(
        string='STA Policy ID',
        required=True,
        unique=True,
        help='Policy ID in STA system'
    )
    
    description = fields.Text(
        string='Description',
        help='Policy description'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this policy is active'
    )
    
    policy_type = fields.Char(
        string='Policy Type',
        help='Type of rental policy'
    )
    
    terms_and_conditions = fields.Html(
        string='Terms and Conditions',
        help='Policy terms and conditions'
    )
    
    minimum_age = fields.Integer(
        string='Minimum Age',
        help='Minimum age required for this policy'
    )
    
    maximum_rental_days = fields.Integer(
        string='Maximum Rental Days',
        help='Maximum number of days for rental under this policy'
    )
    
    deposit_amount = fields.Float(
        string='Deposit Amount',
        help='Required deposit amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for amounts'
    )
    
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        help='Last synchronization date with STA'
    )
    
    sta_response_log = fields.Text(
        string='STA Response Log',
        help='Log of responses from STA API'
    )

    @api.model
    def sync_policies_from_sta(self):
        """Synchronize rental policies from STA system"""
        from ..controllers.sta_api_controller import STAAPIController
        
        try:
            api_controller = STAAPIController()
            result = api_controller.get_rent_policies()
            
            if result.get('success'):
                policies_data = result.get('policies', [])
                synced_count = 0
                
                for policy_data in policies_data:
                    sta_policy_id = policy_data.get('id')
                    if not sta_policy_id:
                        continue
                    
                    # Check if policy already exists
                    existing_policy = self.search([('sta_policy_id', '=', sta_policy_id)], limit=1)
                    
                    policy_vals = {
                        'name': policy_data.get('name', f'Policy {sta_policy_id}'),
                        'sta_policy_id': sta_policy_id,
                        'description': policy_data.get('description', ''),
                        'policy_type': policy_data.get('type', ''),
                        'terms_and_conditions': policy_data.get('terms', ''),
                        'minimum_age': policy_data.get('minimumAge', 0),
                        'maximum_rental_days': policy_data.get('maxRentalDays', 0),
                        'deposit_amount': policy_data.get('depositAmount', 0.0),
                        'last_sync_date': fields.Datetime.now(),
                        'sta_response_log': json.dumps(policy_data, indent=2),
                    }
                    
                    if existing_policy:
                        existing_policy.write(policy_vals)
                    else:
                        self.create(policy_vals)
                    
                    synced_count += 1
                
                _logger.info(f"Synchronized {synced_count} rental policies from STA")
                return {
                    'success': True,
                    'synced_count': synced_count,
                    'message': f'Successfully synchronized {synced_count} rental policies'
                }
            else:
                _logger.error(f"Failed to sync policies: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error')
                }
                
        except Exception as e:
            _logger.error(f"Error syncing policies: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def action_sync_policies(self):
        """Action to sync policies from STA"""
        result = self.sync_policies_from_sta()
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': result.get('message'),
                    'type': 'success',
                }
            }
        else:
            raise UserError(_('Failed to sync policies: %s') % result.get('error'))

    def name_get(self):
        """Custom name_get to show STA ID with name"""
        result = []
        for record in self:
            name = f"[{record.sta_policy_id}] {record.name}"
            result.append((record.id, name))
        return result

