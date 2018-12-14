# © 2017 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import random
from datetime import datetime, timedelta
from odoo.tests import common


class TestCheckPrintStubLines(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_currency = cls.env.ref('base.main_company').currency_id
        cls.foreign_currency = cls.env['res.currency'].search(
            [('id', '!=', cls.company_currency.id)], limit=1)

        cls.env['res.currency.rate'].search([]).unlink()
        cls.env['res.currency.rate'].create({
            'name': datetime.now().date() - timedelta(days=1),
            'currency_id': cls.foreign_currency.id,
            'rate': 0.80,
        })

        cls.expense_account = cls.env['account.account'].search([
            ('user_type_id.type', '=', 'other'),
        ], limit=1)

        cls.partner = cls.env['res.partner'].search([], limit=1)
        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
        ], limit=1)

        cls.journal = cls.env['account.journal'].create({
            'name': 'BMO',
            'code': 'BMO',
            'type': 'bank',
        })

        cls.purchase_journal = cls.env['account.journal'].create({
            'name': 'PURCHASES',
            'code': 'PURC1',
            'type': 'purchase',
        })

        cls.payable_account = cls.env['account.account'].create({
            'user_type_id': cls.env.ref('account.data_account_type_payable').id,
            'name': 'Account Payable',
            'code': '210100',
            'reconcile': True,
        })

        cls.purchase_journal_foreign = cls.env['account.journal'].create({
            'name': 'PURCHASES',
            'code': 'PURC2',
            'type': 'purchase',
            'currency_id': cls.foreign_currency.id,
        })

        cls.payable_account_foreign = cls.env['account.account'].create({
            'user_type_id': cls.env.ref('account.data_account_type_payable').id,
            'name': 'Account Payable',
            'code': '210200',
            'currency_id': cls.foreign_currency.id,
            'reconcile': True,
        })

    def _create_invoice(self, amount, currency, days_before_due_date, type_='in_invoice'):
        """Create payable invoice in the given currency."""
        journal = (
            self.purchase_journal
            if currency == self.company_currency else self.purchase_journal_foreign
        )
        account = (
            self.payable_account
            if currency == self.company_currency else self.payable_account_foreign
        )
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'account_id': account.id,
            'date': datetime.now(),
            'date_due': datetime.now() + timedelta(days_before_due_date),
            'type': type_,
            'reference': 'INV%d' % random.randrange(1, 10000),
            'currency_id': currency.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'My Product',
                    'quantity': 1,
                    'price_unit': amount,
                    'account_id': self.expense_account.id,
                })
            ]
        })

        invoice.action_invoice_open()
        return invoice

    def _create_payment(self, invoices, currency, amount):
        """Create a payment for the given invoices.

        :param invoices: the invoices to pay
        :param currency: the payment currency
        :param amount: the amount to pay
        """
        payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': amount,
            'journal_id': self.journal.id,
            'currency_id': currency.id,
            'payment_method_id': self.env.ref(
                'account_check_printing.account_payment_method_check').id,
            'invoice_ids': [(6, 0, [inv.id for inv in invoices])],
            'partner_type': 'supplier',
            'payment_type': 'outbound',
        })
        payment.post()
        return payment

    def _check_stub_line(self, line, invoice, amount_total, amount_paid, amount_residual):
        """Check the amount in the given stub line."""
        self.assertEqual(line, {
            'amount_total': amount_total,
            'amount_paid': amount_paid,
            'amount_residual': amount_residual,
            'currency': invoice.currency_id,
            'invoice': invoice,
        })

    def test_payment_and_invoices_both_in_company_currency(self):
        invoices = [
            self._create_invoice(100, self.company_currency, 1, type_='in_invoice'),
            self._create_invoice(100, self.company_currency, 2, type_='in_invoice'),
            self._create_invoice(100, self.company_currency, 3, type_='in_invoice'),
            self._create_invoice(240, self.company_currency, 4, type_='in_refund'),
        ]
        payment = self._create_payment(invoices, self.company_currency, 60)
        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 4
        self._check_stub_line(lines[0], invoices[0], 100, 100, 0)
        self._check_stub_line(lines[1], invoices[1], 100, 100, 0)
        self._check_stub_line(lines[2], invoices[2], 100, 100, 0)
        self._check_stub_line(lines[3], invoices[3], -240, -240, 0)

    def test_payment_and_invoices_both_in_foreign_currency(self):
        invoices = [
            self._create_invoice(100, self.foreign_currency, 1, type_='in_invoice'),
            self._create_invoice(100, self.foreign_currency, 2, type_='in_invoice'),
            self._create_invoice(100, self.foreign_currency, 3, type_='in_invoice'),
            self._create_invoice(240, self.foreign_currency, 4, type_='in_refund'),
        ]
        payment = self._create_payment(invoices, self.foreign_currency, 60)
        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 4
        self._check_stub_line(lines[0], invoices[0], 100, 100, 0)
        self._check_stub_line(lines[1], invoices[1], 100, 100, 0)
        self._check_stub_line(lines[2], invoices[2], 100, 100, 0)
        self._check_stub_line(lines[3], invoices[3], -240, -240, 0)

    def test_payment_in_foreign_currency(self):
        invoices = [
            self._create_invoice(100, self.company_currency, 1, type_='in_invoice'),
            self._create_invoice(100, self.company_currency, 2, type_='in_invoice'),
            self._create_invoice(100, self.company_currency, 3, type_='in_invoice'),
            self._create_invoice(240, self.company_currency, 4, type_='in_refund'),
        ]
        payment = self._create_payment(invoices, self.foreign_currency, 48)  # 60 * 0.80
        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 4
        self._check_stub_line(lines[0], invoices[0], 100, 100, 0)
        self._check_stub_line(lines[1], invoices[1], 100, 100, 0)
        self._check_stub_line(lines[2], invoices[2], 100, 100, 0)
        self._check_stub_line(lines[3], invoices[3], -240, -240, 0)

    def test_invoices_in_foreign_currency(self):
        invoices = [
            self._create_invoice(100, self.foreign_currency, 1, type_='in_invoice'),
            self._create_invoice(100, self.foreign_currency, 2, type_='in_invoice'),
            self._create_invoice(100, self.foreign_currency, 3, type_='in_invoice'),
            self._create_invoice(240, self.foreign_currency, 4, type_='in_refund'),
        ]
        payment = self._create_payment(invoices, self.company_currency, 75)  # 60 / 0.80
        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 4
        self._check_stub_line(lines[0], invoices[0], 100, 100, 0)
        self._check_stub_line(lines[1], invoices[1], 100, 100, 0)
        self._check_stub_line(lines[2], invoices[2], 100, 100, 0)
        self._check_stub_line(lines[3], invoices[3], -240, -240, 0)

    def test_ifInvoicesReconciledWithCreditNote_thenCreditNoteStillAppears(self):
        """If credit note reconciled with invoices, credit note appears on the check.

        This case is the most common in practice.

            1. The refunds have been reconciled with the invoice before being selected
                on the payment.
            2. The invoices are selected without the credit for payment.
            3. The paid amount on the invoices include the credit note amount.
            4. The credit note appears after the invoices.

        The result is the same as when selecting the invoices and the refunds together
        for payment.
        """
        invoices = [
            self._create_invoice(100, self.company_currency, 1, type_='in_invoice'),
            self._create_invoice(100, self.company_currency, 2, type_='in_invoice'),
        ]
        refund = self._create_invoice(50, self.company_currency, 3, type_='in_refund')

        # 1. Reconcile the refund with the invoices.
        refund_move_line = refund.move_id.line_ids.filtered(
            lambda l: l.account_id == self.payable_account)
        invoices[0].assign_outstanding_credit(refund_move_line.id)

        # 2. Pay the invoices without the refunds.
        payment = self._create_payment(invoices, self.company_currency, 150)

        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 3
        self._check_stub_line(lines[0], invoices[0], 100, 100, 0)
        self._check_stub_line(lines[1], invoices[1], 100, 100, 0)
        self._check_stub_line(lines[2], refund, -50, -50, 0)

    def test_customer_refund_handled_like_supplier_invoice(self):
        """Test that a customer refund is handled like a supplier invoice."""
        invoice = self._create_invoice(100, self.company_currency, 1, type_='out_invoice')
        refund = self._create_invoice(150, self.company_currency, 2, type_='out_refund')

        # Reconcile the refund with the invoices.
        refund_move_line = refund.move_id.line_ids.filtered(
            lambda l: l.account_id == self.payable_account)
        invoice.assign_outstanding_credit(refund_move_line.id)

        # 2. Pay the exceeding amount on the customer refund
        payment = self._create_payment(refund, self.company_currency, 50)

        lines = payment.get_aeroo_check_stub_lines()
        assert len(lines) == 2
        self._check_stub_line(lines[0], refund, 150, 150, 0)
        self._check_stub_line(lines[1], invoice, -100, -100, 0)
