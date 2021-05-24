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
        cls.payment = cls.env['account.payment'].create({
            'partner_id': cls.partner.id,
            'amount': 1234.56,
            'journal_id': cls.journal.id,
            'payment_type': 'outbound',
            'payment_method_id': cls.env.ref(
                'account_check_printing.account_payment_method_check').id,
        })

    def test_print_check(self):
        self.payment.do_print_checks()
