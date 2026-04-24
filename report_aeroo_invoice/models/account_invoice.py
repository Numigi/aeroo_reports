# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import api, fields, models


class InvoiceWithAerooReport(models.Model):

    _inherit = 'account.invoice'

    closest_timesheet_date = fields.Date(
        compute="_compute_closest_timesheet_date",
        string="Closest Timesheet Date",
    )

    @api.depends("date_invoice", "timesheet_ids", "timesheet_ids.timesheet_invoice_id")
    def _compute_closest_timesheet_date(self):
        for invoice in self:
            if not invoice.timesheet_ids or not invoice.date_invoice:
                invoice.closest_timesheet_date = False
                continue

            ts_dates = []
            for ts in invoice.timesheet_ids:
                # We strictly ensure the timesheet is linked to the current invoice
                # Adapt 'timesheet_invoice_id' if your custom module uses another field name
                if ts.timesheet_invoice_id and ts.timesheet_invoice_id.id == invoice.id:
                    ts_val = getattr(ts, "date_time", False) or getattr(ts, "date", False)
                    if ts_val:
                        ts_date = ts_val.date() if hasattr(ts_val, "date") else ts_val
                        ts_dates.append(ts_date)

            if not ts_dates:
                invoice.closest_timesheet_date = False
                continue

            # Calculate the minimal difference in days between timesheet date and invoice date
            closest_date = min(ts_dates, key=lambda d: abs((d - invoice.date_invoice).days))
            invoice.closest_timesheet_date = closest_date

    def invoice_print(self):
        """Print the invoice using the aeroo invoice template if it is defined.

        If the aeroo invoice report is not setup, fallback to the qweb template.
        """
        report = self.env.ref('report_aeroo_invoice.aeroo_invoice_report', raise_if_not_found=False)
        if report:
            return report.report_action(self)
        else:
            return super().invoice_print()







