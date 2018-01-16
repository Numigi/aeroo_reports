# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import stat
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
            'image': open(image_path, 'rb').read().encode('base64')
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

    def test_01_sample_report_doc(self):
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_doc_odt')
        self.partner.print_report('sample_report', {})

    def _create_report_line(self, lang, company=None):
        self.report.write({
            'tml_source': 'lang',
            'lang_eval': 'o.lang',
            'out_format': self.env.ref(
                'report_aeroo.report_mimetypes_pdf_odt').id,
        })
        self.report.report_line_ids = [(0, 0, {
            'lang_id': lang,
            'company_id': company,
            'template_source': 'file',
            'template_location': 'report_aeroo/demo/template.odt',
        })]

    def test_02_sample_report_pdf_by_lang(self):
        self._create_report_line(self.lang_en)
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
        file_location = 'sh ' + dir_path + '/' + filename
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

    def test_08_multicompany_context(self):
        self._create_report_line(self.lang_en, self.company.id)
        self.partner.print_report('sample_report', {})

    def test_09_multicompany_context(self):
        self._create_report_line(self.lang_en, self.company.id)
        self.partner.write({'company_id': self.company_2.id})
        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})

    def test_10_multicompany_context(self):
        self._create_report_line(self.lang_en)
        self.partner.print_report('sample_report', {})

    def test_11_multicompany_context(self):
        self._create_report_line(self.lang_fr)
        with self.assertRaises(ValidationError):
            self.partner.print_report('sample_report', {})

    def test_12_sample_report_pdf_with_multiple_export(self):
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')
        partners = self.partner | self.partner_2
        partners.print_report('sample_report', {})

    def test_13_pdf_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')
        self.report.out_format = self.env.ref(
            'report_aeroo.report_mimetypes_pdf_odt')
        partners = self.partner | self.partner_2

        with self.assertRaises(ValidationError):
            partners.print_report('sample_report', {})
