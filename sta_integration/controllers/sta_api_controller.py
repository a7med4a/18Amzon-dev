# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime
from odoo import http, _, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class STAAPIController:
    """Controller for handling STA API calls"""

    def __init__(self, env=None):
        """Initialize controller with optional environment"""
        self.env = env or (http.request.env if http.request else None)
        self.config = self._get_config()
        self._validate_config()

    def _get_config(self):
        """Get STA configuration from system parameters or company settings"""
        if not self.env:
            return {}

        # محاولة الحصول على الإعدادات من system parameters أولاً
        config = {
            'app_id': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_app_id'),
            'app_key': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_app_key'),
            'authorization_token': self.env['ir.config_parameter'].sudo().get_param(
                'sta_integration.sta_authorization_token'),
            'base_url': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_base_url'),
            'is_production': self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_is_production',
                                                                              'False') == 'True',
            'connection_timeout': int(
                self.env['ir.config_parameter'].sudo().get_param('sta_integration.sta_connection_timeout', '30'))
        }

        # إذا لم تكن الإعدادات متوفرة في system parameters، احصل عليها من الشركة الحالية
        if not config.get('app_id'):
            company = self.env.company
            config.update({
                'app_id': company.sta_app_id,
                'app_key': company.sta_app_key,
                'authorization_token': company.sta_authorization_token,
                'base_url': company.sta_base_url or 'https://tajeer-stg.api.elm.sa',
                'is_production': company.sta_is_production,
                'connection_timeout': company.sta_connection_timeout or 30
            })

        return config

    def _validate_config(self):
        """Validate that required configuration is available"""
        required_fields = ['app_id', 'app_key', 'authorization_token', 'base_url']
        missing_fields = [field for field in required_fields if not self.config.get(field)]

        if missing_fields:
            _logger.warning(f"Missing STA configuration: {', '.join(missing_fields)}")

    def _get_headers(self, content_type='application/json'):
        """Get standard headers for STA API requests"""
        headers = {
            'Content-Type': content_type,
            'Accept': 'application/json',
            'User-Agent': 'Odoo-STA-Integration/1.0',
            'app-id': str(self.config.get('app_id', '')),
            'app-key': str(self.config.get('app_key', '')),
            'Authorization': str(self.config.get('authorization_token', ''))
        }

        # إزالة headers الفارغة
        headers = {k: v for k, v in headers.items() if v}

        return headers

    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to STA API with enhanced error handling"""
        base_url = self.config.get('base_url', '').rstrip('/')
        url = f"{base_url}{endpoint}"
        headers = self._get_headers()
        timeout = self.config.get('connection_timeout', 30)

        _logger.info(f"🔄 Making {method.upper()} request to: {url}")
        _logger.debug(f"📋 Headers: {headers}")

        if data:
            _logger.debug(f"📤 Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

        try:
            # إعداد الطلب حسب النوع
            request_kwargs = {
                'headers': headers,
                'timeout': timeout,
                'verify': True  # للتحقق من SSL
            }

            if params:
                request_kwargs['params'] = params

            if data and method.upper() in ['POST', 'PUT']:
                request_kwargs['json'] = data

            # إرسال الطلب
            if method.upper() == 'GET':
                response = requests.get(url, **request_kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **request_kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, **request_kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **request_kwargs)
            else:
                raise ValueError(f"❌ Unsupported HTTP method: {method}")

            _logger.info(f"📥 Response status: {response.status_code}")
            _logger.debug(f"📝 Response headers: {dict(response.headers)}")

            # محاولة تحليل الاستجابة JSON
            try:
                response_data = response.json()
                _logger.debug(f"📋 Response data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except (ValueError, json.JSONDecodeError):
                response_data = {
                    'raw_response': response.text,
                    'content_type': response.headers.get('content-type', 'unknown')
                }
                _logger.warning(f"⚠️ Failed to parse JSON response. Content: {response.text[:500]}")

            # تحديد نجاح الطلب
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'response': response_data,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            else:
                # استخراج رسالة الخطأ
                if isinstance(response_data, dict):
                    error_message = (
                            response_data.get('message') or
                            response_data.get('error') or
                            response_data.get('detail') or
                            response.text
                    )
                else:
                    error_message = response.text

                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {error_message}",
                    'response': response_data,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }

        except requests.exceptions.Timeout:
            error_msg = f'⏱️ Request timeout after {timeout} seconds'
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'timeout'
            }

        except requests.exceptions.SSLError as e:
            error_msg = f'🔒 SSL Certificate error: {str(e)}'
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'ssl_error'
            }

        except requests.exceptions.ConnectionError as e:
            error_msg = f'🔌 Connection error: Unable to connect to STA API. {str(e)}'
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'connection_error'
            }

        except requests.exceptions.RequestException as e:
            error_msg = f'📡 Request error: {str(e)}'
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'request_error'
            }

        except Exception as e:
            error_msg = f'❌ Unexpected error: {str(e)}'
            _logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }

    def test_connection(self):
        """Test connection to STA API by attempting to get branches"""
        _logger.info("🧪 Testing STA API connection...")

        # التحقق من الإعدادات المطلوبة
        required_config = ['app_id', 'app_key', 'authorization_token', 'base_url']
        missing_config = [key for key in required_config if not self.config.get(key)]

        if missing_config:
            error_msg = f"❌ Missing configuration parameters: {', '.join(missing_config)}"
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'missing_config': missing_config
            }

        # اختبار الاتصال بالحصول على قائمة الفروع
        result = self.get_branches()

        if result.get('success'):
            branches_count = len(result.get('branches', []))
            _logger.info(f"✅ STA API connection test successful! Found {branches_count} branches")
            result['test_success'] = True
            result['message'] = f"Connection successful - Found {branches_count} branches"
        else:
            _logger.error(f"❌ STA API connection test failed: {result.get('error')}")
            result['test_success'] = False

        return result

    def get_branches(self):
        """Get all branches from STA system"""
        _logger.info("📍 Fetching branches from STA API...")
        endpoint = '/rental-api/branch/all'
        result = self._make_request('GET', endpoint)

        if result.get('success'):
            # استخراج الفروع من الاستجابة
            response_data = result.get('response', {})

            if isinstance(response_data, list):
                branches = response_data
            elif isinstance(response_data, dict):
                branches = (
                        response_data.get('branches') or
                        response_data.get('data') or
                        response_data.get('result') or
                        []
                )
            else:
                branches = []

            result['branches'] = branches
            _logger.info(f"✅ Successfully fetched {len(branches)} branches")

            # طباعة معلومات الفروع للتتبع
            for branch in branches[:3]:  # طباعة أول 3 فروع فقط
                _logger.debug(f"🏢 Branch: {branch}")

        else:
            _logger.error(f"❌ Failed to fetch branches: {result.get('error')}")

        return result

    def get_rent_policies(self):
        """Get all rental policies from STA system"""
        _logger.info("📋 Fetching rental policies from STA API...")
        endpoint = '/rental-api/rent-policy/all'
        result = self._make_request('GET', endpoint)

        if result.get('success'):
            # استخراج السياسات من الاستجابة
            response_data = result.get('response', {})

            if isinstance(response_data, list):
                policies = response_data
            elif isinstance(response_data, dict):
                policies = (
                        response_data.get('policies') or
                        response_data.get('data') or
                        response_data.get('result') or
                        []
                )
            else:
                policies = []

            result['policies'] = policies
            _logger.info(f"✅ Successfully fetched {len(policies)} rental policies")

        else:
            _logger.error(f"❌ Failed to fetch rental policies: {result.get('error')}")

        return result

    def create_contract(self, sta_contract):
        """Create contract in STA system"""
        _logger.info(f"📝 Creating contract in STA: {sta_contract.sta_contract_number}")
        endpoint = '/rental-api/rent-contract/create'

        # إعداد بيانات العقد
        data = {
            'contractNumber': sta_contract.sta_contract_number or '',
            'operatorId': sta_contract.operator_id or '1028558326',
            'workingBranchId': sta_contract.working_branch_id.sta_branch_id if sta_contract.working_branch_id else 10583,
            'renterOTPValue': '404012',  # يجب أن يكون ديناميكي في الإنتاج
            'otpValue': '404012',  # يجب أن يكون ديناميكي في الإنتاج
            'vehicleOwnerIdVersion': sta_contract.vehicle_owner_id_version or 1
        }

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            response_data = result.get('response', {})
            contract_number = response_data.get('contractNumber') or response_data.get('contract_number')
            if contract_number:
                result['contract_number'] = contract_number
                _logger.info(f"✅ Contract created successfully: {contract_number}")
            else:
                _logger.warning("⚠️ Contract created but no contract number returned")
        else:
            _logger.error(f"❌ Failed to create contract: {result.get('error')}")

        return result

    def send_otp(self, contract_number):
        """Send OTP for contract verification"""
        _logger.info(f"📱 Sending OTP for contract: {contract_number}")
        endpoint = f'/rental-api/rent-contract/{contract_number}/send-otp'
        result = self._make_request('GET', endpoint)

        if result.get('success'):
            _logger.info(f"✅ OTP sent successfully for contract: {contract_number}")
        else:
            _logger.error(f"❌ Failed to send OTP for contract {contract_number}: {result.get('error')}")

        return result

    def cancel_contract(self, contract_number, cancellation_reason):
        """Cancel contract in STA system"""
        _logger.info(f"❌ Cancelling contract: {contract_number}")
        endpoint = f'/rental-api/rent-contract/{contract_number}/cancel'
        data = {
            'cancellationReason': cancellation_reason
        }
        result = self._make_request('PUT', endpoint, data)

        if result.get('success'):
            _logger.info(f"✅ Contract cancelled successfully: {contract_number}")
        else:
            _logger.error(f"❌ Failed to cancel contract {contract_number}: {result.get('error')}")

        return result

    def save_contract(self, sta_contract):
        """Save complete contract details to STA"""
        _logger.info(f"💾 Saving complete contract details: {sta_contract.sta_contract_number}")
        endpoint = '/rental-api/rent-contract'

        # الحصول على بيانات عقد الإيجار
        rental_contract = sta_contract.rental_contract_id
        if not rental_contract:
            return {
                'success': False,
                'error': 'No rental contract linked to STA contract'
            }

        # إعداد بيانات المستأجر
        customer = rental_contract.partner_id
        renter_data = {
            'personAddress': customer.street or 'Saudi Arabia',
            'email': customer.email or '',
            'mobile': customer.mobile or customer.phone or '',
            'idTypeCode': '1',
            'idNumber': customer.vat or '77557755',
            'passportNumber': customer.vat or '77557755',
            'hijriBirthDate': '20000605'
        }

        # إعداد تفاصيل الدفع
        payment_data = {
            'extraKmCost': 100.0,
            'rentDayCost': 750,
            'fullFuelCost': 1500,
            'driverFarePerDay': 0,
            'driverFarePerHour': 0,
            'vehicleTransferCost': 150,
            'internationalAuthorizationCost': 150,
            'discount': 0,
            'paid': 3322.35,
            'extraDriverCost': 140,
            'paymentMethodCode': 3,
            'otherPaymentMethodCode': 0,
            'additionalCoverageCost': 150
        }

        # إعداد تفاصيل المركبة
        vehicle = rental_contract.vehicle_id
        vehicle_data = {
            'plateNumber': vehicle.license_plate or '1234',
            'firstChar': 'د',
            'secondChar': 'ط',
            'thirdChar': 'ه',
            'plateType': 1
        }

        # إعداد حالة الإيجار
        rent_status = {
            'ac': 1,
            'carSeats': 6,
            'fireExtinguisher': 8,
            'firstAidKit': 8,
            'keys': 4,
            'radioStereo': 1,
            'safetyTriangle': 8,
            'screen': 1,
            'spareTire': 1,
            'spareTireTools': 8,
            'speedometer': 4,
            'tires': 1,
            'sketchInfo': '[]',
            'notes': '0',
            'availableFuel': 1,
            'odometerReading': vehicle.odometer or 1000,
            'other1': '0',
            'other2': '0',
            'oilChangeKmDistance': 3000,
            'enduranceAmount': 0,
            'fuelTypeCode': 2,
            'oilChangeDate': '2025-06-18T00:00',
            'additionalInsurance': 20013,
            'oilType': 'shell'
        }

        # إعداد تفاصيل التفويض
        auth_details = {
            'authorizationTypeCode': '2',
            'authorizationEndDate': '2024-09-09T00:00',
            'tammExternalAuthorizationCountries': [
                {'id': 1, 'code': 1},
                {'id': 2, 'code': 2},
                {'id': 5, 'code': 5}
            ]
        }

        # إعداد بيانات العقد الكاملة
        data = {
            'renter': renter_data,
            'paymentDetails': payment_data,
            'vehicleDetails': vehicle_data,
            'rentStatus': rent_status,
            'workingBranchId': sta_contract.working_branch_id.sta_branch_id if sta_contract.working_branch_id else 10965,
            'rentPolicyId': sta_contract.rent_policy_id.sta_policy_id if sta_contract.rent_policy_id else 77,
            'contractStartDate': rental_contract.date_start.strftime(
                '%Y-%m-%dT%H:%M') if rental_contract.date_start else '2024-07-25T00:00',
            'contractEndDate': rental_contract.date_end.strftime(
                '%Y-%m-%dT%H:%M') if rental_contract.date_end else '2024-07-26T00:00',
            'authorizationDetails': auth_details,
            'allowedKmPerHour': 0,
            'unlimitedKm': True,
            'receiveBranchId': sta_contract.receive_branch_id.sta_branch_id if sta_contract.receive_branch_id else 10965,
            'returnBranchId': sta_contract.return_branch_id.sta_branch_id if sta_contract.return_branch_id else 10965,
            'allowedKmPerDay': 250.0,
            'contractTypeCode': '1',
            'allowedLateHours': 10,
            'operatorId': int(sta_contract.operator_id) if sta_contract.operator_id else 1028558326
        }

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            _logger.info(f"✅ Contract saved successfully: {sta_contract.sta_contract_number}")
        else:
            _logger.error(f"❌ Failed to save contract: {result.get('error')}")

        return result

    def suspend_contract(self, contract_data):
        """Suspend contract in STA system"""
        _logger.info("⏸️ Suspending contract in STA")
        endpoint = '/rental-api/rent-contract/suspension'
        result = self._make_request('PUT', endpoint, contract_data)

        if result.get('success'):
            _logger.info("✅ Contract suspended successfully")
        else:
            _logger.error(f"❌ Failed to suspend contract: {result.get('error')}")

        return result

    def close_contract(self, contract_data):
        """Close contract in STA system"""
        _logger.info("🔚 Closing contract in STA")
        endpoint = '/rental-api/rent-contract/closure'
        result = self._make_request('PUT', endpoint, contract_data)

        if result.get('success'):
            _logger.info("✅ Contract closed successfully")
        else:
            _logger.error(f"❌ Failed to close contract: {result.get('error')}")

        return result


class STAWebController(http.Controller):
    """Web controller for STA integration endpoints"""

    @http.route('/sta/test_connection', type='json', auth='user', methods=['POST'])
    def test_sta_connection(self):
        """Test STA API connection via web endpoint"""
        try:
            _logger.info("🌐 Web endpoint: Testing STA API connection")
            api_controller = STAAPIController()
            result = api_controller.test_connection()

            if result.get('success'):
                _logger.info("✅ Web endpoint: STA connection test successful")
            else:
                _logger.error(f"❌ Web endpoint: STA connection test failed: {result.get('error')}")

            return result
        except Exception as e:
            error_msg = f"Web endpoint error: {str(e)}"
            _logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    @http.route('/sta/sync_branches', type='json', auth='user', methods=['POST'])
    def sync_sta_branches(self):
        """Sync branches from STA via web endpoint"""
        try:
            _logger.info("🌐 Web endpoint: Syncing STA branches")

            # التحقق من وجود نموذج الفروع
            if 'sta.branch' not in http.request.env:
                return {
                    'success': False,
                    'error': 'STA Branch model not found. Please install the complete STA integration module.'
                }

            sta_branch_model = http.request.env['sta.branch']
            result = sta_branch_model.sync_branches_from_sta()

            if result.get('success'):
                _logger.info("✅ Web endpoint: STA branches synced successfully")
            else:
                _logger.error(f"❌ Web endpoint: STA branches sync failed: {result.get('error')}")

            return result
        except Exception as e:
            error_msg = f"Web endpoint error: {str(e)}"
            _logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    @http.route('/sta/sync_policies', type='json', auth='user', methods=['POST'])
    def sync_sta_policies(self):
        """Sync rental policies from STA via web endpoint"""
        try:
            _logger.info("🌐 Web endpoint: Syncing STA rental policies")

            # التحقق من وجود نموذج السياسات
            if 'sta.rent.policy' not in http.request.env:
                return {
                    'success': False,
                    'error': 'STA Rent Policy model not found. Please install the complete STA integration module.'
                }

            sta_policy_model = http.request.env['sta.rent.policy']
            result = sta_policy_model.sync_policies_from_sta()

            if result.get('success'):
                _logger.info("✅ Web endpoint: STA rental policies synced successfully")
            else:
                _logger.error(f"❌ Web endpoint: STA rental policies sync failed: {result.get('error')}")

            return result
        except Exception as e:
            error_msg = f"Web endpoint error: {str(e)}"
            _logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    @http.route('/sta/get_api_status', type='json', auth='user', methods=['POST'])
    def get_sta_api_status(self):
        """Get current STA API configuration status"""
        try:
            api_controller = STAAPIController()
            config = api_controller.config

            return {
                'success': True,
                'config_status': {
                    'app_id_configured': bool(config.get('app_id')),
                    'app_key_configured': bool(config.get('app_key')),
                    'authorization_configured': bool(config.get('authorization_token')),
                    'base_url_configured': bool(config.get('base_url')),
                    'is_production': config.get('is_production', False),
                    'base_url': config.get('base_url', ''),
                    'timeout': config.get('connection_timeout', 30)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }