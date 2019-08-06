# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import re

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import content_disposition, request


class PortalAccountWithAerooInvoiceReport(CustomerPortal):

    def _show_aeroo_report(self, record, template, download=False):
        """Show the given aeroo in the portal.

        This method is an adapted version of CustomerPortal._show_report found here:
        odoo/addons/portal/controllers/portal.py

        :param record: the odoo record for which to print the report.
        :param template: the aeroo report template.
        :param download: whether the report is dowloaded or only shown to the screen.
        """
        pdf = template.sudo().render_aeroo(doc_ids=[record.id], force_output_format='pdf')[0]

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]

        if download:
            filename = template.get_aeroo_filename(record, "pdf")
            headers.append(('Content-Disposition', content_disposition(filename)))

        return request.make_response(pdf, headers=headers)
