# -*- coding: utf-8 -*-
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAerooReportCompanyEval(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'My Company',
        })

        cls.company_2 = cls.env['res.company'].create({
            'name': 'My Company 2',
        })

        cls.env.user.write({
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'My Partner',
            'company_id': cls.company_2.id,
        })

        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report')

    def test_eval_company_using_the_company_defined_on_the_partner(self):
        self.report.aeroo_company_eval = "o.company_id"
        self.assertEqual(self.report._get_aeroo_company(self.partner), self.company_2)

    def test_if_no_company_defined_on_the_partner_then_no_company_is_used(self):
        self.report.aeroo_company_eval = "o.company_id"
        self.partner.company_id = None
        self.assertFalse(self.report._get_aeroo_company(self.partner))

    def test_eval_company_using_the_company_of_the_user(self):
        self.report.aeroo_company_eval = "user.company_id"
        self.assertEqual(self.report._get_aeroo_company(self.partner), self.company)

    def test_if_company_eval_is_not_defined_then_the_company_of_the_user_is_used(self):
        self.report.aeroo_company_eval = None
        self.assertEqual(self.report._get_aeroo_company(self.partner), self.company)
