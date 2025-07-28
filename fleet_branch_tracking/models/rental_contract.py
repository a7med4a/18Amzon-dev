# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RentalContract(models.Model):
    _inherit = 'rental.contract'

    def apply_in_check_list_to_vehicle(self):
        self.ensure_one()
        return super(RentalContract, self.with_context(external_change=True, rental_id=self.id)).apply_in_check_list_to_vehicle()
