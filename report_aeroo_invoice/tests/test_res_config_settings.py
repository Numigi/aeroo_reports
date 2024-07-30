# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo.tests import common


class TestResConfigSettingsWithAerooReport(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard = cls.env["res.config.settings"].create({})
        cls.wizard.get_values()
        cls.report = cls.env.ref("report_aeroo_invoice.aeroo_invoice_report")

    def test_empty_aeroo_invoice_template_id(self):
        self.assertEqual(self.wizard.aeroo_invoice_template_id, self.report)

        self.wizard.aeroo_invoice_template_id = None
        self.wizard.execute()
        self.wizard = self.env["res.config.settings"].create({})
        self.assertFalse(self.wizard.aeroo_invoice_template_id)

    def test_change_aeroo_invoice_template_id(self):
        self.assertEqual(self.wizard.aeroo_invoice_template_id, self.report)

        report_copy = self.report.copy({"report_name": "new_aeroo_invoice_report"})
        self.wizard.aeroo_invoice_template_id = report_copy
        self.wizard.execute()
        self.wizard = self.env["res.config.settings"].create({})

        self.assertEqual(self.wizard.aeroo_invoice_template_id, report_copy)
