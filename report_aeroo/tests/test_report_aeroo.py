# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
import stat
from PIL import Image
from odoo.exceptions import ValidationError
from odoo.modules import module
from odoo.tests import common


class TestAerooReport(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAerooReport, cls).setUpClass()
        image_path = (
            module.get_module_path('report_aeroo') + '/static/img/logo.png')

        cls.company = cls.env['res.company'].create({
            'name': 'My Company',
        })
        cls.company_2 = cls.env['res.company'].create({
            'name': 'My Company 2',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'My Partner',
            'lang': 'en_US',
            'company_id': cls.company.id,
            'image': base64.b64encode(open(image_path, 'rb').read())
        })

        cls.lang_en = cls.env.ref('base.lang_en').id
        cls.lang_fr = cls.env.ref('base.lang_fr').id

        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'My Partner 2',
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
            'report_aeroo.pdftk_location', 'pdftk')

        cls.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '60')

    def _render_report(self, partners):
        self.report.render(partners.ids, {})

    def test_01_sample_report_doc(self):
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_doc_odt')
        self._render_report(self.partner)

    def _create_report_line(self, lang, company=None):
        self.report.write({
            'aeroo_template_source': 'lines',
            'aeroo_lang_eval': 'o.lang',
            'aeroo_out_format_id': self.env.ref(
                'report_aeroo.aeroo_mimetype_pdf_odt').id,
        })
        self.report.aeroo_template_line_ids = [(0, 0, {
            'lang_id': lang,
            'company_id': company,
            'template_source': 'file',
            'template_location': 'report_aeroo/demo/template.odt',
        })]

    def test_02_sample_report_pdf_by_lang(self):
        self._create_report_line(self.lang_en)
        self._render_report(self.partner)

    def test_03_sample_report_pdf_with_attachment(self):
        self.report.write({
            'attachment_use': True,
            'attachment': "object.name",
        })
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')
        self._render_report(self.partner)

        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', self.partner.id),
            ('res_model', '=', 'res.partner'),
            ('datas_fname', '=', 'My Partner.pdf'),
        ])
        self.assertEqual(len(attachment), 1)

        self._render_report(self.partner)

    def test_04_libreoffice_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def _set_libreoffice_location(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_location = 'sh ' + dir_path + '/' + filename
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_location', file_location)

    def test_05_fail_after_10ms(self):
        self._set_libreoffice_location('./sleep_10ms.sh')
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_06_libreoffice_finish_after_100s(self):
        self._set_libreoffice_location('./libreoffice_100s.sh')
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_07_libreoffice_fail(self):
        self._set_libreoffice_location('./libreoffice_fail.sh')
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_08_multicompany_context(self):
        self._create_report_line(self.lang_en, self.company.id)
        self._render_report(self.partner)

    def test_09_multicompany_context(self):
        self._create_report_line(self.lang_en, self.company.id)
        self.partner.write({'company_id': self.company_2.id})
        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_10_multicompany_context(self):
        self._create_report_line(self.lang_en)
        self._render_report(self.partner)

    def test_11_multicompany_context(self):
        self._create_report_line(self.lang_fr)
        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_12_sample_report_pdf_with_multiple_export(self):
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')
        self._render_report(self.partner | self.partner_2)

    def test_13_pdf_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_pdf_odt')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner | self.partner_2)
