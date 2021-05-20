# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import http
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

AEROO_INVOICE_REPORT_REF = 'report_aeroo_invoice.aeroo_invoice_report'


class PortalAccountWithAerooInvoiceReport(PortalAccount):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(
        self, invoice_id, access_token=None, report_type=None, download=False, **kw
    ):
        template = request.env.ref(AEROO_INVOICE_REPORT_REF, raise_if_not_found=False)

        if not template or report_type != 'pdf':
            return super().portal_my_invoice_detail(
                invoice_id, access_token=access_token, report_type=report_type,
                download=download, **kw)

        try:
            invoice = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return self._show_aeroo_report(record=invoice, template=template, download=download)
