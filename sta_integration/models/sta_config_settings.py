# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    sta_app_id = fields.Char(
        string='STA App ID',
        help='Application ID provided by Saudi Transport Authority',
        default="c49fda9f",
        groups="base.group_system"
    )

    sta_app_key = fields.Char(
        string='STA App Key',
        help='Application Key provided by Saudi Transport Authority',
        default="0a0ecdd133cbda8414c36b1d9f8f8f51",
        groups="base.group_system"
    )

    sta_authorization_token = fields.Char(
        string='STA Authorization Token',
        help='Authorization token for STA API (Basic Auth encoded)',
        default="Basic YXBpVXNlcjEzMTM4MjQ6QWFAMTIzNDU2",
        groups="base.group_system"
    )

    sta_base_url = fields.Char(
        string='STA Base URL',
        default='https://tajeer-stg.api.elm.sa',
        help='Base URL for STA API endpoints',
        required=True
    )

    sta_is_production = fields.Boolean(
        string='Production Environment',
        help='Check if using production environment, uncheck for staging',
        default=False
    )

    sta_connection_timeout = fields.Integer(
        string='Connection Timeout',
        help='Connection timeout in seconds',
        default=30
    )

    sta_last_connection_test = fields.Datetime(
        string='Last Connection Test',
        help='Last successful connection test date',
        readonly=True
    )

    sta_connection_status = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Connection Status', default='not_tested', readonly=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # إضافة حقل المديول لإظهار الأيقونة
    module_naql_integration = fields.Boolean(
        string='Enable Naql Integration',
        help='Enable Saudi Transport Authority Integration features'
    )

    sta_app_id = fields.Char(
        string='STA App ID',
        related='company_id.sta_app_id',
        readonly=False,
        help='Application ID provided by Saudi Transport Authority'
    )

    sta_app_key = fields.Char(
        string='STA App Key',
        related='company_id.sta_app_key',
        readonly=False,
        help='Application Key provided by Saudi Transport Authority'
    )

    sta_authorization_token = fields.Char(
        string='STA Authorization Token',
        related='company_id.sta_authorization_token',
        readonly=False,
        help='Authorization token for STA API (Basic Auth encoded)'
    )

    sta_base_url = fields.Char(
        string='STA Base URL',
        related='company_id.sta_base_url',
        readonly=False,
        help='Base URL for STA API endpoints',
        required=True
    )

    sta_is_production = fields.Boolean(
        string='Production Environment',
        related='company_id.sta_is_production',
        readonly=False,
        help='Check if using production environment, uncheck for staging'
    )

    sta_connection_timeout = fields.Integer(
        string='Connection Timeout (seconds)',
        related='company_id.sta_connection_timeout',
        readonly=False,
        help='Connection timeout in seconds'
    )

    sta_last_connection_test = fields.Datetime(
        string='Last Connection Test',
        related='company_id.sta_last_connection_test',
        readonly=True,
        help='Last successful connection test date'
    )

    sta_connection_status = fields.Selection(
        related='company_id.sta_connection_status',
        readonly=True
    )

    @api.model
    def get_config(self):
        """إرجاع إعدادات STA كقاموس"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()

        config = {
            'sta_api_url': IrConfigParameter.get_param('sta_integration.api_url',
                                                       'https://tajeer-stg.api.elm.sa/rental-api'),
            'sta_app_id': IrConfigParameter.get_param('sta_integration.app_id', ''),
            'sta_app_key': IrConfigParameter.get_param('sta_integration.app_key', ''),
            'sta_auth_token': IrConfigParameter.get_param('sta_integration.auth_token', ''),
            'sta_timeout': int(IrConfigParameter.get_param('sta_integration.api_timeout', '30')),
            'sta_auto_sync': IrConfigParameter.get_param('sta_integration.auto_sync', 'False').lower() == 'true',
        }

        return config

    @api.model
    def get_api_credentials(self):
        """إرجاع بيانات الاعتماد للـ API"""
        config = self.get_config()

        return {
            'api_url': config['sta_api_url'],
            'app_id': config['sta_app_id'],
            'app_key': config['sta_app_key'],
            'auth_token': config['sta_auth_token'],
            'timeout': config['sta_timeout']
        }

    @api.onchange('sta_is_production')
    def _onchange_sta_is_production(self):
        """تغيير URL تلقائياً حسب البيئة"""
        if self.sta_is_production:
            self.sta_base_url = 'https://tajeer-sta.api.elm.sa'
        else:
            self.sta_base_url = 'https://tajeer-stg.api.elm.sa'

    def _get_sta_api_controller(self):
        """إنشاء instance من STA API Controller"""
        # حفظ البيانات في system parameters مؤقتاً لاستخدامها في الكونترولر
        self.env['ir.config_parameter'].sudo().set_param('sta_integration.sta_app_id', self.sta_app_id or '')
        self.env['ir.config_parameter'].sudo().set_param('sta_integration.sta_app_key', self.sta_app_key or '')
        self.env['ir.config_parameter'].sudo().set_param('sta_integration.sta_authorization_token',
                                                         self.sta_authorization_token or '')
        self.env['ir.config_parameter'].sudo().set_param('sta_integration.sta_base_url', self.sta_base_url or '')
        self.env['ir.config_parameter'].sudo().set_param('sta_integration.sta_is_production',
                                                         str(self.sta_is_production))

        # استيراد الكونترولر من المكان الصحيح
        from ..controllers.sta_api_controller import STAAPIController
        return STAAPIController()

    def test_sta_connection(self):
        """اختبار الاتصال مع STA API"""
        self.ensure_one()

        try:
            # التحقق من البيانات المطلوبة
            required_fields = ['sta_app_id', 'sta_app_key', 'sta_authorization_token', 'sta_base_url']
            missing_fields = []

            for field in required_fields:
                if not getattr(self.company_id, field):
                    missing_fields.append(self._fields[field].string)

            if missing_fields:
                raise UserError(_('Please configure: %s') % ', '.join(missing_fields))

            # إنشاء instance من الكونترولر واختبار الاتصال
            api_controller = self._get_sta_api_controller()
            result = api_controller.test_connection()

            if result.get('success'):
                # تحديث حالة الاتصال
                self.company_id.write({
                    'sta_connection_status': 'success',
                    'sta_last_connection_test': fields.Datetime.now()
                })

                branches = result.get('branches', [])
                branches_count = len(branches) if branches else 0

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Connection Successful'),
                        'message': _('Successfully connected to STA API!\nEnvironment: %s\nBranches found: %s') % (
                            'Production' if self.sta_is_production else 'Staging',
                            branches_count
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # تحديث حالة الاتصال
                self.company_id.sta_connection_status = 'failed'
                error_message = result.get('error', 'Unknown error')
                raise UserError(_('❌ Connection test failed:\n%s') % error_message)

        except Exception as e:
            self.company_id.sta_connection_status = 'failed'
            _logger.error(f"STA API connection test failed: {str(e)}")
            raise UserError(_('❌ Connection test failed:\n%s') % str(e))

    def sync_sta_branches(self):
        """مزامنة الفروع من STA"""
        self.ensure_one()

        try:
            api_controller = self._get_sta_api_controller()
            result = api_controller.get_branches()

            if result.get('success'):
                branches = result.get('branches', [])
                print("branches ==> ",branches)

                # إنشاء أو تحديث الفروع في Odoo
                sta_branch_model = self.env['sta.branch']
                created_count = 0
                updated_count = 0

                for branch_data in branches:
                    branch_id = branch_data.get('id')
                    branch_name = branch_data.get('name', f'Branch {branch_id}')

                    existing_branch = sta_branch_model.search([('sta_branch_id', '=', branch_id)], limit=1)

                    if existing_branch:
                        existing_branch.write({
                            'name': branch_name,
                        })
                        updated_count += 1
                    else:
                        sta_branch_model.create({
                            'sta_branch_id': branch_id,
                            'name': branch_name,
                        })
                        created_count += 1

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Sync Complete'),
                        'message': _('Branches synchronized successfully!\nCreated: %s\nUpdated: %s') % (
                            created_count, updated_count
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Failed to fetch branches: %s') % result.get('error', 'Unknown error'))

        except Exception as e:
            _logger.error(f"STA branches sync failed: {str(e)}")
            raise UserError(_('❌ Sync failed:\n%s') % str(e))

    def reset_sta_credentials(self):
        """إعادة تعيين البيانات للقيم الافتراضية"""
        self.ensure_one()

        default_values = {
            'sta_app_id': 'c49fda9f',
            'sta_app_key': '0a0ecdd133cbda8414c36b1d9f8f8f51',
            'sta_authorization_token': 'Basic YXBpVXNlcjEzMTM4MjQ6QWFAMTIzNDU2',
            'sta_base_url': 'https://tajeer-stg.api.elm.sa',
            'sta_is_production': False,
            'sta_connection_timeout': 30,
            'sta_connection_status': 'not_tested',
            'sta_last_connection_test': False
        }

        self.company_id.write(default_values)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset Complete'),
                'message': _('STA credentials have been reset to default values.'),
                'type': 'info',
                'sticky': False,
            }
        }

    def open_sta_documentation(self):
        """فتح وثائق STA API"""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://developer.elm.sa/docs/sta-api',
            'target': 'new',
        }

    @api.model
    def default_get(self, fields_list):
        """Override to ensure STA tab is selected by default when accessed from STA menu"""
        res = super().default_get(fields_list)

        # إذا تم الوصول من خلال menu STA Integration
        context = self.env.context
        if context.get('sta_integration_settings') or context.get('module') == 'sta_integration':
            # تأكد من أن حقل المديول مفعل لإظهار التبويب
            res.update({
                'module_naql_integration': True,  # أو اسم المديول الصحيح
            })

            # إضافة flag لـ JavaScript للتبديل التلقائي للتبويب
            self = self.with_context(auto_select_sta_tab=True)

        return res