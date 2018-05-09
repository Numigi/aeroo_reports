# -*- coding: utf-8 -*-
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import models


class InvoiceWithAerooReport(models.Model):

    _inherit = 'account.invoice'

    def invoice_print(self):
        """Print the invoice using the aeroo invoice template if it is defined.

        If the aeroo invoice report is not setup, fallback to the qweb template.
        """
        report = self.env.ref('report_aeroo_invoice.aeroo_invoice_report', raise_if_not_found=False)
        if report:
            return report.report_action(self)
        else:
            return super().invoice_print()
