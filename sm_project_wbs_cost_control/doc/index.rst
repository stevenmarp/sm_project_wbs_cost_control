Project WBS Cost Control
========================

Project WBS Cost Control adds a structured Work Breakdown Structure to Odoo
projects and tracks planned cost, committed purchase cost, actual analytic cost,
variance, and margin.

Dependencies
------------

This module depends only on standard Odoo applications: Project, Timesheets,
Purchase, and Accounting. It does not require any customer-specific module.

Basic Flow
----------

1. Open Project > WBS Cost Control.
2. Create a WBS item and select a project.
3. Add budget lines for labor, material, equipment, subcontract, overhead, or other cost.
4. Link project tasks to WBS items when operational work needs task tracking.
5. Add WBS items on purchase order lines to track committed cost.
6. Add WBS items on vendor bill lines or analytic lines to track actual cost.
7. Review planned cost, committed cost, actual cost, variance, margin, and cost performance.

Notes
-----

Actual cost is calculated from analytic lines linked to WBS items. Vendor bill
lines copy the WBS item into generated analytic lines when the bill creates
analytic entries.
