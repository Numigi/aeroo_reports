# -*- coding: utf-8 -*-
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
import stat
from PIL import Image
from odoo.exceptions import ValidationError
from odoo.modules import module
from odoo.tests import common


class TestAerooReportLangEval(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.lang = 'es_AR'

        cls.partner = cls.env['res.partner'].create({
            'name': 'My Partner',
            'lang': 'fr_FR',
        })

        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report_id')

    def test_eval_lang_using_the_lang_defined_on_the_partner(self):
        self.report.aeroo_lang_eval = "o.lang"
        self.assertEqual(self.report._get_aeroo_lang(self.partner), 'fr_FR')

    def test_eval_lang_using_the_lang_of_the_user(self):
        self.report.aeroo_lang_eval = "user.lang"
        self.assertEqual(self.report._get_aeroo_lang(self.partner), 'es_AR')

    def test_if_lang_eval_is_not_defined_then_the_laguage_used_is_en_us(self):
        self.report.aeroo_lang_eval = None
        self.assertEqual(self.report._get_aeroo_lang(self.partner), 'en_US')
