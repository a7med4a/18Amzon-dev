# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class STASuspendContractWizard(models.TransientModel):
    _name = 'sta.suspend.contract.wizard'
    _description = 'Suspend STA Contract'

    sta_contract_id = fields.Many2one(
        'sta.contract',
        string='STA Contract',
        required=True,
        help='STA contract to suspend'
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
    
    actual_return_branch_id = fields.Many2one(
        'sta.branch',
        string='Actual Return Branch',
        required=True,
        help='Branch where vehicle is actually returned'
    )
    
    suspension_code = fields.Selection([
        ('1', 'Early Return'),
        ('2', 'Late Return'),
        ('3', 'Damage'),
        ('4', 'Other'),
    ], string='Suspension Code', required=True, default='2')
    
    # Return Status Fields
    ac_status = fields.Selection([
        ('1', 'Working'),
        ('2', 'Not Working'),
        ('3', 'Damaged'),
    ], string='AC Status', default='1')
    
    car_seats = fields.Integer(string='Car Seats', default=6)
    fire_extinguisher = fields.Selection([
        ('1', 'Available'),
        ('8', 'Not Available'),
    ], string='Fire Extinguisher', default='8')
    
    first_aid_kit = fields.Selection([
        ('1', 'Available'),
        ('8', 'Not Available'),
    ], string='First Aid Kit', default='8')
    
    keys = fields.Selection([
        ('1', 'All Keys'),
        ('4', 'Missing Keys'),
        ('5', 'Damaged Keys'),
    ], string='Keys Status', default='5')
    
    radio_stereo = fields.Selection([
        ('1', 'Working'),
        ('2', 'Not Working'),
    ], string='Radio/Stereo', default='1')
    
    safety_triangle = fields.Selection([
        ('1', 'Available'),
        ('8', 'Not Available'),
    ], string='Safety Triangle', default='8')
    
    screen = fields.Selection([
        ('1', 'Working'),
        ('2', 'Not Working'),
    ], string='Screen', default='1')
    
    spare_tire = fields.Selection([
        ('1', 'Available'),
        ('2', 'Not Available'),
    ], string='Spare Tire', default='1')
    
    spare_tire_tools = fields.Selection([
        ('1', 'Available'),
        ('8', 'Not Available'),
    ], string='Spare Tire Tools', default='8')
    
    speedometer = fields.Selection([
        ('1', 'Working'),
        ('4', 'Not Working'),
        ('5', 'Damaged'),
    ], string='Speedometer', default='5')
    
    tires = fields.Selection([
        ('1', 'Good'),
        ('2', 'Damaged'),
    ], string='Tires', default='1')
    
    available_fuel = fields.Selection([
        ('1', 'Full'),
        ('2', 'Half'),
        ('3', 'Quarter'),
        ('4', 'Empty'),
    ], string='Available Fuel', default='1')
    
    odometer_reading = fields.Float(string='Odometer Reading', default=50000.0)
    sketch_info = fields.Text(string='Sketch Info', default='[]')
    notes = fields.Text(string='Notes')
    other1 = fields.Char(string='Other 1')
    other2 = fields.Char(string='Other 2')
    
    # Payment Details
    spare_parts_cost = fields.Float(string='Spare Parts Cost', default=0.0)
    damage_cost = fields.Float(string='Damage Cost', default=0.0)
    oil_change_cost = fields.Float(string='Oil Change Cost', default=0.0)
    payment_method_code = fields.Selection([
        ('1', 'Cash'),
        ('2', 'Credit Card'),
        ('3', 'Bank Transfer'),
    ], string='Payment Method', default='3')
    paid = fields.Float(string='Paid Amount', default=260.82)
    discount = fields.Float(string='Discount', default=0.0)

    def action_suspend_contract(self):
        """Suspend the contract in STA system"""
        self.ensure_one()
        
        if not self.sta_contract_id.sta_contract_number:
            raise UserError(_('Contract must be created in STA system first.'))
        
        if self.sta_contract_id.sta_status in ['cancelled', 'closed', 'suspended']:
            raise UserError(_('Contract is already cancelled, closed, or suspended.'))
        
        # Prepare suspension data
        suspension_data = {
            'contractNumber': self.sta_contract_id.sta_contract_number,
            'returnStatus': {
                'ac': int(self.ac_status),
                'carSeats': self.car_seats,
                'fireExtinguisher': int(self.fire_extinguisher),
                'firstAidKit': int(self.first_aid_kit),
                'keys': int(self.keys),
                'radioStereo': int(self.radio_stereo),
                'safetyTriangle': int(self.safety_triangle),
                'screen': int(self.screen),
                'spareTire': int(self.spare_tire),
                'spareTireTools': int(self.spare_tire_tools),
                'speedometer': int(self.speedometer),
                'tires': int(self.tires),
                'sketchInfo': self.sketch_info or '[]',
                'notes': self.notes or '',
                'availableFuel': int(self.available_fuel),
                'odometerReading': self.odometer_reading,
                'other1': self.other1 or '',
                'other2': self.other2 or '',
            },
            'actualReturnBranchId': self.actual_return_branch_id.sta_branch_id,
            'suspensionCode': self.suspension_code,
            'suspensionPaymentDetails': {
                'sparePartsCost': self.spare_parts_cost,
                'damageCost': self.damage_cost,
                'oilChangeCost': self.oil_change_cost,
                'paymentMethodCode': int(self.payment_method_code),
                'paid': self.paid,
                'discount': self.discount,
            },
            'operatorId': int(self.sta_contract_id.operator_id) if self.sta_contract_id.operator_id else 1028558326
        }
        
        from ..controllers.sta_api_controller import STAAPIController
        
        try:
            api_controller = STAAPIController()
            result = api_controller.suspend_contract(suspension_data)
            
            if result.get('success'):
                self.sta_contract_id.write({
                    'sta_status': 'suspended',
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                    'error_message': False,
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Contract suspended successfully in STA system.'),
                        'type': 'success',
                    }
                }
            else:
                self.sta_contract_id.write({
                    'sta_status': 'error',
                    'error_message': result.get('error'),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                raise UserError(_('Failed to suspend contract: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error suspending STA contract: {str(e)}")
            self.sta_contract_id.write({
                'sta_status': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error suspending contract: %s') % str(e))

