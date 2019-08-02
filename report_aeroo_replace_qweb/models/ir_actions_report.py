# © 2019 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class IrActionsReport(models.Model):
    """Allow replacing a qweb report with an aeroo report.

    In the form view of a qweb report, a many2one field allows to select
    an aeroo report that replaces the qweb report.

    This allows to easily bind an aeroo report to the action buttons
    of a form view. By default, most of those buttons are bound to a qweb report.

    This feature supports the qweb-pdf format but not qweb-html.
    """

    _inherit = 'ir.actions.report'

    aeroo_report_id = fields.Many2one(
        'ir.actions.report',
        help="This field allows to select an Aeroo report that replaces this report."
    )

    qweb_report_ids = fields.One2many(
        'ir.actions.report',
        'aeroo_report_id',
        help="This field allows to select Qweb reports that should be replaced "
        "by this Aeroo report. Only qweb-pdf reports are supported."
    )

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if self.aeroo_report_id:
            return self.aeroo_report_id.render_aeroo(
                doc_ids=res_ids, data=data, force_output_format='pdf')

        return super().render_qweb_pdf(res_ids, data)
