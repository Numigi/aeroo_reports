# © 2017 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime
from odoo.tests import common


class TestCheckPrinting(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].search([], limit=1)
        cls.report = cls.env.ref('account_check_printing_aeroo.sample_report')
        cls.journal = cls.env['account.journal'].create({
            'name': 'BMO CAD',
            'code': 'BMO',
            'type': 'bank',
            'check_report_id': cls.report.id,
        })

        currency = cls.env.user.company_id.currency_id
        journal = cls.env['account.journal'].create({
            'name': 'PURCHASES',
            'code': 'PURC',
            'type': 'purchase',
        })

        expense_account = cls.env['account.account'].search([
            ('user_type_id.type', '=', 'other'),
        ], limit=1)

        account = cls.env['account.account'].create({
            'user_type_id': cls.env.ref('account.data_account_type_payable').id,
            'name': 'Account Payable',
            'code': '210X00',
            'reconcile': True,
        })

        invoice = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'journal_id': journal.id,
            'account_id': account.id,
            'date': datetime.now(),
            'date_due': datetime.now(),
            'type': 'in_invoice',
            'reference': 'XXXXXX1',
            'currency_id': currency.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'My Product',
                    'quantity': 1,
                    'price_unit': 100,
                    'account_id': expense_account.id,
                })
            ]
        })
        invoice.action_invoice_open()

        cls.payment = cls.env['account.payment'].create({
            'partner_id': cls.partner.id,
            'amount': 1234.56,
            'journal_id': cls.journal.id,
            'invoice_ids': [(6, 0, [invoice.id])],
            'payment_type': 'outbound',
            'payment_method_id': cls.env.ref(
                'account_check_printing.account_payment_method_check').id,
        })
        cls.payment._onchange_amount()

    def test_print_check(self):
        self.payment.do_print_checks()
