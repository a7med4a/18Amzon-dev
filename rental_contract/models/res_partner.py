# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression


class Partner(models.Model):

    _inherit = 'res.partner'
    _rec_names_search = ['complete_name',
                         'email', 'ref', 'vat', 'company_registry', 'mobile2', 'id_no']
