# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountPaymentWithCheckStubLines(models.Model):
    """Enable getting the stub line details from an aeroo report.

    Stub lines are the details regarding the invoices/refunds paid by the check.
    This must usually be printed with the check.
    """

    _inherit = "account.payment"

    def get_aeroo_check_stub_lines(self):
        """Method callable from the aeroo report."""
        invoices = self.invoice_ids.sorted(key=lambda inv: inv.date_due)
        return [self._aeroo_check_make_stub_line(inv) for inv in invoices]

    def _aeroo_check_make_stub_line(self, invoice):
        """Return the dict used to display an invoice/refund in the stub.

        This method was adapted from the following method in odoo version 12.0
        https://github.com/odoo/odoo/blob/12.0/addons/account_check_printing/models/account_payment.py

        It was also improved in order to:
            * work with invoices paid in different currencies.
            * work with invoices and refunds in the same payment.
            * display paid amounts in the currency of the invoice.
        """
        if invoice.type in ['in_invoice', 'out_refund']:
            invoice_sign = 1
            invoice_payment_reconcile = (
                invoice.move_id.line_ids.mapped('matched_debit_ids')
                .filtered(lambda r: r.debit_move_id in self.move_line_ids or
                          r.debit_move_id.invoice_id in self.invoice_ids)
            )
        else:
            invoice_sign = -1
            invoice_payment_reconcile = (
                invoice.move_id.line_ids.mapped('matched_credit_ids')
                .filtered(lambda r: r.credit_move_id in self.move_line_ids or
                          r.credit_move_id.invoice_id in self.invoice_ids)
            )

        if invoice.currency_id != self.journal_id.company_id.currency_id:
            amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount_currency')))
        else:
            amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount')))

        return {
            'invoice': invoice,
            'amount_total': invoice_sign * invoice.amount_total,
            'amount_residual': invoice_sign * invoice.residual,
            'amount_paid': invoice_sign * amount_paid,
            'currency': invoice.currency_id,
        }
