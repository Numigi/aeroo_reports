# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import stat
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestAerooReport(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAerooReport, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'My Partner',
            'lang': 'en_US',
        })
        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report_id')
        cls.report.write({
            'attachment': None,
            'attachment_use': False,
        })
        cls.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_location', 'libreoffice')

        cls.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '60')

    def test_01_sample_report_doc(self):
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_doc_odt')
        self.partner.print_report('sample_report', {})

    def test_02_sample_report_pdf(self):
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')
        self.partner.print_report('sample_report', {})

    def test_03_sample_report_pdf_by_lang(self):
        self.report.write({
            'tml_source': 'lang',
            'lang_eval': 'o.lang',
        })
        self.report.report_line_ids = [(0, 0, {
            'lang_id': self.env.ref('base.lang_en').id,
            'template_source': 'file',
            'template_location': 'report_aeroo_sample/report/template.odt',
        })]
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')
        self.partner.print_report('sample_report', {})

    def test_03_sample_report_pdf_with_attachment(self):
        self.report.write({
            'attachment_use': True,
            'attachment': "object.name",
        })
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')
        self.partner.print_report('sample_report', {})

        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', self.partner.id),
            ('res_model', '=', 'res.partner'),
            ('datas_fname', '=', 'My Partner.pdf'),
        ])
        self.assertEqual(len(attachment), 1)

        self.partner.print_report('sample_report', {})

    def test_04_libreoffice_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')

        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})

    def _set_libreoffice_location(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_location = dir_path + '/' + filename
        os.chmod(
            file_location,
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_location', file_location)

    def test_05_fail_after_10ms(self):
        self._set_libreoffice_location('./sleep_10ms.sh')
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')

        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})

    def test_06_libreoffice_finish_after_100s(self):
        self._set_libreoffice_location('./libreoffice_100s.sh')
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})

    def test_07_libreoffice_fail(self):
        self._set_libreoffice_location('./libreoffice_fail.sh')
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})
