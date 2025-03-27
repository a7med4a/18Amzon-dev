# additional.supplementary.services
# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AdditionalSupplementaryServices(models.Model):
    _inherit = 'additional.supplementary.services'

    type = fields.Selection(
        selection_add=[('internal_authorization', 'Internal Authorization'),
                       ('external_authorization', 'External Authorization')],
        ondelete={'internal_authorization': 'set additional', 'external_authorization': 'set additional'})
