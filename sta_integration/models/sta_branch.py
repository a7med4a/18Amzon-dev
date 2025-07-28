# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class STABranch(models.Model):
    _name = 'sta.branch'
    _description = 'STA Branch Integration'
    _order = 'name'

    name = fields.Char(
        string='Branch Name',
        required=True,
        help='Name of the branch in STA system'
    )
    
    sta_branch_id = fields.Integer(
        string='STA Branch ID',
        required=True,
        unique=True,
        help='Branch ID in STA system'
    )
    
    odoo_branch_id = fields.Many2one(
        'res.branch',
        string='Odoo Branch',
        help='Corresponding branch in Odoo system'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this branch is active'
    )
    
    address = fields.Text(
        string='Address',
        help='Branch address'
    )
    
    city = fields.Char(
        string='City',
        help='Branch city'
    )
    
    phone = fields.Char(
        string='Phone',
        help='Branch phone number'
    )
    
    email = fields.Char(
        string='Email',
        help='Branch email'
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
    def sync_branches_from_sta(self):
        """Synchronize branches from STA system"""
        from ..controllers.sta_api_controller import STAAPIController
        
        try:
            api_controller = STAAPIController()
            result = api_controller.get_branches()
            
            if result.get('success'):
                branches_data = result.get('branches', [])
                synced_count = 0
                
                for branch_data in branches_data:
                    sta_branch_id = branch_data.get('id')
                    if not sta_branch_id:
                        continue
                    
                    # Check if branch already exists
                    existing_branch = self.search([('sta_branch_id', '=', sta_branch_id)], limit=1)
                    
                    branch_vals = {
                        'name': branch_data.get('name', f'Branch {sta_branch_id}'),
                        'sta_branch_id': sta_branch_id,
                        'address': branch_data.get('address', ''),
                        'city': branch_data.get('city', ''),
                        'phone': branch_data.get('phone', ''),
                        'email': branch_data.get('email', ''),
                        'last_sync_date': fields.Datetime.now(),
                        'sta_response_log': json.dumps(branch_data, indent=2),
                    }
                    
                    if existing_branch:
                        existing_branch.write(branch_vals)
                    else:
                        self.create(branch_vals)
                    
                    synced_count += 1
                
                _logger.info(f"Synchronized {synced_count} branches from STA")
                return {
                    'success': True,
                    'synced_count': synced_count,
                    'message': f'Successfully synchronized {synced_count} branches'
                }
            else:
                _logger.error(f"Failed to sync branches: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error')
                }
                
        except Exception as e:
            _logger.error(f"Error syncing branches: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def action_sync_branches(self):
        """Action to sync branches from STA"""
        result = self.sync_branches_from_sta()
        
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
            raise UserError(_('Failed to sync branches: %s') % result.get('error'))

    @api.model
    def get_sta_branch_by_odoo_branch(self, odoo_branch_id):
        """Get STA branch by Odoo branch ID"""
        sta_branch = self.search([('odoo_branch_id', '=', odoo_branch_id)], limit=1)
        return sta_branch.sta_branch_id if sta_branch else None

    def name_get(self):
        """Custom name_get to show STA ID with name"""
        result = []
        for record in self:
            name = f"[{record.sta_branch_id}] {record.name}"
            result.append((record.id, name))
        return result

