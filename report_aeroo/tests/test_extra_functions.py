# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, date
from freezegun import freeze_time
from odoo.tests import common
from ..extra_functions import (
    format_date,
    format_date_today,
    format_datetime,
    format_datetime_now,
    format_decimal,
    format_currency,
    format_html2text,
)


class TestAerooReport(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env.ref('report_aeroo.aeroo_sample_report')

    def test_format_date_fr(self):
        report = self.report.with_context(lang='fr_CA')
        result = format_date(report, date(2018, 4, 6), 'd MMMM yyyy')
        self.assertEqual(result, '6 avril 2018')

    def test_format_date_en(self):
        report = self.report.with_context(lang='en_US')
        result = format_date(report, date(2018, 4, 6), 'd MMMM yyyy')
        self.assertEqual(result, '6 April 2018')

    def test_format_date_today_fr_in_utc(self):
        with freeze_time('2018-04-06 00:00:00'):
            report = self.report.with_context(lang='fr_CA', tz='UTC')
            result = format_date_today(report, 'd MMMM yyyy')
            self.assertEqual(result, '6 avril 2018')

    def test_format_date_today_fr_in_specific_timezone(self):
        with freeze_time('2018-04-06 00:00:00'):
            report = self.report.with_context(lang='fr_CA', tz='Canada/Eastern')
            result = format_date_today(report, 'd MMMM yyyy')
            self.assertEqual(result, '5 avril 2018')  # Canada/Eastern = UTC - 4 hours

    def test_format_datetime_fr(self):
        report = self.report.with_context(lang='fr_CA', tz='UTC')
        result = format_datetime(report, datetime(2018, 4, 6, 10, 34), 'd MMMM yyyy hh:mm a')
        self.assertEqual(result, '6 avril 2018 10:34 AM')

    def test_format_datetime_en(self):
        report = self.report.with_context(lang='en_US', tz='UTC')
        result = format_datetime(report, datetime(2018, 4, 6, 10, 34), 'd MMMM yyyy hh:mm a')
        self.assertEqual(result, '6 April 2018 10:34 AM')

    def test_format_datetime_en_in_specific_timezone(self):
        report = self.report.with_context(lang='en_US', tz='Canada/Eastern')
        result = format_datetime(report, datetime(2018, 4, 6, 10, 34), 'd MMMM yyyy hh:mm a')
        self.assertEqual(result, '6 April 2018 06:34 AM')  # Canada/Eastern = UTC - 4 hours

    def test_format_datetime_now_fr_in_utc(self):
        with freeze_time(datetime(2018, 4, 6, 10, 34)):
            report = self.report.with_context(lang='fr_CA', tz='UTC')
            result = format_datetime_now(report, 'd MMMM yyyy hh:mm a')
            self.assertEqual(result, '6 avril 2018 10:34 AM')

    def test_format_datetime_now_fr_in_specific_timezone(self):
        with freeze_time(datetime(2018, 4, 6, 10, 34)):
            report = self.report.with_context(lang='fr_CA', tz='Canada/Eastern')
            result = format_datetime_now(report, 'd MMMM yyyy hh:mm a')
            self.assertEqual(result, '6 avril 2018 06:34 AM')  # Canada/Eastern = UTC - 4 hours

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

    def test_format_html2text(self):
        r"""Test the formating of html into text.

        * \n\n is added after the end of a div.
        * Line breaks are replaced with 2 spaces and one \n.
        * The text is ended with a single \n.
        * No \n is added when a line exceeds a given number length (i.e. 79 chars)
        """
        html = (
            "<div>Lorem Ipsum</div>"
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            "Morbi eleifend magna sit amet sem gravida sollicitudin."
            "<br/>Vestibulum metus ipsum, varius in ultricies eget, vulputate eu felis."
        )
        text = format_html2text(self.report, html)
        self.assertEqual(text, (
            "Lorem Ipsum"
            "\n\n"
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            "Morbi eleifend magna sit amet sem gravida sollicitudin.  \n"
            "Vestibulum metus ipsum, varius in ultricies eget, vulputate eu felis.\n"
        ))

    def test_format_html2text_with_none(self):
        self.assertEqual(format_html2text(self.report, None), "\n")
