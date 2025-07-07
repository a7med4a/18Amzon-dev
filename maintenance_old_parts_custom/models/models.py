# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from lxml import etree

class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = "Stock Moves"

    old_spare_parts_id=fields.Many2one(
        comodel_name='old.spare.parts',
        string='Old Spare Parts'
    )
    maintenance_job_order_id = fields.Many2one(
        comodel_name='maintenance.job.order',
        string='Job Order'
    )
    maintenance_external_job_order_id = fields.Many2one(
        comodel_name='maintenance.external.job.order',
        string='External Job Order'
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = "Stock Picking"

    is_old_spare_parts = fields.Boolean(string='Is Old Spare Parts', default=False)



class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = "Account Move"

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == 'form' and options.get('action_id') == self.env.ref('maintenance_custom.action_maintenance_create_bill').id:
            doc = etree.XML(res['arch'])
            journals = doc.xpath("//field[@name='journal_id']")
            if journals:
                for  journal in journals:
                    journal.set("readonly", "1")
                    journal.set("options", "{'no_open': True,'no_create': True}")
            maintenance_request = doc.xpath("//field[@name='maintenance_request_id']")
            for request in maintenance_request:
                request.set("readonly", "1")
                request.set("options", "{'no_open': True,'no_create': True}")
            partners = doc.xpath("//field[@name='partner_id']")
            for partner in partners:
                partner.set("options", "{'no_open': True,'no_create': True}")
            names = doc.xpath("//field[@name='name']")
            names[0].set("readonly", "1")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
