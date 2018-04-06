# -*- coding: utf-8 -*-
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from ..extra_functions import (
    format_date,
    format_datetime,
    format_decimal,
    format_currency,
)


class TestAerooReport(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env.ref('report_aeroo.aeroo_sample_report_id')

    def test_format_date_fr(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_date(report, '2018-04-06', 'd MMMM yyyy')
        self.assertEqual(result, '6 avril 2018')

    def test_format_date_en(self):
        report = self.report.with_context(lang='en_US')
        result = format_date(report, '2018-04-06', 'd MMMM yyyy')
        self.assertEqual(result, '6 April 2018')

    def test_format_datetime_fr(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_datetime(report, '2018-04-06 10:34:00', 'd MMMM yyyy hh:mm a')
        self.assertEqual(result, '6 avril 2018 10:34 AM')

    def test_format_datetime_en(self):
        report = self.report.with_context(lang='en_US')
        result = format_datetime(report, '2018-04-06 10:34:00', 'd MMMM yyyy hh:mm a')
        self.assertEqual(result, '6 April 2018 10:34 AM')

    def test_format_decimal_fr(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_decimal(report, 1500)
        self.assertEqual(result, '1\xa0500,00')

    def test_format_decimal_en(self):
        report = self.report.with_context(lang='en_US')
        result = format_decimal(report, 1500)
        self.assertEqual(result, '1,500.00')

    def test_format_decimal_fr_with_format(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_decimal(report, 1500, amount_format='#,##0.0')
        self.assertEqual(result, '1\xa0500,0')

    def test_format_currency_fr(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_currency(report, 1500, self.env.ref('base.USD'))
        self.assertEqual(result, '1\xa0500,00\xa0$US')

    def test_format_currency_en(self):
        report = self.report.with_context(lang='en_US')
        result = format_currency(report, 1500, self.env.ref('base.USD'))
        self.assertEqual(result, '$1,500.00')

    def test_format_currency_fr_with_format(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_currency(
            report, 1500, self.env.ref('base.USD'), amount_format='#,##0.00\xa0¤¤')
        self.assertEqual(result, '1\xa0500,00\xa0USD')
