# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sta_app_id = fields.Char(
        string='STA App ID',
        config_parameter='sta_integration.app_id',
        help='Application ID provided by Saudi Transport Authority'
    )
    
    sta_app_key = fields.Char(
        string='STA App Key',
        config_parameter='sta_integration.app_key',
        help='Application Key provided by Saudi Transport Authority'
    )
    
    sta_authorization_token = fields.Char(
        string='STA Authorization Token',
        config_parameter='sta_integration.authorization_token',
        help='Authorization token for STA API (Basic Auth encoded)'
    )
    
    sta_base_url = fields.Char(
        string='STA Base URL',
        config_parameter='sta_integration.base_url',
        default='https://tajeer-stg.api.elm.sa',
        help='Base URL for STA API endpoints'
    )
    
    sta_is_production = fields.Boolean(
        string='Production Environment',
        config_parameter='sta_integration.is_production',
        default=False,
        help='Check if using production environment, uncheck for staging'
    )

    @api.model
    def get_sta_config(self):
        """Get STA configuration parameters"""
        return {
            'app_id': self.env['ir.config_parameter'].sudo().get_param('sta_integration.app_id'),
            'app_key': self.env['ir.config_parameter'].sudo().get_param('sta_integration.app_key'),
            'authorization_token': self.env['ir.config_parameter'].sudo().get_param('sta_integration.authorization_token'),
            'base_url': self.env['ir.config_parameter'].sudo().get_param('sta_integration.base_url', 'https://tajeer-stg.api.elm.sa'),
            'is_production': self.env['ir.config_parameter'].sudo().get_param('sta_integration.is_production', False),
        }

    def test_sta_connection(self):
        """Test connection to STA API"""
        config = self.get_sta_config()
        if not all([config['app_id'], config['app_key'], config['authorization_token']]):
            raise UserError(_('Please configure all STA credentials before testing connection.'))
        
        # Import here to avoid circular imports
        from ..controllers.sta_api_controller import STAAPIController
        
        try:
            api_controller = STAAPIController()
            result = api_controller.test_connection()
            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection to STA API successful!'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Connection failed: %s') % result.get('error', 'Unknown error'))
        except Exception as e:
            raise UserError(_('Connection test failed: %s') % str(e))

