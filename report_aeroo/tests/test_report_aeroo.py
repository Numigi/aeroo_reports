# -*- coding: utf-8 -*-
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.modules import module
from odoo.tests import common


class TestAerooReport(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAerooReport, cls).setUpClass()
        image_path = module.get_module_path('report_aeroo') + '/static/img/logo.png'

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

        cls.lang_en = cls.env.ref('base.lang_en')
        cls.lang_fr = cls.env.ref('base.lang_fr')

        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'My Partner 2',
            'lang': 'en_US',
        })

        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report')
        cls.report.write({
            'attachment': None,
            'attachment_use': False,
            'aeroo_out_format_id': cls.env.ref('report_aeroo.aeroo_mimetype_pdf_odt').id,
        })

    def _render_report(self, partners):
        """Render the demo aeroo report for the given partners.

        The report is rendered with a basic user to detect issues related to access rights.

        :param partners: a res.partner recordset
        """
        self.report.sudo(self.env.ref('base.user_demo').id).render(partners.ids, {})

    def _create_report_line(self, lang, company=None):
        self.report.write({
            'aeroo_template_source': 'lines',
            'aeroo_lang_eval': 'o.lang',
        })
        return self.env['aeroo.template.line'].create({
            'report_id': self.report.id,
            'lang_id': lang.id if lang else False,
            'company_id': company.id if company else False,
            'template_data': base64.b64encode(
                self.report._get_aeroo_template_from_file()),
        })

    def test_sample_report_doc(self):
        self.report.aeroo_out_format_id = self.env.ref(
            'report_aeroo.aeroo_mimetype_doc_odt')
        self._render_report(self.partner)

    def test_sample_report_pdf_by_lang(self):
        self._create_report_line(self.lang_en)
        self._render_report(self.partner)

    def test_ifFirstTemplateLineHasNoLang_thenItIsSelected(self):
        line_1 = self._create_report_line(False)
        self._create_report_line(self.lang_en)
        selected_line = self.report._get_aeroo_template_line(self.partner)
        self.assertEqual(selected_line, line_1)

    def test_ifFirstTemplateLineHasWrongLang_thenItIsNotSelected(self):
        self._create_report_line(self.lang_fr)
        line_2 = self._create_report_line(self.lang_en)
        selected_line = self.report._get_aeroo_template_line(self.partner)
        self.assertEqual(selected_line, line_2)

    def test_ifFirstTemplateLineHasWrongCompany_thenItIsNotSelected(self):
        self._create_report_line(self.lang_en, company=self.company_2)
        line_2 = self._create_report_line(self.lang_en, company=self.company)
        selected_line = self.report._get_aeroo_template_line(self.partner)
        self.assertEqual(selected_line, line_2)

    def test_get_template_line_with_2_lines(self):
        self._create_report_line(self.lang_en)
        self._render_report(self.partner)

    def test_sample_report_pdf_with_attachment(self):
        self.report.write({
            'attachment_use': True,
            'attachment': "${o.name}",
        })
        self._render_report(self.partner)

        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', self.partner.id),
            ('res_model', '=', 'res.partner'),
            ('datas_fname', '=', 'My Partner.pdf'),
        ])
        self.assertEqual(len(attachment), 1)

        self._render_report(self.partner)

    def _create_filename_line(self, lang, filename):
        self.report.write({
            'attachment_use': True,
            'aeroo_filename_per_lang': True,
            'aeroo_filename_line_ids': [
                (0, 0, {
                    'lang_id': lang.id,
                    'filename': filename,
                }),
            ]
        })

    def _search_attachment(self):
        return self.env['ir.attachment'].search([
            ('res_id', '=', self.partner.id),
            ('res_model', '=', 'res.partner'),
        ])

    def test_ifPartnerHasNoLang_thenAttachmentNameIsRenderedInEnglish(self):
        self.report.aeroo_lang_eval = "None"

        self._create_filename_line(self.lang_fr, "Rapport de contact: ${o.name}")
        self._create_filename_line(self.lang_en, "Sample Report: ${o.name}")

        self._render_report(self.partner)

        attachment = self._search_attachment()
        self.assertEqual(attachment.datas_fname, 'Sample Report: My Partner.pdf')

    def test_ifReportHasSpecificLang_thenAttachmentNameIsRenderedInSpecificLang(self):
        filename = "Rapport de contact: ${today('d MMMM yyyy')}"
        self._create_filename_line(self.lang_fr, filename)

        self.report.aeroo_lang_eval = "'fr_FR'"
        self.report.aeroo_tz_eval = "'UTC'"

        with freeze_time('2018-04-06 00:00:00'):
            self._render_report(self.partner)

        attachment = self._search_attachment()
        self.assertEqual(attachment.datas_fname, 'Rapport de contact: 6 avril 2018.pdf')

    def test_ifReportHasSpecificTimezone_thenAttachmentNameIsRenderedInSpecificTimezone(self):
        filename = "Sample Report: ${today('MMMM d, yyyy')}"
        self._create_filename_line(self.lang_en, filename)

        self.report.aeroo_lang_eval = "'en_US'"
        self.report.aeroo_tz_eval = "'Canada/Eastern'"

        with freeze_time('2018-04-06 00:00:00'):
            self._render_report(self.partner)

        attachment = self._search_attachment()
        self.assertEqual(attachment.datas_fname, 'Sample Report: April 5, 2018.pdf')

    def test_libreoffice_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def _set_libreoffice_location(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_location = 'sh ' + dir_path + '/' + filename
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_location', file_location)

    def test_fail_after_10ms(self):
        self._set_libreoffice_location('./sleep_10ms_and_fail.sh')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_libreoffice_finish_after_100s(self):
        self._set_libreoffice_location('./libreoffice_100s.sh')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_libreoffice_fail(self):
        self._set_libreoffice_location('./libreoffice_fail.sh')

        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '5')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_multicompany_context_with_lang_and_company(self):
        self._create_report_line(self.lang_en, self.company)
        self._render_report(self.partner)

    def test_multicompany_context_company_not_available(self):
        self._create_report_line(self.lang_en, self.company)
        self.partner.write({'company_id': self.company_2.id})
        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_multicompany_context_with_lang(self):
        self._create_report_line(self.lang_en)
        self._render_report(self.partner)

    def test_multicompany_context_lang_not_available(self):
        self._create_report_line(self.lang_fr)
        with self.assertRaises(ValidationError):
            self._render_report(self.partner)

    def test_sample_report_pdf_with_multiple_export(self):
        self._render_report(self.partner | self.partner_2)

    def test_pdf_low_timeout(self):
        self.env['ir.config_parameter'].set_param(
            'report_aeroo.libreoffice_timeout', '0.01')

        with self.assertRaises(ValidationError):
            self._render_report(self.partner | self.partner_2)
