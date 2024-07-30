# Copyright 2019 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAccountWithAerooInvoiceReport(CustomerPortal):

    def _show_report(self, model, report_type, report_ref, download=False):
        """Dowload a replacement aeroo report instead of a qweb report.

        Without inheriting this method, the replacement report is printed,
        but with the filename defined on the qweb report.
        """
        report = request.env.ref(report_ref)
        report_id = report.sudo().aeroo_report_id
        if report_type == "pdf" and report_id:
            return self._show_aeroo_report(model, report_id, download=download)
        else:
            return super()._show_report(
                model, report_type, report_ref, download=download
            )
