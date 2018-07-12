# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestMailTemplateWithAerooReport(common.SavepointCase):
    """Test generating an aeroo report from a list of records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({'name': 'Partner 1'})
        cls.report = cls.env.ref('report_aeroo.aeroo_sample_report_multi')
        cls.template = cls.env['mail.template'].create({
            'name': 'Partner Email',
            'model_id': cls.env.ref('base.model_res_partner').id,
            'aeroo_report_ids': [(4, cls.report.id)],
        })

    def test_generate_mail_template(self):
        res = self.template.generate_email([self.partner_1.id])
        self.assertEqual(len(res[self.partner_1.id]['attachments']), 1)
