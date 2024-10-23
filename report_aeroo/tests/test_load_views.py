# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestLoadViews(TransactionCase):
    def test_aeroo_template_data_not_in_result(self):
        self.env.ref("report_aeroo.aeroo_sample_report").create_action()
        result = self.env["res.partner"].get_views([(None, "tree")], {"toolbar": True})
        actions = result["fields_views"]["tree"]["toolbar"]["print"]
        assert "aeroo_template_data" not in actions[0]
