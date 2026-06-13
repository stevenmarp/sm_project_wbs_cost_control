# -*- coding: utf-8 -*-
{
    'name': 'Project Budget Control with WBS & Gantt',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Track project budgets, WBS cost breakdowns, committed purchases, actual costs, variance, and Gantt planning',
    'description': """
Project WBS Cost Control
========================
Manage Work Breakdown Structure cost control for Odoo projects.

Features:
- WBS tree per project with parent and child breakdowns
- Planned cost and revenue per WBS item
- Budget lines by labor, material, equipment, subcontract, and overhead
- Committed cost from purchase order lines linked to WBS
- Actual cost from analytic lines linked to WBS
- Variance and cost performance percentage
- Smart buttons from Project and Task
- WBS fields on purchase order lines, vendor bill lines, and analytic lines
    """,
    'author': 'Steven Marp',
    'website': 'https://apps.odoo.com/apps/modules/browse?repo_maintainer_id=512936',
    'license': 'OPL-1',
    'depends': [
        'web',
        'project',
        'hr_timesheet',
        'purchase',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/project_wbs_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/account_analytic_line_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sm_project_wbs_cost_control/static/src/gantt_view/*.*',
        ],
    },
    'images': [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 199.00,
    'currency': 'USD',
}
