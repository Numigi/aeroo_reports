# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import pytest
from datetime import datetime, date
from ddt import data, ddt, unpack
from freezegun import freeze_time
from odoo.exceptions import ValidationError
from odoo.tests import common
from ..extra_functions import (
    barcode,
    qrcode,
    format_date,
    format_date_today,
    format_datetime,
    format_datetime_now,
    format_decimal,
    format_currency,
    format_hours,
    format_html2text,
    group_by,
)


@ddt
class TestAerooReport(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env.ref("report_aeroo.aeroo_sample_report")

    @data(
        (0, "00:00"),
        (2.25, "02:15"),
        (-2.25, "-02:15"),
        (100, "100:00"),
    )
    @unpack
    def test_format_hours(self, number, result):
        self.assertEqual(format_hours(self.report, number), result)

    def test_format_date_fr(self):
        report = self.report.with_context(lang="fr_CA")
        result = format_date(report, date(2018, 4, 6), "d MMMM yyyy")
        self.assertEqual(result, "6 avril 2018")

    def test_format_date_en(self):
        report = self.report.with_context(lang="en_US")
        result = format_date(report, date(2018, 4, 6), "d MMMM yyyy")
        self.assertEqual(result, "6 April 2018")

    def test_format_date_today_fr_in_utc(self):
        with freeze_time("2018-04-06 00:00:00"):
            report = self.report.with_context(lang="fr_CA", tz="UTC")
            result = format_date_today(report, "d MMMM yyyy")
            self.assertEqual(result, "6 avril 2018")

    def test_format_date_today_fr_in_specific_timezone(self):
        with freeze_time("2018-04-06 00:00:00"):
            report = self.report.with_context(lang="fr_CA", tz="Canada/Eastern")
            result = format_date_today(report, "d MMMM yyyy")
            self.assertEqual(result, "5 avril 2018")  # Canada/Eastern = UTC - 4 hours

    def test_format_datetime_fr(self):
        report = self.report.with_context(lang="fr_CA", tz="UTC")
        result = format_datetime(
            report, datetime(2018, 4, 6, 10, 34), "d MMMM yyyy hh:mm a"
        )
        self.assertEqual(result, "6 avril 2018 10:34 AM")

    def test_format_datetime_en(self):
        report = self.report.with_context(lang="en_US", tz="UTC")
        result = format_datetime(
            report, datetime(2018, 4, 6, 10, 34), "d MMMM yyyy hh:mm a"
        )
        self.assertEqual(result, "6 April 2018 10:34 AM")

    def test_format_datetime_en_in_specific_timezone(self):
        report = self.report.with_context(lang="en_US", tz="Canada/Eastern")
        result = format_datetime(
            report, datetime(2018, 4, 6, 10, 34), "d MMMM yyyy hh:mm a"
        )
        self.assertEqual(
            result, "6 April 2018 06:34 AM"
        )  # Canada/Eastern = UTC - 4 hours

    def test_format_datetime_now_fr_in_utc(self):
        with freeze_time(datetime(2018, 4, 6, 10, 34)):
            report = self.report.with_context(lang="fr_CA", tz="UTC")
            result = format_datetime_now(report, "d MMMM yyyy hh:mm a")
            self.assertEqual(result, "6 avril 2018 10:34 AM")

    def test_format_datetime_now_fr_in_specific_timezone(self):
        with freeze_time(datetime(2018, 4, 6, 10, 34)):
            report = self.report.with_context(lang="fr_CA", tz="Canada/Eastern")
            result = format_datetime_now(report, "d MMMM yyyy hh:mm a")
            self.assertEqual(
                result, "6 avril 2018 06:34 AM"
            )  # Canada/Eastern = UTC - 4 hours

    def test_format_decimal_fr(self):
        report = self.report.with_context(lang="fr_CA")
        result = format_decimal(report, 1500)
        self.assertEqual(result, "1\xa0500,00")

    def test_format_decimal_en(self):
        report = self.report.with_context(lang="en_US")
        result = format_decimal(report, 1500)
        self.assertEqual(result, "1,500.00")

    def test_format_decimal_fr_with_format(self):
        report = self.report.with_context(lang="fr_CA")
        result = format_decimal(report, 1500, amount_format="#,##0.0")
        self.assertEqual(result, "1\xa0500,0")

    def test_format_currency_fr(self):
        report = self.report.with_context(lang="fr_CA")
        result = format_currency(report, 1500, self.env.ref("base.USD"))
        self.assertEqual(result, "1\xa0500,00\xa0$US")

    def test_format_currency_en(self):
        report = self.report.with_context(lang="en_US")
        result = format_currency(report, 1500, self.env.ref("base.USD"))
        self.assertEqual(result, "$1,500.00")

    @data(
        ("en_US", "base.ca", "base.CAD", "$1,500.00"),
        ("en_US", "base.ca", "base.USD", "US$1,500.00"),
        ("en_US", "base.us", "base.CAD", "CA$1,500.00"),
        ("en_US", "base.us", "base.USD", "$1,500.00"),
        ("fr_FR", "base.ca", "base.CAD", "1 500,00 $"),
        ("fr_FR", "base.ca", "base.USD", "1 500,00 $US"),
        ("fr_FR", "base.us", "base.CAD", "1 500,00 $CA"),
        ("fr_FR", "base.us", "base.USD", "1 500,00 $US"),
    )
    @unpack
    def test_format_currency_en__with_specific_country(
        self, lang, country, currency, expected_amount
    ):
        report = self.report.with_context(lang=lang)
        result = format_currency(
            report, 1500, self.env.ref(currency), country=self.env.ref(country)
        )
        self.assertEqual(result, expected_amount)

    @data(
        ("fr_FR", "base.ca", "base.CAD", "1 500,00 $"),
        ("fr_FR", "base.us", "base.CAD", "1 500,00 $CA"),
    )
    @unpack
    def test_country_from_context_used_by_default(
        self, lang, country, currency, expected_amount
    ):
        report = self.report.with_context(lang=lang, country=self.env.ref(country))
        result = format_currency(report, 1500, self.env.ref(currency))
        self.assertEqual(result, expected_amount)

    @data(
        ("fr_FR", "base.us", "base.USD", "1 500,00 $US"),
        ("fr_FR", "base.us", "base.CAD", "1 500,00 $CA"),
    )
    @unpack
    def test_currency_from_context_used_by_default(
        self, lang, country, currency, expected_amount
    ):
        report = self.report.with_context(lang=lang, currency=self.env.ref(currency))
        result = format_currency(report, 1500, country=self.env.ref(country))
        self.assertEqual(result, expected_amount)

    def test_if_format_currency_called_without_currency__raise_error(self):
        report = self.report.with_context(lang="en_US", country=self.env.ref("base.us"))
        with pytest.raises(ValidationError):
            format_currency(report, 1500)

    def test_format_currency_fr_with_format(self):
        report = self.report.with_context(lang="fr_CA")
        result = format_currency(
            report, 1500, self.env.ref("base.USD"), amount_format="#,##0.00\xa0¤¤"
        )
        self.assertEqual(result, "1\xa0500,00\xa0USD")

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
        self.assertEqual(
            text,
            (
                "Lorem Ipsum"
                "\n\n"
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                "Morbi eleifend magna sit amet sem gravida sollicitudin.  \n"
                "Vestibulum metus ipsum, varius in ultricies eget, vulputate eu felis.\n"
            ),
        )

    def test_format_html2text_with_none(self):
        self.assertEqual(format_html2text(self.report, None), "\n")

    @data(
        ("ean13", "501234567890"),
        ("code128", "1234"),
        ("code39", "1234"),
    )
    @unpack
    def test_render_barcode(self, barcode_type, code):
        result = barcode(self.report, code, barcode_type)
        assert isinstance(result[0], io.BytesIO)

    def test_qrcode(self):
        result = qrcode(self.report, "1234")
        assert isinstance(result[0], io.BytesIO)

    def test_qrcode__specific_dimension(self):
        result = qrcode(self.report, "1234", "4.31cm")
        assert result[2] == "4.31cm"
        assert result[3] == "4.31cm"


class TestGroupBy(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env.ref("report_aeroo.aeroo_sample_report")
        cls.contact_1 = cls.env["res.partner"].create({"name": "C1", "type": "contact"})
        cls.invoice_1 = cls.env["res.partner"].create({"name": "I1", "type": "invoice"})
        cls.invoice_2 = cls.env["res.partner"].create({"name": "I2", "type": "invoice"})
        cls.delivery_1 = cls.env["res.partner"].create(
            {"name": "D1", "type": "delivery"}
        )
        cls.delivery_2 = cls.env["res.partner"].create(
            {"name": "D2", "type": "delivery"}
        )

    def test_group_by_with_no_record(self):
        partners = self.env["res.partner"]
        groups = list(group_by(self.report, partners, lambda p: p.type))
        assert len(groups) == 0

    def test_group_by_with_one_record(self):
        groups = list(group_by(self.report, self.contact_1, lambda p: p.type))
        assert len(groups) == 1
        assert groups[0][0] == "contact"
        assert groups[0][1] == self.contact_1

    def test_group_by_with_multiple_records(self):
        partners = (
            self.delivery_1
            | self.contact_1
            | self.invoice_1
            | self.delivery_2
            | self.invoice_2
        )

        groupby = lambda p: p.type

        groups = list(group_by(self.report, partners, groupby))
        assert len(groups) == 3
        assert groups[0][0] == "contact"
        assert groups[0][1] == self.contact_1
        assert groups[1][0] == "delivery"
        assert groups[1][1] == self.delivery_1 | self.delivery_2
        assert groups[2][0] == "invoice"
        assert groups[2][1] == self.invoice_1 | self.invoice_2

    def test_group_by_with_custom_sort(self):
        partners = (
            self.delivery_1
            | self.contact_1
            | self.invoice_1
            | self.delivery_2
            | self.invoice_2
        )

        groupby = lambda p: p.type

        def custom_sort(partner_type):
            if partner_type == "invoice":
                return 1
            elif partner_type == "delivery":
                return 2
            else:
                return 3

        groups = list(group_by(self.report, partners, groupby, sort=custom_sort))
        assert len(groups) == 3
        assert groups[0][0] == "invoice"
        assert groups[0][1] == self.invoice_1 | self.invoice_2
        assert groups[1][0] == "delivery"
        assert groups[1][1] == self.delivery_1 | self.delivery_2
        assert groups[2][0] == "contact"
        assert groups[2][1] == self.contact_1
