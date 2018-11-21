# -*- coding: utf-8 -*-
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import http
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError
from odoo.http import request


class PortalAccountWithAerooInvoiceReport(PortalAccount):

    @http.route(['/my/invoices/pdf/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_report(self, invoice_id, access_token=None, **kw):
        """Print the invoice using the aeroo invoice template if it is defined.

        If the aeroo invoice report is not setup, fallback to the qweb template.
        """
        report = request.env.ref(
            'report_aeroo_invoice.aeroo_invoice_report', raise_if_not_found=False)
        if not report:
            return super().portal_my_invoice_report(
                invoice_id=invoice_id, access_token=access_token, **kw)

        try:
            invoice = self._invoice_check_access(invoice_id, access_token)
        except AccessError:
            return request.redirect('/my')

        pdf = report.sudo().render_aeroo(doc_ids=[invoice.id], force_output_format='pdf')[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
