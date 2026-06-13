# -*- coding: utf-8 -*-
from odoo import fields, models


class IrActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(
        selection_add=[('sm_gantt', 'SM Gantt')],
        ondelete={'sm_gantt': 'cascade'},
    )
