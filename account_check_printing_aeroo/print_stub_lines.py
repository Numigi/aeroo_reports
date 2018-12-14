# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


def _get_reconcile_sum(account_move_reconciles: models.Model, use_company_currency: bool) -> float:
    """Get the sum of amounts of the given account move reconciles.

    :param account_move_reconciles: the reconciles to sum
    :param use_company_currency: whether to return the amount in company currency.
    :return: the sum of amounts
    """
    amount_field = 'amount' if use_company_currency else 'amount_currency'
    return sum(account_move_reconciles.mapped(amount_field))


def _get_invoice_paid_amount(check: models.Model, invoice: models.Model) -> float:
    """Get the amount paid on the invoice.

    The result amount includes any refunds already applied to the invoice,
    plus the amount paid with the given payment (check).

    If the invoice has a foreign currency, the amount in the foreign
    currency is returned. This implies that the payment is in the same
    currency than the invoice.

    :param check: the check payment.
    :param invoice: the invoice for which to determine the amount paid.
    :return: the amount paid.
    """
    refund_reconciles = (
        invoice.move_id.line_ids.mapped('matched_debit_ids')
        .filtered(lambda r: r.debit_move_id.invoice_id)
    )
    payment_reconciles = (
        invoice.move_id.line_ids.mapped('matched_debit_ids')
        .filtered(lambda r: r.debit_move_id in check.move_line_ids)
    )

    in_company_currency = invoice.currency_id == invoice.company_id.currency_id
    return _get_reconcile_sum(refund_reconciles | payment_reconciles, in_company_currency)


def _get_refund_paid_amount(check: models.Model, refund: models.Model) -> float:
    """Get the paid amount to display on the stub for a refund.

    For a refund, the paid amount is the total of amounts reconciled
    with any invoice paid by the check.

    :param check: the check payment.
    :param refund: the refund for which to determine the amount paid.
    :return: the amount paid.
    """
    invoice_reconciles = (
        refund.move_id.line_ids.mapped('matched_credit_ids')
        .filtered(lambda r: r.credit_move_id.invoice_id in check.invoice_ids)
    )

    in_company_currency = refund.currency_id == refund.company_id.currency_id
    return _get_reconcile_sum(invoice_reconciles, in_company_currency)


class AccountPaymentWithCheckStubLines(models.Model):
    """Enable getting the stub line details from an aeroo report.

    Stub lines are the details regarding the invoices/refunds paid by the check.
    This must usually be printed with the check.
    """

    _inherit = "account.payment"

    def get_aeroo_check_stub_lines(self):
        """Get the data to display on the check stub lines.

        It contains one line per invoice and one line per refund matched with
        any of the invoices.

        :return: the check stub lines data.
        :rtype: List[dict]
        """
        invoices_and_refunds = (
            self.invoice_ids |
            self.invoice_ids.mapped('payment_move_line_ids.invoice_id')
        ).sorted(key=lambda inv: inv.date_due)
        return [self._aeroo_check_make_stub_line(inv) for inv in invoices_and_refunds]

    def _aeroo_check_make_stub_line(self, invoice):
        """Return the dict used to display an invoice/refund in the stub.

        This method was adapted from the following method in odoo version 12.0
        https://github.com/odoo/odoo/blob/12.0/addons/account_check_printing/models/account_payment.py

        It was also improved in order to:
            * work with invoices paid in different currencies.
            * work with invoices and refunds in the same payment.
            * display paid amounts in the currency of the invoice.

        Note here that a customer refund is handled like a supplier invoice
        and a customer invoice is handled like a supplier refund.
        """
        is_supplier_invoice = invoice.type in ('in_invoice', 'out_refund')

        amount_paid = (
            _get_invoice_paid_amount(self, invoice) if is_supplier_invoice
            else _get_refund_paid_amount(self, invoice)
        )

        amount_sign = 1 if is_supplier_invoice else -1

        return {
            'invoice': invoice,
            'amount_total': amount_sign * invoice.amount_total,
            'amount_residual': amount_sign * invoice.residual,
            'amount_paid': amount_sign * amount_paid,
            'currency': invoice.currency_id,
        }
