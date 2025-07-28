# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ApiLookupWizard(models.TransientModel):
    _name = 'api.lookup.wizard'
    _description = 'API Lookup Wizard'

    lookup_action = fields.Selection(
        selection=[
            ('authorization-type', 'Authorization Type'),
            ('contract-status', 'Contract Status'),
            ('contract-type', 'Contract Type'),
            ('external-authorization-countries', 'External Authorization Countries'),
            ('fuel-type', 'Fuel Type'),
            ('id-type', 'ID Type'),
            ('payment-method', 'Payment Method'),
            ('yakeen-nationality', 'Yakeen Nationality'),
            ('gccNationality', 'GCC Nationality'),
            ('country', 'Country'),
            ('closure-reasons', 'Closure Reasons'),
            ('suspension-reasons', 'Suspension Reasons'),
            # الفروع
            ('branch-all', 'All Branches'),
        ],
        string='Lookup Action',
        required=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('loading', 'Loading'),
        ('loaded', 'Data Loaded'),
        ('error', 'Error')
    ], default='draft', string='State')

    url = fields.Char('API URL', readonly=True)
    response_message = fields.Text('Response Message', readonly=True)
    total_records = fields.Integer('Total Records', readonly=True)
    last_sync = fields.Datetime('Last Sync', readonly=True)
    api_lines_ids = fields.One2many('api.lookup.lines', 'wizard_id', string='API Lines')
    raw_response_data = fields.Text('Raw Response Data', readonly=True)

    def _get_api_config(self):
        """الحصول على إعدادات الـ API"""
        try:
            config = {
                'sta_app_id': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_app_id'),
                'sta_app_key': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_app_key'),
                'sta_authorization_token': self.env['ir.config_parameter'].sudo().get_param(
                    'sta_integration.sta_authorization_token'),
                'sta_base_url': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_base_url'),
                'sta_is_production': self.env['ir.config_parameter'].sudo().get_param(
                    'sta_integration.sta_is_production',
                    'False') == 'True',
                'sta_connection_timeout': int(
                    self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_connection_timeout', '30'))
            }

            # إذا لم تكن الإعدادات متوفرة في system parameters، احصل عليها من الشركة الحالية
            if not config.get('sta_app_id'):
                company = self.env.company
                config.update({
                    'sta_app_id': company.sta_app_id if hasattr(company, 'sta_app_id') else '',
                    'sta_app_key': company.sta_app_key if hasattr(company, 'sta_app_key') else '',
                    'sta_authorization_token': company.sta_authorization_token if hasattr(company,
                                                                                          'sta_authorization_token') else '',
                    'sta_base_url': company.sta_base_url if hasattr(company,
                                                                    'sta_base_url') else 'https://tajeer-stg.api.elm.sa',
                    'sta_is_production': company.sta_is_production if hasattr(company, 'sta_is_production') else False,
                    'sta_connection_timeout': company.sta_connection_timeout if hasattr(company,
                                                                                        'sta_connection_timeout') else 30
                })

            # تحديد base_url بناءً على البيئة
            if not config.get('sta_base_url'):
                if config.get('sta_is_production'):
                    config['sta_base_url'] = 'https://tajeer.api.elm.sa'
                else:
                    config['sta_base_url'] = 'https://tajeer-stg.api.elm.sa'

            return config

        except Exception as e:
            _logger.error(f"Error getting API config: {str(e)}")
            # إعدادات افتراضية في حالة الخطأ
            return {
                'sta_app_id': '',
                'sta_app_key': '',
                'sta_authorization_token': '',
                'sta_base_url': 'https://tajeer-stg.api.elm.sa',
                'sta_is_production': False,
                'sta_connection_timeout': 30,
            }

    def _get_api_url(self, action):
        """بناء URL للـ API حسب النوع المختار"""
        config = self._get_api_config()
        base_url = config.get('sta_base_url', 'https://tajeer-stg.api.elm.sa')

        # إضافة /rental-api إذا لم تكن موجودة
        if not base_url.endswith('/rental-api'):
            base_url = f"{base_url}/rental-api"

        # تحديد URL حسب النوع
        url_mapping = {
            # الـ Lookups الأساسية
            'authorization-type': f"{base_url}/lookups/authorization-type",
            'contract-status': f"{base_url}/lookups/contract-status",
            'contract-type': f"{base_url}/lookups/contract-type",
            'external-authorization-countries': f"{base_url}/lookups/external-authorization-countries",
            'fuel-type': f"{base_url}/lookups/fuel-type",
            'id-type': f"{base_url}/lookups/id-type",
            'payment-method': f"{base_url}/lookups/payment-method",
            'yakeen-nationality': f"{base_url}/lookups/yakeen-nationality",
            'gccNationality': f"{base_url}/lookups/gccNationality",
            'country': f"{base_url}/lookups/country",
            'closure-reasons': f"{base_url}/lookups/closure-reasons",
            'suspension-reasons': f"{base_url}/lookups/suspension-reasons",

            # الفروع - endpoint الصحيح
            'branch-all': f"{base_url}/branch/all",
        }

        return url_mapping.get(action)

    def _get_api_headers(self):
        """إعداد Headers للـ API"""
        config = self._get_api_config()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Odoo-STA-Integration/1.0',
            'app-id': str(config.get('sta_app_id', '')),
            'app-key': str(config.get('sta_app_key', '')),
            'Authorization': str(config.get('sta_authorization_token', ''))
        }

        # إزالة headers الفارغة
        headers = {k: v for k, v in headers.items() if v}
        return headers

    def _process_response_data(self, data, action):
        """معالجة البيانات المستقبلة من API حسب النوع"""
        records_data = []

        try:
            # البحث عن البيانات الفعلية
            actual_data = data

            if isinstance(data, dict):
                possible_keys = ['data', 'result', 'items', 'records', 'lookups', 'branches', 'branchList']
                for key in possible_keys:
                    if key in data and data[key]:
                        actual_data = data[key]
                        _logger.info(f"Found data in key: {key}")
                        break

            if isinstance(actual_data, list):
                _logger.info(f"Processing {len(actual_data)} items for action: {action}")

                for idx, item in enumerate(actual_data):
                    # طباعة البيانات الخام للعنصر الأول للتشخيص
                    if idx == 0:
                        _logger.info(f"First item raw data: {json.dumps(item, indent=2, ensure_ascii=False)}")

                    record = self._process_single_item(item, idx, action)
                    if record:
                        records_data.append(record)
                    else:
                        _logger.warning(f"Failed to process item at index {idx}")

            elif isinstance(actual_data, dict):
                record = self._process_single_item(actual_data, 0, action)
                if record:
                    records_data.append(record)

            _logger.info(f"Successfully processed {len(records_data)} records for action: {action}")

            # طباعة عينة من البيانات المعالجة
            if records_data:
                sample_record = records_data[0]
                _logger.info(
                    f"Sample processed record: transfer_id={sample_record['transfer_id']}, ar_name='{sample_record['ar_name']}', en_name='{sample_record['en_name']}'")

        except Exception as e:
            _logger.error(f"Error processing response data for action {action}: {str(e)}")
            _logger.error(
                f"Data type: {type(data)}, Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

        return records_data

    def _process_single_item(self, item, index, action):
        """معالجة عنصر واحد من البيانات"""
        try:
            # استخراج الحقول الأساسية حسب نوع الـ lookup
            description = self._extract_description(item, action)
            transfer_id = self._extract_transfer_id(item, action)
            system_id = self._extract_system_id(item, action)
            ar_name = self._extract_ar_name(item, action)
            en_name = self._extract_en_name(item, action)

            # إذا لم نجد transfer_id، استخدم index كـ fallback أخير فقط
            if transfer_id is None:
                _logger.warning(f"No transfer_id found for index {index}, using index as fallback")
                transfer_id = index + 1

            # استخراج الحقول الإضافية للفروع
            city_ar_name = ''
            region_ar_name = ''
            district_ar = ''

            if action == 'branch-all':
                license_data = item.get('license', {})
                if license_data:
                    city_ar_name = license_data.get('cityArName', '')
                    region_ar_name = license_data.get('regionArName', '')
                    district_ar = license_data.get('districtAr', '')

                if not city_ar_name:
                    city_ar_name = item.get('cityArName', '')
                if not region_ar_name:
                    region_ar_name = item.get('regionArName', '')
                if not district_ar:
                    district_ar = item.get('districtAr', '')

            # طباعة لوج للتشخيص
            _logger.info(
                f"Processing item {index}: transfer_id={transfer_id}, ar_name='{ar_name}', en_name='{en_name}'")

            return {
                'wizard_id': self.id,
                'description': description or f'{ar_name or en_name or "Record"} ({transfer_id})',
                'transfer_id': str(transfer_id),
                'system_id': str(system_id) if system_id is not None else '',
                'ar_name': ar_name or '',
                'en_name': en_name or '',
                'city_ar_name': city_ar_name,
                'region_ar_name': region_ar_name,
                'district_ar': district_ar,
                'raw_data': json.dumps(item, indent=2, ensure_ascii=False)
            }

        except Exception as e:
            _logger.error(f"Error processing single item at index {index}: {str(e)}")
            _logger.error(f"Item data: {item}")
            return None

    def _extract_description(self, item, action):
        """استخراج الوصف حسب نوع الـ lookup"""
        description_fields = {
            'authorization-type': ['name', 'description', 'authorizationType', 'arName', 'enName'],
            'contract-status': ['name', 'status', 'statusName', 'arName', 'enName'],
            'contract-type': ['name', 'type', 'typeName', 'arName', 'enName'],
            'external-authorization-countries': ['countryName', 'name', 'country', 'arName', 'enName'],
            'fuel-type': ['name', 'type', 'fuelType', 'arName', 'enName'],
            'id-type': ['name', 'type', 'idType', 'arName', 'enName'],
            'payment-method': ['name', 'method', 'paymentMethod', 'arName', 'enName'],
            'yakeen-nationality': ['nationalityName', 'name', 'nationality', 'arName', 'enName'],
            'gccNationality': ['nationalityName', 'name', 'nationality', 'arName', 'enName'],
            'country': ['countryName', 'name', 'country', 'arName', 'enName'],
            'closure-reasons': ['reason', 'name', 'description', 'arName', 'enName'],
            'suspension-reasons': ['reason', 'name', 'description', 'arName', 'enName'],
            'branch-all': ['license.crName', 'branchName', 'name', 'branch', 'description', 'arName', 'enName'],
        }

        fields_to_check = description_fields.get(action, ['name', 'description', 'title', 'arName', 'enName'])

        for field in fields_to_check:
            # التحقق من الحقول المتداخلة مثل license.crName
            if '.' in field:
                parts = field.split('.')
                current_obj = item
                for part in parts:
                    if isinstance(current_obj, dict) and part in current_obj:
                        current_obj = current_obj[part]
                    else:
                        current_obj = None
                        break
                if current_obj:
                    return current_obj
            else:
                # التحقق من الحقول العادية
                if field in item and item[field]:
                    return item[field]

        return None

    def _extract_ar_name(self, item, action):
        """استخراج الاسم العربي من البيانات"""
        ar_fields = ['arName', 'arabicName', 'nameAr', 'ar_name', 'name_ar']

        # إضافة حقول خاصة بالفروع
        if action == 'branch-all':
            # البحث في license أولاً
            license_data = item.get('license', {})
            if license_data:
                license_ar_fields = ['crName', 'cityArName', 'regionArName']
                for field in license_ar_fields:
                    if field in license_data and license_data[field]:
                        return license_data[field]

            # ثم البحث في الكائن الرئيسي
            ar_fields.extend(['branchNameAr', 'branchArabicName', 'branchArName', 'addressAr', 'locationAr'])

        for field in ar_fields:
            if field in item and item[field]:
                return item[field]

        # إذا لم نجد حقل عربي مخصص، نحاول البحث في الحقول الأخرى
        if action in ['yakeen-nationality', 'gccNationality', 'country']:
            other_fields = ['nationalityNameAr', 'countryNameAr']
            for field in other_fields:
                if field in item and item[field]:
                    return item[field]

        return None

    def _extract_en_name(self, item, action):
        """استخراج الاسم الإنجليزي من البيانات"""
        en_fields = ['enName', 'englishName', 'nameEn', 'en_name', 'name_en']

        # إضافة حقول خاصة بالفروع
        if action == 'branch-all':
            # البحث في license أولاً
            license_data = item.get('license', {})
            if license_data:
                license_en_fields = ['cityEnName', 'regionEnName']
                for field in license_en_fields:
                    if field in license_data and license_data[field]:
                        return license_data[field]

            # ثم البحث في الكائن الرئيسي
            en_fields.extend(['branchNameEn', 'branchEnglishName', 'branchEnName', 'addressEn', 'locationEn'])

        for field in en_fields:
            if field in item and item[field]:
                return item[field]

        # إذا لم نجد حقل إنجليزي مخصص، نحاول البحث في الحقول الأخرى
        if action in ['yakeen-nationality', 'gccNationality', 'country']:
            other_fields = ['nationalityNameEn', 'countryNameEn', 'nationalityName', 'countryName']
            for field in other_fields:
                if field in item and item[field]:
                    return item[field]

        # للفروع، نجرب الحقول الأساسية
        if action == 'branch-all':
            branch_fields = ['branchName', 'address', 'location']
            for field in branch_fields:
                if field in item and item[field]:
                    return item[field]

        # إذا لم نجد حقل إنجليزي، نجرب 'name' كبديل
        if 'name' in item and item['name']:
            return item['name']

        return None

    def _extract_transfer_id(self, item, action):
        """استخراج Transfer ID حسب نوع الـ lookup"""

        # البحث أولاً عن الـ ID في المكان الصحيح حسب نوع الـ API
        id_fields = {
            'authorization-type': ['id', 'authorizationTypeId'],
            'contract-status': ['id', 'statusId'],
            'contract-type': ['id', 'typeId'],
            'external-authorization-countries': ['countryId', 'id'],
            'fuel-type': ['id', 'fuelTypeId'],
            'id-type': ['id', 'idTypeId'],
            'payment-method': ['id', 'methodId'],
            'yakeen-nationality': ['id', 'nationalityId'],  # تأكد من أن id هو الأول
            'gccNationality': ['id', 'nationalityId'],
            'country': ['id', 'countryId'],
            'closure-reasons': ['id', 'reasonId'],
            'suspension-reasons': ['id', 'reasonId'],
            'branch-all': ['id', 'branchId', 'accountId'],
        }

        fields_to_check = id_fields.get(action, ['id'])

        # البحث في الحقول المحددة
        for field in fields_to_check:
            if field in item and item[field] is not None:
                try:
                    # تحويل إلى رقم للتأكد
                    id_value = int(item[field])
                    _logger.info(f"Found {field}={id_value} for action={action}")
                    return id_value
                except (ValueError, TypeError):
                    continue

        # البحث العام في جميع الحقول التي تنتهي بـ id أو Id
        for key, value in item.items():
            if key.lower().endswith('id') and value is not None:
                try:
                    id_value = int(value)
                    _logger.warning(f"Fallback: Using {key}={id_value} for action={action}")
                    return id_value
                except (ValueError, TypeError):
                    continue

        _logger.error(f"No valid ID found for action={action}, item keys: {list(item.keys())}")
        return None

    def _extract_system_id(self, item, action):
        """استخراج System ID حسب نوع الـ lookup"""
        code_fields = {
            'authorization-type': ['code', 'systemId', 'authorizationCode'],
            'contract-status': ['code', 'systemId', 'statusCode'],
            'contract-type': ['code', 'systemId', 'typeCode'],
            'external-authorization-countries': ['countryCode', 'code', 'systemId'],
            'fuel-type': ['code', 'systemId', 'fuelCode'],
            'id-type': ['code', 'systemId', 'idCode'],
            'payment-method': ['code', 'systemId', 'methodCode'],
            'yakeen-nationality': ['nationalityCode', 'code', 'systemId'],
            'gccNationality': ['nationalityCode', 'code', 'systemId'],
            'country': ['countryCode', 'code', 'systemId'],
            'closure-reasons': ['reasonCode', 'code', 'systemId'],
            'suspension-reasons': ['reasonCode', 'code', 'systemId'],
            'branch-all': ['license.licenseNumber', 'license.crNumber', 'branchCode', 'code', 'systemId'],
        }

        fields_to_check = code_fields.get(action, ['code', 'systemId', 'id'])

        for field in fields_to_check:
            # التحقق من الحقول المتداخلة مثل license.licenseNumber
            if '.' in field:
                parts = field.split('.')
                current_obj = item
                for part in parts:
                    if isinstance(current_obj, dict) and part in current_obj:
                        current_obj = current_obj[part]
                    else:
                        current_obj = None
                        break
                if current_obj is not None:
                    return current_obj
            else:
                # التحقق من الحقول العادية
                if field in item and item[field] is not None:
                    return item[field]

        return None

    def action_fetch_data(self):
        """جلب البيانات من STA API"""
        try:
            # تحديث الحالة إلى loading
            self.write({'state': 'loading'})

            # الحصول على URL
            api_url = self._get_api_url(self.lookup_action)
            if not api_url:
                raise ValueError(f"Invalid lookup action: {self.lookup_action}")

            # إعداد Headers
            headers = self._get_api_headers()
            config = self._get_api_config()
            timeout = config.get('sta_connection_timeout', 30)

            _logger.info(f"Fetching data from: {api_url}")
            _logger.info(f"Headers: {headers}")

            # إرسال الطلب
            response = requests.get(api_url, headers=headers, timeout=timeout)

            _logger.info(f"Response status: {response.status_code}")
            _logger.info(f"Response content: {response.text[:500]}...")

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON response from API")

                # حفظ البيانات الخام الكاملة
                raw_data = json.dumps(data, indent=2, ensure_ascii=False)

                # مسح البيانات السابقة
                self.api_lines_ids.unlink()

                # معالجة البيانات
                records_data = self._process_response_data(data, self.lookup_action)

                # إنشاء السجلات
                if records_data:
                    self.env['api.lookup.lines'].create(records_data)

                # تحديث الحالة
                self.write({
                    'url': api_url,
                    'total_records': len(records_data),
                    'last_sync': fields.Datetime.now(),
                    'state': 'loaded',
                    'response_message': f"✅ Successfully loaded {len(records_data)} records from {self.lookup_action.replace('-', ' ').title()}.",
                    'raw_response_data': raw_data
                })

                _logger.info(f"Successfully processed {len(records_data)} records for {self.lookup_action}")

            elif response.status_code == 401:
                error_msg = "❌ Authentication failed. Please check your API credentials (app-id, app-key, Authorization token)."
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

            elif response.status_code == 403:
                error_msg = "❌ Access forbidden. Your API credentials don't have permission to access this resource."
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

            elif response.status_code == 404:
                error_msg = f"❌ API endpoint not found: {api_url}"
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

            elif response.status_code == 429:
                error_msg = "❌ Too many requests. Please wait and try again later."
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

            elif response.status_code == 500:
                error_msg = "❌ Internal server error. The API server encountered an error."
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

            else:
                error_msg = f"❌ API Error: {response.status_code} - {response.text[:200]}"
                self.write({
                    'state': 'error',
                    'response_message': error_msg,
                    'total_records': 0,
                    'url': api_url
                })

        except requests.exceptions.Timeout:
            error_msg = "❌ Request timeout. The API server took too long to respond."
            self.write({
                'state': 'error',
                'response_message': error_msg,
                'total_records': 0
            })

        except requests.exceptions.ConnectionError:
            error_msg = "❌ Connection error. Please check your internet connection and API URL."
            self.write({
                'state': 'error',
                'response_message': error_msg,
                'total_records': 0
            })

        except json.JSONDecodeError:
            error_msg = "❌ Invalid JSON response from API."
            self.write({
                'state': 'error',
                'response_message': error_msg,
                'total_records': 0
            })

        except ValueError as e:
            error_msg = f"❌ Value error: {str(e)}"
            self.write({
                'state': 'error',
                'response_message': error_msg,
                'total_records': 0
            })

        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            _logger.error(f"API Lookup Error: {error_msg}")
            self.write({
                'state': 'error',
                'response_message': error_msg,
                'total_records': 0
            })

        # إعادة نفس الـ wizard بدلاً من إغلاقه
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'api.lookup.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_clear_data(self):
        """مسح البيانات"""
        self.api_lines_ids.unlink()
        self.write({
            'state': 'draft',
            'response_message': False,
            'total_records': 0,
            'last_sync': False,
            'raw_response_data': False,
            'url': False
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'api.lookup.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_view_full_response(self):
        """عرض الاستجابة الكاملة"""
        action_labels = dict(self._fields['lookup_action'].selection)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Full API Response',
            'res_model': 'api.response.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Full Response - {action_labels.get(self.lookup_action, self.lookup_action)}',
                'default_content': self.raw_response_data or 'No data available',
                'default_content_type': 'json'
            }
        }

    def action_link_countries(self):
        """ربط البلدان والجنسيات التلقائي مع أودو"""
        if self.lookup_action not in ['country', 'yakeen-nationality']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'هذه الميزة متاحة فقط للبلدان (Country) والجنسيات (Yakeen Nationality)',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        if not self.api_lines_ids:
            data_type = 'البلدان' if self.lookup_action == 'country' else 'الجنسيات'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'يجب جلب بيانات {data_type} أولاً',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        try:
            # تحديد النوع والحقل المناسب
            is_country = self.lookup_action == 'country'
            field_name = 'naql_id' if is_country else 'nationality_naql_id'
            data_type = 'البلدان' if is_country else 'الجنسيات'

            # إحصائيات
            total_naql_items = len(self.api_lines_ids)
            matched_countries = 0
            new_links = 0
            existing_links = 0
            not_found_in_odoo = 0

            # الحصول على جميع البلدان في أودو
            odoo_countries = self.env['res.country'].search([])

            # معالجة كل عنصر من نقل
            for naql_item in self.api_lines_ids:

                naql_id = naql_item.transfer_id
                naql_ar_name = naql_item.ar_name
                naql_en_name = naql_item.en_name
                naql_code = naql_item.system_id

                # طباعة لوج للتشخيص
                _logger.info(
                    f"Processing {data_type}: ID={naql_id}, AR='{naql_ar_name}', EN='{naql_en_name}', Code='{naql_code}'")

                # البحث عن مطابقة في أودو
                matched_country = self._find_matching_country(odoo_countries, naql_ar_name, naql_en_name, naql_code)

                # إذا وجدنا مطابقة
                if matched_country:
                    matched_countries += 1

                    # التحقق من وجود ربط سابق في الحقل المناسب
                    current_value = getattr(matched_country, field_name)

                    if current_value:
                        if current_value == naql_id:
                            existing_links += 1
                            _logger.info(
                                f"{data_type} already linked: {matched_country.name} -> {field_name}={naql_id}")
                        else:
                            # تحديث الربط
                            old_id = current_value
                            setattr(matched_country, field_name, naql_id)
                            new_links += 1
                            _logger.info(
                                f"{data_type} updated: {matched_country.name} -> {field_name}: {old_id} -> {naql_id}")
                    else:
                        # إضافة ربط جديد
                        setattr(matched_country, field_name, naql_id)
                        new_links += 1
                        _logger.info(f"{data_type} linked: {matched_country.name} -> {field_name}={naql_id}")

                else:
                    not_found_in_odoo += 1
                    _logger.warning(f"{data_type} not found in Odoo: {naql_ar_name} / {naql_en_name}")

            # إعداد رسالة النتيجة
            success_msg = f"""
🌍 **تم ربط {data_type} بنجاح!**

📊 **الإحصائيات:**
• إجمالي {data_type} في نقل: {total_naql_items}
• تم العثور على مطابقات: {matched_countries}
• روابط جديدة: {new_links}
• روابط موجودة مسبقاً: {existing_links}
• غير موجودة في أودو: {not_found_in_odoo}

✅ تم تحديث {new_links} من {data_type} بمعرفات نقل الجديدة في حقل {field_name}.
            """

            # تحديث رسالة الاستجابة
            self.write({'response_message': success_msg})

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'تم ربط {matched_countries} من {data_type} بنجاح! ({new_links} روابط جديدة)',
                    'type': 'success',
                    'sticky': True,
                }
            }

        except Exception as e:
            error_msg = f"خطأ في ربط {data_type}: {str(e)}"
            _logger.error(error_msg)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }


    def _find_matching_country(self, odoo_countries, naql_ar_name, naql_en_name, naql_code):
        """البحث عن مطابقة للدولة في أودو - محدث للاعتماد على الأسماء فقط"""
        matched_country = None

        # تنظيف الأسماء من المسافات الزائدة
        clean_ar_name = naql_ar_name.strip() if naql_ar_name else ''
        clean_en_name = naql_en_name.strip() if naql_en_name else ''

        _logger.info(
            f"Searching for country: AR='{clean_ar_name}', EN='{clean_en_name}', Code='{naql_code}' (code ignored)")

        # 1. البحث بالاسم الإنجليزي أولاً (مطابقة تامة)
        if clean_en_name:
            matched_country = odoo_countries.filtered(
                lambda c: c.name and c.name.lower().strip() == clean_en_name.lower()
            )
            if matched_country:
                _logger.info(f"Found exact English match: {matched_country[0].name}")

        # 2. البحث المرن بالاسم الإنجليزي (يحتوي على)
        if not matched_country and clean_en_name:
            for country in odoo_countries:
                if country.name:
                    # البحث في الاتجاهين
                    if (clean_en_name.lower() in country.name.lower()) or \
                            (country.name.lower() in clean_en_name.lower()):
                        matched_country = country
                        _logger.info(f"Found partial English match: {country.name} <-> {clean_en_name}")
                        break

        # 3. مطابقة خاصة بالأسماء العربية والإنجليزية للبلدان الشائعة
        if not matched_country:
            # خريطة مطابقة محسنة للبلدان العربية
            country_mapping = {
                # العراق
                'العراق': ['Iraq', 'IQ'],
                'عراق': ['Iraq', 'IQ'],
                'عراقي': ['Iraq', 'IQ'],
                'عراقية': ['Iraq', 'IQ'],

                # السعودية
                'السعودية': ['Saudi Arabia', 'SA'],
                'سعودية': ['Saudi Arabia', 'SA'],
                'سعودي': ['Saudi Arabia', 'SA'],
                'المملكة العربية السعودية': ['Saudi Arabia', 'SA'],

                # مصر
                'مصر': ['Egypt', 'EG'],
                'مصري': ['Egypt', 'EG'],
                'مصرية': ['Egypt', 'EG'],
                'جمهورية مصر العربية': ['Egypt', 'EG'],

                # الأردن
                'الأردن': ['Jordan', 'JO'],
                'أردن': ['Jordan', 'JO'],
                'أردني': ['Jordan', 'JO'],
                'أردنية': ['Jordan', 'JO'],
                'المملكة الأردنية الهاشمية': ['Jordan', 'JO'],

                # الكويت
                'الكويت': ['Kuwait', 'KW'],
                'كويت': ['Kuwait', 'KW'],
                'كويتي': ['Kuwait', 'KW'],
                'كويتية': ['Kuwait', 'KW'],
                'دولة الكويت': ['Kuwait', 'KW'],

                # الإمارات
                'الإمارات': ['United Arab Emirates', 'AE'],
                'إمارات': ['United Arab Emirates', 'AE'],
                'إماراتي': ['United Arab Emirates', 'AE'],
                'إماراتية': ['United Arab Emirates', 'AE'],
                'الإمارات العربية المتحدة': ['United Arab Emirates', 'AE'],
                'دولة الإمارات العربية المتحدة': ['United Arab Emirates', 'AE'],

                # قطر
                'قطر': ['Qatar', 'QA'],
                'قطري': ['Qatar', 'QA'],
                'قطرية': ['Qatar', 'QA'],
                'دولة قطر': ['Qatar', 'QA'],

                # البحرين
                'البحرين': ['Bahrain', 'BH'],
                'بحرين': ['Bahrain', 'BH'],
                'بحريني': ['Bahrain', 'BH'],
                'بحرينية': ['Bahrain', 'BH'],
                'مملكة البحرين': ['Bahrain', 'BH'],

                # عمان
                'عمان': ['Oman', 'OM'],
                'عماني': ['Oman', 'OM'],
                'عمانية': ['Oman', 'OM'],
                'سلطنة عمان': ['Oman', 'OM'],

                # لبنان
                'لبنان': ['Lebanon', 'LB'],
                'لبناني': ['Lebanon', 'LB'],
                'لبنانية': ['Lebanon', 'LB'],
                'الجمهورية اللبنانية': ['Lebanon', 'LB'],

                # سوريا
                'سوريا': ['Syria', 'SY'],
                'سوري': ['Syria', 'SY'],
                'سورية': ['Syria', 'SY'],
                'الجمهورية العربية السورية': ['Syria', 'SY'],

                # اليمن
                'اليمن': ['Yemen', 'YE'],
                'يمن': ['Yemen', 'YE'],
                'يمني': ['Yemen', 'YE'],
                'يمنية': ['Yemen', 'YE'],
                'الجمهورية اليمنية': ['Yemen', 'YE'],

                # فلسطين
                'فلسطين': ['Palestine', 'PS'],
                'فلسطيني': ['Palestine', 'PS'],
                'فلسطينية': ['Palestine', 'PS'],
                'دولة فلسطين': ['Palestine', 'PS'],

                # المغرب
                'المغرب': ['Morocco', 'MA'],
                'مغرب': ['Morocco', 'MA'],
                'مغربي': ['Morocco', 'MA'],
                'مغربية': ['Morocco', 'MA'],
                'المملكة المغربية': ['Morocco', 'MA'],

                # الجزائر
                'الجزائر': ['Algeria', 'DZ'],
                'جزائر': ['Algeria', 'DZ'],
                'جزائري': ['Algeria', 'DZ'],
                'جزائرية': ['Algeria', 'DZ'],
                'الجمهورية الجزائرية الديمقراطية الشعبية': ['Algeria', 'DZ'],

                # تونس
                'تونس': ['Tunisia', 'TN'],
                'تونسي': ['Tunisia', 'TN'],
                'تونسية': ['Tunisia', 'TN'],
                'الجمهورية التونسية': ['Tunisia', 'TN'],

                # ليبيا
                'ليبيا': ['Libya', 'LY'],
                'ليبي': ['Libya', 'LY'],
                'ليبية': ['Libya', 'LY'],
                'دولة ليبيا': ['Libya', 'LY'],

                # السودان
                'السودان': ['Sudan', 'SD'],
                'سودان': ['Sudan', 'SD'],
                'سوداني': ['Sudan', 'SD'],
                'سودانية': ['Sudan', 'SD'],
                'جمهورية السودان': ['Sudan', 'SD'],

                # إيران
                'إيران': ['Iran', 'IR'],
                'ايران': ['Iran', 'IR'],
                'إيراني': ['Iran', 'IR'],
                'إيرانية': ['Iran', 'IR'],
                'جمهورية إيران الإسلامية': ['Iran', 'IR'],

                # تركيا
                'تركيا': ['Turkey', 'TR'],
                'تركي': ['Turkey', 'TR'],
                'تركية': ['Turkey', 'TR'],
                'الجمهورية التركية': ['Turkey', 'TR'],

                # الهند
                'الهند': ['India', 'IN'],
                'هند': ['India', 'IN'],
                'هندي': ['India', 'IN'],
                'هندية': ['India', 'IN'],
                'جمهورية الهند': ['India', 'IN'],

                # باكستان
                'باكستان': ['Pakistan', 'PK'],
                'باكستاني': ['Pakistan', 'PK'],
                'باكستانية': ['Pakistan', 'PK'],
                'جمهورية باكستان الإسلامية': ['Pakistan', 'PK'],

                # بنغلاديش
                'بنغلاديش': ['Bangladesh', 'BD'],
                'بنغلادش': ['Bangladesh', 'BD'],
                'بنغلاديشي': ['Bangladesh', 'BD'],
                'بنغلاديشية': ['Bangladesh', 'BD'],

                # الفلبين
                'الفلبين': ['Philippines', 'PH'],
                'فلبين': ['Philippines', 'PH'],
                'فلبيني': ['Philippines', 'PH'],
                'فلبينية': ['Philippines', 'PH'],

                # إندونيسيا
                'إندونيسيا': ['Indonesia', 'ID'],
                'اندونيسيا': ['Indonesia', 'ID'],
                'إندونيسي': ['Indonesia', 'ID'],
                'إندونيسية': ['Indonesia', 'ID'],
            }

            # البحث في الاسم العربي
            if clean_ar_name:
                for ar_variant, (en_name, iso_code) in country_mapping.items():
                    if ar_variant in clean_ar_name or clean_ar_name in ar_variant:
                        # البحث بالاسم الإنجليزي المطابق
                        matched_country = odoo_countries.filtered(
                            lambda c: c.name and en_name.lower() in c.name.lower()
                        )
                        if matched_country:
                            _logger.info(f"Found Arabic mapping: {clean_ar_name} -> {en_name} -> {matched_country[0].name}")
                            break

                        # البحث بالكود كـ fallback
                        matched_country = odoo_countries.filtered(lambda c: c.code == iso_code)
                        if matched_country:
                            _logger.info(
                                f"Found Arabic mapping by code: {clean_ar_name} -> {iso_code} -> {matched_country[0].name}")
                            break

            # البحث في الاسم الإنجليزي إذا لم نجد في العربي
            if not matched_country and clean_en_name:
                # البحث المباشر في الخريطة
                for ar_variant, (en_name, iso_code) in country_mapping.items():
                    if en_name.lower() == clean_en_name.lower() or \
                            clean_en_name.lower() in en_name.lower() or \
                            en_name.lower() in clean_en_name.lower():

                        # البحث بالاسم الإنجليزي
                        matched_country = odoo_countries.filtered(
                            lambda c: c.name and en_name.lower() in c.name.lower()
                        )
                        if matched_country:
                            _logger.info(
                                f"Found English mapping: {clean_en_name} -> {en_name} -> {matched_country[0].name}")
                            break

                        # البحث بالكود كـ fallback
                        matched_country = odoo_countries.filtered(lambda c: c.code == iso_code)
                        if matched_country:
                            _logger.info(
                                f"Found English mapping by code: {clean_en_name} -> {iso_code} -> {matched_country[0].name}")
                            break

        # 4. البحث بالكلمات المفتاحية المتقدم
        if not matched_country:
            # كلمات مفتاحية للبحث
            ar_keywords = {
                'عراق': ['Iraq', 'IQ'],
                'سعود': ['Saudi Arabia', 'SA'],
                'مصر': ['Egypt', 'EG'],
                'أردن': ['Jordan', 'JO'],
                'كويت': ['Kuwait', 'KW'],
                'إمارات': ['United Arab Emirates', 'AE'],
                'قطر': ['Qatar', 'QA'],
                'بحرين': ['Bahrain', 'BH'],
                'عمان': ['Oman', 'OM'],
                'لبنان': ['Lebanon', 'LB'],
                'سوري': ['Syria', 'SY'],
                'يمن': ['Yemen', 'YE'],
                'فلسطين': ['Palestine', 'PS'],
                'مغرب': ['Morocco', 'MA'],
                'جزائر': ['Algeria', 'DZ'],
                'تونس': ['Tunisia', 'TN'],
                'ليبي': ['Libya', 'LY'],
                'سودان': ['Sudan', 'SD'],
            }

            if clean_ar_name:
                for keyword, (en_name, iso_code) in ar_keywords.items():
                    if keyword in clean_ar_name:
                        matched_country = odoo_countries.filtered(lambda c: c.code == iso_code)
                        if matched_country:
                            _logger.info(
                                f"Found by Arabic keyword: {keyword} in {clean_ar_name} -> {matched_country[0].name}")
                            break

        if matched_country:
            _logger.info(
                f"Successfully matched: {clean_ar_name}/{clean_en_name} -> {matched_country[0].name} ({matched_country[0].code})")
        else:
            _logger.warning(f"No match found for: {clean_ar_name}/{clean_en_name}")

        return matched_country[0] if matched_country else None

