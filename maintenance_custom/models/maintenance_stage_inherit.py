# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MaintenanceStageInherit(models.Model):
    """ Model for case stages. This models the main stages of a Maintenance Request management flow. """
    _inherit = 'maintenance.stage'

    stage_type = fields.Selection(
        string='Stage Type',
        selection=[('new', 'New'),
                   ('under_approval', 'Under Approval'),
                   ('opened', 'Opened'),
                   ('closed', 'Closed'),
                   ('cancelled', 'Cancelled'), ('rejected', 'Rejected'), ],
        required=True, default='new')

