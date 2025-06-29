# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime
from odoo import http, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NaqlAPIController:
    """Controller for handling Naql API calls"""
    
    def __init__(self):
        self.env = http.request.env if http.request else None
        self.config = self._get_config()
    
    def _get_config(self):
        """Get Naql configuration from system parameters"""
        if not self.env:
            return {}
        
        return {
            'app_id': self.env['ir.config_parameter'].sudo().get_param('sta_integration.app_id'),
            'app_key': self.env['ir.config_parameter'].sudo().get_param('sta_integration.app_key'),
            'authorization_token': self.env['ir.config_parameter'].sudo().get_param('sta_integration.authorization_token'),
            'base_url': self.env['ir.config_parameter'].sudo().get_param('sta_integration.base_url', 'https://tajeer-stg.api.elm.sa'),
            'is_production': self.env['ir.config_parameter'].sudo().get_param('sta_integration.is_production', False),
        }
    
    def _get_headers(self, content_type='application/json'):
        """Get standard headers for Naql API requests"""
        headers = {
            'Content-Type': content_type,
            'app-id': self.config.get('app_id', ''),
            'app-key': self.config.get('app_key', ''),
            'Authorization': self.config.get('authorization_token', ''),
        }
        return headers
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to Naql API"""
        url = f"{self.config.get('base_url', '')}{endpoint}"
        headers = self._get_headers()
        
        try:
            _logger.info(f"Making {method} request to {url}")
            _logger.debug(f"Headers: {headers}")
            _logger.debug(f"Data: {data}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            _logger.info(f"Response status: {response.status_code}")
            _logger.debug(f"Response content: {response.text}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {'raw_response': response.text}
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'response': response_data,
                    'status_code': response.status_code
                }
            else:
                error_message = response_data.get('message', response.text) if isinstance(response_data, dict) else response.text
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {error_message}",
                    'response': response_data,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - Naql API did not respond within 30 seconds'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error - Unable to connect to Naql API'
            }
        except Exception as e:
            _logger.error(f"Unexpected error in API request: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def test_connection(self):
        """Test connection to Naql API by getting branches"""
        return self.get_branches()
    
    def create_contract(self, sta_contract):
        """Create contract in Naql system"""
        endpoint = '/rental-api/rent-contract/create'
        
        # Prepare contract data
        data = {
            'contractNumber': sta_contract.sta_contract_number or '',
            'operatorId': sta_contract.operator_id or '1028558326',
            'workingBranchId': sta_contract.working_branch_id.sta_branch_id if sta_contract.working_branch_id else 10583,
            'renterOTPValue': '404012',  # This should be dynamic in production
            'otpValue': '404012',  # This should be dynamic in production
            'vehicleOwnerIdVersion': sta_contract.vehicle_owner_id_version or 1
        }
        
        result = self._make_request('POST', endpoint, data)
        
        if result.get('success'):
            # Extract contract number from response if available
            response_data = result.get('response', {})
            contract_number = response_data.get('contractNumber') or response_data.get('contract_number')
            if contract_number:
                result['contract_number'] = contract_number
        
        return result
    
    def send_otp(self, contract_number):
        """Send OTP for contract verification"""
        endpoint = f'/rental-api/rent-contract/{contract_number}/send-otp'
        return self._make_request('GET', endpoint)
    
    def save_contract(self, sta_contract):
        """Save complete contract details to Naql"""
        endpoint = '/rental-api/rent-contract'
        
        # Get rental contract data
        rental_contract = sta_contract.rental_contract_id
        if not rental_contract:
            return {
                'success': False,
                'error': 'No rental contract linked to Naql contract'
            }
        
        # Prepare renter data
        customer = rental_contract.partner_id
        renter_data = {
            'personAddress': customer.street or 'Saudi Arabia',
            'email': customer.email or '',
            'mobile': customer.mobile or customer.phone or '',
            'idTypeCode': '1',  # This should be mapped from customer data
            'idNumber': customer.vat or '77557755',  # This should be mapped properly
            'passportNumber': customer.vat or '77557755',  # This should be mapped properly
            'hijriBirthDate': '20000605'  # This should be calculated from birth date
        }
        
        # Prepare payment details
        payment_data = {
            'extraKmCost': 100.0,  # These should come from rental contract
            'rentDayCost': 750,
            'fullFuelCost': 1500,
            'driverFarePerDay': 0,
            'driverFarePerHour': 0,
            'vehicleTransferCost': 150,
            'internationalAuthorizationCost': 150,
            'discount': 0,
            'paid': 3322.35,  # This should come from actual payment
            'extraDriverCost': 140,
            'paymentMethodCode': 3,
            'otherPaymentMethodCode': 0,
            'additionalCoverageCost': 150
        }
        
        # Prepare vehicle details
        vehicle = rental_contract.vehicle_id
        vehicle_data = {
            'plateNumber': vehicle.license_plate or '1234',
            'firstChar': 'د',  # These should be extracted from license plate
            'secondChar': 'ط',
            'thirdChar': 'ه',
            'plateType': 1
        }
        
        # Prepare rent status
        rent_status = {
            'ac': 1,
            'carSeats': 6,  # This should come from vehicle data
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
        
        # Prepare authorization details
        auth_details = {
            'authorizationTypeCode': '2',
            'authorizationEndDate': '2024-09-09T00:00',
            'tammExternalAuthorizationCountries': [
                {'id': 1, 'code': 1},
                {'id': 2, 'code': 2},
                {'id': 5, 'code': 5}
            ]
        }
        
        # Prepare complete contract data
        data = {
            'renter': renter_data,
            'paymentDetails': payment_data,
            'vehicleDetails': vehicle_data,
            'rentStatus': rent_status,
            'workingBranchId': sta_contract.working_branch_id.sta_branch_id if sta_contract.working_branch_id else 10965,
            'rentPolicyId': sta_contract.rent_policy_id.sta_policy_id if sta_contract.rent_policy_id else 77,
            'contractStartDate': rental_contract.date_start.strftime('%Y-%m-%dT%H:%M') if rental_contract.date_start else '2024-07-25T00:00',
            'contractEndDate': rental_contract.date_end.strftime('%Y-%m-%dT%H:%M') if rental_contract.date_end else '2024-07-26T00:00',
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
        
        return self._make_request('POST', endpoint, data)
    
    def cancel_contract(self, contract_number, cancellation_reason):
        """Cancel contract in Naql system"""
        endpoint = f'/rental-api/rent-contract/{contract_number}/cancel'
        data = {
            'cancellationReason': cancellation_reason
        }
        return self._make_request('PUT', endpoint, data)
    
    def suspend_contract(self, contract_data):
        """Suspend contract in Naql system"""
        endpoint = '/rental-api/rent-contract/suspension'
        return self._make_request('PUT', endpoint, contract_data)
    
    def close_contract(self, contract_data):
        """Close contract in Naql system"""
        endpoint = '/rental-api/rent-contract/closure'
        return self._make_request('PUT', endpoint, contract_data)
    
    def get_branches(self):
        """Get all branches from Naql system"""
        endpoint = '/rental-api/branch/all'
        result = self._make_request('GET', endpoint)
        
        if result.get('success'):
            # Extract branches from response
            response_data = result.get('response', {})
            branches = response_data if isinstance(response_data, list) else response_data.get('branches', [])
            result['branches'] = branches
        print("result ==> ",result)
        return result
    
    def get_rent_policies(self):
        """Get all rental policies from Naql system"""
        endpoint = '/rental-api/rent-policy/all'
        result = self._make_request('GET', endpoint)
        
        if result.get('success'):
            # Extract policies from response
            response_data = result.get('response', {})
            policies = response_data if isinstance(response_data, list) else response_data.get('policies', [])
            result['policies'] = policies
        
        return result


class NaqlWebController(http.Controller):
    """Web controller for Naql integration endpoints"""
    
    @http.route('/sta/test_connection', type='json', auth='user', methods=['POST'])
    def test_sta_connection(self):
        """Test Naql API connection"""
        try:
            api_controller = NaqlAPIController()
            result = api_controller.test_connection()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/sta/sync_branches', type='json', auth='user', methods=['POST'])
    def sync_sta_branches(self):
        """Sync branches from Naql"""
        try:
            sta_branch_model = http.request.env['sta.branch']
            result = sta_branch_model.sync_branches_from_sta()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/sta/sync_policies', type='json', auth='user', methods=['POST'])
    def sync_sta_policies(self):
        """Sync rental policies from Naql"""
        try:
            sta_policy_model = http.request.env['sta.rent.policy']
            result = sta_policy_model.sync_policies_from_sta()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

