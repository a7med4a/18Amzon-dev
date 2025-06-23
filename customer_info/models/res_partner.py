# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def default_get(self, fields):
        defaults = super(ResPartner, self).default_get(fields)
        if self.env.context.get('default_contract_type') == 'rental':
            config = self.env['individual.customer.config'].search(
                [('type', '=', 'rental')], limit=1)
            if config:
                defaults['property_account_receivable_id'] = config.account_receivable_id.id
                defaults['category_id'] = config.category_id
        if self.env.context.get('default_contract_type') == 'long_term':
            config = self.env['individual.customer.config'].search(
                [('type', '=', 'long_term')], limit=1)
            if config:
                defaults['property_account_receivable_id'] = config.account_receivable_id.id
                defaults['category_id'] = config.category_id

        return defaults

    create_from_rental = fields.Boolean(string="Create From Rental",)
    date_of_birth = fields.Date(
        string='Date of Birth', required=True, tracking=True)
    age = fields.Char(string='Age', compute='_compute_age',
                      store=True, tracking=True)
    id_type = fields.Selection([
        ('resident', 'Resident'),
        ('national', 'National'),
        ('visitor', 'Visitor'),
        ('citizens', 'Citizens Of The GCC'),
    ], string='ID Type', tracking=True, required=True)
    id_no = fields.Char(string='ID No', tracking=True, required=True)
    id_expiry_date = fields.Date(string='ID Expiry Date', tracking=True)
    version_no = fields.Integer(
        string='Version No', tracking=True, required=True)
    nationality = fields.Many2one(
        'res.country', string='Nationality', tracking=True, required=True)
    license_expiry_date = fields.Date(
        string='License Expiry Date', tracking=True, required=True)
    license_type = fields.Selection([
        ('private', 'Private'),
        ('heavy', 'Heavy'),
        ('temporary', 'Temporary/Visitor '),
        ('public', 'Public Transport '),
        ('heavy', 'Heavy Vehicle License'),
    ], default='private', string='License Type', tracking=True, required=True)
    place_of_issue = fields.Char(string='Place of Issue', tracking=True)
    mobile2 = fields.Char(string="Mobile Number", tracking=True, required=True)
    contract_type = fields.Selection(
        string='Type',
        selection=[('rental', 'Rental'),
                   ('long_term', 'Long Term'), ],
        default='rental')
    _sql_constraints = [
        ('mobile2_unique', 'UNIQUE(mobile2)', 'mobile2 number must be unique.'),
        ('mobile2_length', 'CHECK(LENGTH(mobile2) = 12)',
         'mobile2 number must be exactly 12 digits.'),
    ]

    @api.constrains('mobile2')
    def _check_mobile2(self):
        for record in self:
            if record.mobile2:
                if len(record.mobile2) != 12 or not record.mobile2.isdigit():
                    raise ValidationError(
                        "mobile2 number must be exactly 12 digits and contain only numbers.")
                if not record.mobile2.startswith('9665'):
                    raise ValidationError(
                        "mobile2 number must start with '9665'.")

    @api.model_create_multi
    def create(self, values):
        recordes = super(ResPartner, self).create(values)
        for rec in recordes:
            rec.mobile = rec.mobile2
        if 'version_no' in values:
            recordes._check_version_no()
        return recordes

    def write(self, values):
        # Add code here
        if 'mobile2' in values:
            values['mobile'] = values['mobile2']
        res = super(ResPartner, self).write(values)
        if 'version_no' in values:
            self._check_version_no()
        return res

    @api.onchange('mobile2')
    def _onchange_mobile2(self):
        if self.mobile2:
            if not self.mobile2.isdigit():
                return {
                    'warning': {
                        'title': "Invalid Input",
                        'message': "mobile2 number must contain only numbers.",
                    }
                }
            if not self.mobile2.startswith('9665'):
                return {
                    'warning': {
                        'title': "Invalid Input",
                        'message': "mobile2 number must start with '9665'.",
                    }
                }
            if len(self.mobile2) != 12:
                return {
                    'warning': {
                        'title': "Invalid Input",
                        'message': "mobile2 number must be exactly 12 digits.",
                    }
                }
            self.mobile = self.mobile2

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 0

    def _check_version_no(self):
        for record in self:
            if record.version_no < 1:
                raise ValidationError(
                    "Version No must be greater than or equal to 1.")
