# Copyright 2024 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestCheckPrinting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].search([], limit=1)
        cls.report = cls.env.ref("account_check_printing_aeroo.sample_report")

        cls.journal = cls.env["account.journal"].create(
            {
                "name": "BMO CAD",
                "code": "BMO",
                "type": "bank",
                "check_report_id": cls.report.id,
            }
        )

        check_method = cls.env.ref(
            "account_check_printing.account_payment_method_check"
        )
        check_method_line = cls.journal.outbound_payment_method_line_ids.filtered(
            lambda l: l.payment_method_id == check_method
        )

        if not check_method_line:
            check_method_line = cls.env["account.payment.method.line"].create(
                {
                    "payment_method_id": check_method.id,
                    "journal_id": cls.journal.id,
                }
            )

        cls.payment = cls.env["account.payment"].create(
            {
                "partner_id": cls.partner.id,
                "amount": 1234.56,
                "journal_id": cls.journal.id,
                "payment_type": "outbound",
                "payment_method_line_id": check_method_line.id,
            }
        )

    def test_print_check(self):
        self.payment.do_print_checks()
