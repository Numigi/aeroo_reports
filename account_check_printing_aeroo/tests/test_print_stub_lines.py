# © 2017 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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

    def _create_invoices(self, currency):
        """Create 4 payable invoices.

        * 3 invoices of 100
        * 1 refund of -240
        """
        invoices = self.env['account.invoice']

        journal = self.env['account.journal'].create({
            'name': 'PURCHASES',
            'code': 'PURC',
            'type': 'purchase',
            'currency_id':
            currency.id if currency != self.company_currency else None,
        })

        account = self.env['account.account'].create({
            'user_type_id':
            self.env.ref('account.data_account_type_payable').id,
            'name': 'Account Payable',
            'code': '210X00',
            'currency_id':
            currency.id if currency != self.company_currency else None,
            'reconcile': True,
        })

        for i in range(1, 4):
            invoices |= self.env['account.invoice'].create({
                'partner_id': self.partner.id,
                'journal_id': journal.id,
                'account_id': account.id,
                'date': datetime.now(),
                'date_due': datetime.now() + timedelta(i),
                'type': 'in_invoice',
                'reference': 'XXXXXX%s' % i,
                'currency_id': currency.id,
                'invoice_line_ids': [
                    (0, 0, {
                        'name': 'My Product',
                        'quantity': 1,
                        'price_unit': 100,
                        'account_id': self.expense_account.id,
                    })
                ]
            })

        invoices |= self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'account_id': account.id,
            'date': datetime.now(),
            'date_due': datetime.now() + timedelta(4),
            'type': 'in_refund',
            'reference': 'XXXXXX%s' % 4,
            'currency_id': currency.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Refund Line',
                    'quantity': 1,
                    'price_unit': 240,
                    'account_id': self.expense_account.id,
                })
            ]
        })

        invoices.action_invoice_open()
        return invoices

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
            'invoice_ids': [(6, 0, invoices.ids)],
            'partner_type': 'supplier',
            'payment_type': 'outbound',
        })
        payment.post()
        return payment

    def _check_stub_lines(self, lines, invoices):
        """Check the amounts in the stub lines.

        The result of the stub is the same whether or not the invoices and
        payments are in the same currency. The logic to get these amounts
        is however different.
        """
        self.assertEqual(lines, [
            {
                'amount_paid': 100,
                'amount_residual': 0,
                'amount_total': 100,
                'currency': invoices[0].currency_id,
                'invoice': invoices[0],
            },
            {
                'amount_paid': 100,
                'amount_residual': 0,
                'amount_total': 100,
                'currency': invoices[1].currency_id,
                'invoice': invoices[1],
            },
            {
                'amount_paid': 100,
                'amount_residual': 0,
                'amount_total': 100,
                'currency': invoices[2].currency_id,
                'invoice': invoices[2],
            },
            {
                'amount_paid': -240,
                'amount_residual': -0,
                'amount_total': -240,
                'currency': invoices[3].currency_id,
                'invoice': invoices[3],
            }
        ])

    def test_payment_and_invoices_both_in_company_currency(self):
        invoices = self._create_invoices(self.company_currency)
        payment = self._create_payment(invoices, self.company_currency, 60)
        lines = payment.get_aeroo_check_stub_lines()
        self._check_stub_lines(lines, invoices)

    def test_payment_and_invoices_both_in_foreign_currency(self):
        invoices = self._create_invoices(self.foreign_currency)
        payment = self._create_payment(invoices, self.foreign_currency, 60)
        lines = payment.get_aeroo_check_stub_lines()
        self._check_stub_lines(lines, invoices)

    def test_payment_in_foreign_currency(self):
        invoices = self._create_invoices(self.company_currency)
        payment = self._create_payment(invoices, self.foreign_currency, 48)  # 60 * 0.80
        lines = payment.get_aeroo_check_stub_lines()
        self._check_stub_lines(lines, invoices)

    def test_invoices_in_foreign_currency(self):
        invoices = self._create_invoices(self.foreign_currency)
        payment = self._create_payment(invoices, self.company_currency, 75)  # 60 / 0.80
        lines = payment.get_aeroo_check_stub_lines()
        self._check_stub_lines(lines, invoices)
