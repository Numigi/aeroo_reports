# Copyright 2023 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo.tests.common import TransactionCase


class TestAerooWatermark(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env.ref("base.action_report_layout")

    def test_watermark_parameter_default_false(self):
        """Test that AEROO_REPORTS_TESTS parameter defaults to False"""
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("AEROO_REPORTS_TESTS", "False")
        )
        self.assertEqual(param_value, "False")

    def test_should_add_test_watermark_false(self):
        """Test that _should_add_test_watermark returns False by default"""
        report = self.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "aeroo",
            }
        )
        self.assertFalse(report._should_add_test_watermark())

    def test_should_add_test_watermark_true(self):
        """Test that _should_add_test_watermark returns True when enabled"""
        self.env["ir.config_parameter"].sudo().set_param("AEROO_REPORTS_TESTS", "true")
        report = self.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "aeroo",
            }
        )
        self.assertTrue(report._should_add_test_watermark())

    def test_should_add_test_watermark_case_insensitive(self):
        """Test that _should_add_test_watermark works regardless of case"""
        self.env["ir.config_parameter"].sudo().set_param("AEROO_REPORTS_TESTS", "True")
        report = self.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "aeroo",
            }
        )
        self.assertTrue(report._should_add_test_watermark())

        self.env["ir.config_parameter"].sudo().set_param("AEROO_REPORTS_TESTS", "TRUE")
        self.assertTrue(report._should_add_test_watermark())
