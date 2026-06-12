# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sm_wbs_id = fields.Many2one('sm.project.wbs', string='WBS Item', domain="[('project_id', '=', project_id)]", tracking=True)

    def write(self, vals):
        result = super().write(vals)
        if 'sm_wbs_id' in vals and vals['sm_wbs_id']:
            wbs = self.env['sm.project.wbs'].browse(vals['sm_wbs_id'])
            for task in self.filtered(lambda item: not item.sm_wbs_id.task_id):
                if wbs.project_id == task.project_id:
                    wbs.task_id = task.id
        return result