class ApiLookupLines(models.TransientModel):
    _name = 'api.lookup.lines'
    _description = 'API Lookup Lines'

    wizard_id = fields.Many2one('api.lookup.wizard', string='Wizard', ondelete='cascade')
    description = fields.Char('Description')
    transfer_id = fields.Char('Transfer ID')
    system_id = fields.Char('System ID')
    ar_name = fields.Char('Arabic Name', help='Arabic name from API response')
    en_name = fields.Char('English Name', help='English name from API response')

    # حقول إضافية للفروع
    city_ar_name = fields.Char('City Arabic Name', help='Arabic city name for branches')
    region_ar_name = fields.Char('Region Arabic Name', help='Arabic region name for branches')
    district_ar = fields.Char('District Arabic', help='Arabic district name for branches')

    raw_data = fields.Text('Raw Data')

    def action_view_raw_data(self):
        """عرض البيانات الخام لهذا السجل"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Raw Data - {self.description}',
            'res_model': 'api.response.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Raw Data - {self.description}',
                'default_content': self.raw_data or 'No data available',
                'default_content_type': 'json'
            }
        }


class ApiResponseViewer(models.TransientModel):
    _name = 'api.response.viewer'
    _description = 'API Response Viewer'

    title = fields.Char('Title', readonly=True)
    content = fields.Text('Content', readonly=True)
    content_type = fields.Selection([
        ('json', 'JSON'),
        ('text', 'Text'),
        ('xml', 'XML')
    ], default='json', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """تعيين القيم الافتراضية من السياق"""
        result = super().default_get(fields_list)

        if self.env.context.get('default_title'):
            result['title'] = self.env.context['default_title']
        if self.env.context.get('default_content'):
            result['content'] = self.env.context['default_content']
        if self.env.context.get('default_content_type'):
            result['content_type'] = self.env.context['default_content_type']

        return result