# Copyright 2016-2018 Savoir-faire Linux
# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAerooReportAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env.ref("report_aeroo.aeroo_sample_report")
        cls.user = cls.env.ref("base.user_demo")
        cls.user.groups_id |= cls.env.ref("report_aeroo.group_aeroo_manager")

    def test_report_create(self):
        assert self.report.with_user(self.user.id).copy({})

    def test_report_unlink(self):
        self.report.with_user(self.user.id).unlink()
        assert not self.report.exists()
