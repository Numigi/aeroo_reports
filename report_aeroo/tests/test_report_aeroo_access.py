# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAerooReportAccess(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report')
        cls.user = cls.env.ref('base.user_demo')
        cls.user.groups_id |= cls.env.ref('report_aeroo.group_aeroo_manager')

    def test_report_create(self):
        assert self.report.sudo(self.user).copy({})

    def test_report_unlink(self):
        self.report.sudo(self.user).unlink()
        assert not self.report.exists()
