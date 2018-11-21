# -*- coding: utf-8 -*-
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from odoo.modules import module
from odoo.tests import common


class TestAerooReportMulti(common.SavepointCase):
    """Test generating an aeroo report from a list of records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        image_path = module.get_module_path('report_aeroo') + '/static/img/logo.png'

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Partner 1',
            'lang': 'en_US',
            'image': base64.b64encode(open(image_path, 'rb').read())
        })

        cls.partner_2 = cls.partner_1.copy()

        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report_multi')

    def _render_report(self, partners):
        """Render the demo aeroo report for the given partners.

        The report is rendered with a basic user to detect issues related to access rights.

        :param partners: a res.partner recordset
        """
        self.report.sudo(self.env.ref('base.user_demo').id).render(partners.ids, {})

    def test_generate_report_with_pdf_format_and_multiple_records(self):
        self.report.aeroo_out_format_id = self.env.ref('report_aeroo.aeroo_mimetype_pdf_odt')
        self._render_report(self.partner_1 | self.partner_2)

    def test_generate_report_with_odt_format_and_multiple_records(self):
        self.report.aeroo_out_format_id = self.env.ref('report_aeroo.aeroo_mimetype_doc_odt')
        self._render_report(self.partner_1 | self.partner_2)

    def test_generate_report_with_single_record(self):
        self.report.aeroo_out_format_id = self.env.ref('report_aeroo.aeroo_mimetype_doc_odt')
        self._render_report(self.partner_1 | self.partner_2)
