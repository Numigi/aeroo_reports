# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime, timedelta
from odoo.tests import common


class TestCheckPrinting(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestCheckPrinting, cls).setUpClass()

        cls.company_currency = cls.env.ref('base.main_company').currency_id
        cls.foreign_currency = cls.env['res.currency'].search(
            [('id', '!=', cls.company_currency.id)], limit=1)

        cls.env['res.currency.rate'].search([]).unlink()
        cls.env['res.currency.rate'].create({
            'name': datetime.now().date() - timedelta(days=1),
            'currency_id': cls.foreign_currency.id,
            'rate': 0.75,
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

    def create_invoices_and_payment(self, currency):
        self.invoices = self.env['account.invoice']

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
            self.invoices |= self.env['account.invoice'].create({
                'partner_id': self.partner.id,
                'journal_id': journal.id,
                'account_id': account.id,
                'date': datetime.now(),
                'date_due': datetime.now(),
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

        self.invoices |= self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'account_id': account.id,
            'date': datetime.now(),
            'date_due': datetime.now(),
            'type': 'in_refund',
            'reference': 'XXXXXX%s' % 4,
            'currency_id': currency.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Refund Line',
                    'quantity': 1,
                    'price_unit': 225,
                    'account_id': self.expense_account.id,
                })
            ]
        })

        self.invoices.action_invoice_open()

        self.payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': 75,
            'journal_id': self.journal.id,
            'currency_id': currency.id,
            'payment_type': 'outbound',
            'payment_method_id': self.env.ref(
                'account_check_printing.account_payment_method_check').id,
            'invoice_ids': [(6, 0, self.invoices.ids)],
            'partner_type': 'supplier',
            'payment_type': 'outbound',
        })

    def test_01_get_payment_lines(self):
        self.create_invoices_and_payment(self.company_currency)
        self.payment.post()
        lines = self.payment.get_payment_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0]['ref'], 'XXXXXX1')
        self.assertEqual(lines[1]['ref'], 'XXXXXX2')
        self.assertEqual(lines[2]['ref'], 'XXXXXX3')
        self.assertEqual(lines[3]['ref'], 'XXXXXX4')
        self.assertEqual(lines[0]['amount'], 100)
        self.assertEqual(lines[1]['amount'], 100)
        self.assertEqual(lines[2]['amount'], 100)
        self.assertEqual(lines[3]['amount'], -225)

    def test_02_get_payment_lines_foreign_currency(self):
        self.create_invoices_and_payment(self.foreign_currency)
        self.payment.post()
        lines = self.payment.get_payment_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0]['ref'], 'XXXXXX1')
        self.assertEqual(lines[1]['ref'], 'XXXXXX2')
        self.assertEqual(lines[2]['ref'], 'XXXXXX3')
        self.assertEqual(lines[3]['ref'], 'XXXXXX4')
        self.assertEqual(lines[0]['amount'], 100)
        self.assertEqual(lines[1]['amount'], 100)
        self.assertEqual(lines[2]['amount'], 100)
        self.assertEqual(lines[3]['amount'], -225)

    def test_03_get_payment_lines_different_currency(self):
        self.create_invoices_and_payment(self.company_currency)
        self.payment.currency_id = self.foreign_currency
        self.payment.amount = 56.25  # 75 * 0.75
        self.payment.post()

        lines = self.payment.get_payment_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0]['ref'], 'XXXXXX1')
        self.assertEqual(lines[1]['ref'], 'XXXXXX2')
        self.assertEqual(lines[2]['ref'], 'XXXXXX3')
        self.assertEqual(lines[3]['ref'], 'XXXXXX4')
        self.assertEqual(lines[0]['amount'], 75)
        self.assertEqual(lines[1]['amount'], 75)
        self.assertEqual(lines[2]['amount'], 75)
        self.assertEqual(lines[3]['amount'], -168.75)

    def test_04_get_payment_lines_different_currency(self):
        self.create_invoices_and_payment(self.foreign_currency)
        self.payment.currency_id = self.company_currency
        self.payment.amount = 100  # 75 / 0.75
        self.payment.post()

        lines = self.payment.get_payment_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0]['ref'], 'XXXXXX1')
        self.assertEqual(lines[1]['ref'], 'XXXXXX2')
        self.assertEqual(lines[2]['ref'], 'XXXXXX3')
        self.assertEqual(lines[3]['ref'], 'XXXXXX4')
        self.assertAlmostEqual(lines[0]['amount'], 133.33)
        self.assertAlmostEqual(lines[1]['amount'], 133.33)
        self.assertAlmostEqual(lines[2]['amount'], 133.33)
        self.assertAlmostEqual(lines[3]['amount'], -300)
