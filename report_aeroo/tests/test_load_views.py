# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestLoadViews(TransactionCase):
    def test_aeroo_template_data_not_in_result(self):
        simple_report = self.env.ref("report_aeroo.aeroo_sample_report")
        simple_report.create_action()
        view = self.env.ref("base.view_partner_tree")
        result = self.env["res.partner"].get_views(
            [(view.id, "list")], {"toolbar": True}
        )
        action_reports = result["views"]["list"]["toolbar"]["print"]
        report_ids = [report["id"] for report in action_reports]
        assert simple_report.id in report_ids
