# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    sm_wbs_id = fields.Many2one('sm.project.wbs', string='WBS Item', domain="[('project_id', '=', project_id)]", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sm_wbs_id') and vals.get('task_id'):
                task = self.env['project.task'].browse(vals['task_id'])
                vals['sm_wbs_id'] = task.sm_wbs_id.id or False
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if 'task_id' in vals and 'sm_wbs_id' not in vals:
            for line in self.filtered(lambda item: item.task_id.sm_wbs_id and not item.sm_wbs_id):
                line.sm_wbs_id = line.task_id.sm_wbs_id.id
        return result
