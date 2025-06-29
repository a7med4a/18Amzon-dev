# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class NaqlCloseContractWizard(models.TransientModel):
    _name = 'sta.close.contract.wizard'
    _description = 'Close Naql Contract'

    sta_contract_id = fields.Many2one(
        'sta.contract',
        string='Naql Contract',
        required=True,
        help='Naql contract to close'
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
    
    closure_code = fields.Selection([
        ('1', 'Normal Closure'),
        ('2', 'Early Closure'),
        ('3', 'Late Closure'),
        ('4', 'Damage Closure'),
    ], string='Closure Code', required=True, default='2')
    
    main_closure_code = fields.Selection([
        ('1', 'Normal'),
        ('2', 'Early'),
        ('3', 'Late'),
        ('4', 'Damage'),
    ], string='Main Closure Code', required=True, default='2')
    
    contract_actual_end_date = fields.Datetime(
        string='Actual End Date',
        required=True,
        default=fields.Datetime.now,
        help='Actual contract end date'
    )
    
    # Return Status Fields (similar to suspend wizard)
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
    sketch_info = fields.Text(
        string='Sketch Info', 
        default="[{'type':'small-scratch','x':755.5,'y':301.75}]",
        help='JSON string representing vehicle damage sketch'
    )
    notes = fields.Text(string='Notes')
    other1 = fields.Char(string='Other 1')
    other2 = fields.Char(string='Other 2')
    
    # Payment Details
    oil_change_cost = fields.Float(string='Oil Change Cost', default=0.0)
    payment_method_code = fields.Selection([
        ('1', 'Cash'),
        ('2', 'Credit Card'),
        ('3', 'Bank Transfer'),
    ], string='Payment Method', default='3')
    paid = fields.Float(string='Paid Amount', default=5047.51)
    discount = fields.Float(string='Discount', default=0.0)

    def action_close_contract(self):
        """Close the contract in Naql system"""
        self.ensure_one()
        
        if not self.sta_contract_id.sta_contract_number:
            raise UserError(_('Contract must be created in Naql system first.'))
        
        if self.sta_contract_id.sta_status in ['cancelled', 'closed']:
            raise UserError(_('Contract is already cancelled or closed.'))
        
        # Prepare closure data
        closure_data = {
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
                'other1': self.other1 or '',
                'other2': self.other2 or '',
                'sketchInfo': self.sketch_info or "[]",
                'notes': self.notes or '',
                'odometerReading': self.odometer_reading,
                'availableFuel': int(self.available_fuel),
            },
            'actualReturnBranchId': self.actual_return_branch_id.sta_branch_id,
            'closureCode': self.closure_code,
            'closurePaymentDetails': {
                'paymentMethodCode': int(self.payment_method_code),
                'oilChangeCost': self.oil_change_cost,
                'paid': self.paid,
                'discount': self.discount,
            },
            'contractActualEndDate': self.contract_actual_end_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'mainClosureCode': self.main_closure_code,
            'operatorId': int(self.sta_contract_id.operator_id) if self.sta_contract_id.operator_id else 1028558326
        }
        
        from ..controllers.sta_api_controller import NaqlAPIController
        
        try:
            api_controller = NaqlAPIController()
            result = api_controller.close_contract(closure_data)
            
            if result.get('success'):
                self.sta_contract_id.write({
                    'sta_status': 'closed',
                    'last_sync_date': fields.Datetime.now(),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                    'error_message': False,
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Contract closed successfully in Naql system.'),
                        'type': 'success',
                    }
                }
            else:
                self.sta_contract_id.write({
                    'sta_status': 'error',
                    'error_message': result.get('error'),
                    'sta_response_log': json.dumps(result.get('response', {}), indent=2),
                })
                raise UserError(_('Failed to close contract: %s') % result.get('error'))
                
        except Exception as e:
            _logger.error(f"Error closing Naql contract: {str(e)}")
            self.sta_contract_id.write({
                'sta_status': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Error closing contract: %s') % str(e))

