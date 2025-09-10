# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(IrHttp, self).session_info()
        # ex_date = datetime.strptime(result['expiration_date'], '%Y-%m-%d %H:%M:%S')
        # print("ex_date ===>", ex_date)
        # new_date = ex_date + relativedelta(months=1)
        # print("new_date ===>",new_date)
        # result['expiration_date'] = str(new_date)
        result["expiration_date"] = "2025-08-30 02:00:00"
        return result
