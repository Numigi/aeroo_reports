# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import api, fields, models


class ResConfigSettingsWithAerooInvoiceTemplate(models.TransientModel):

    _inherit = 'res.config.settings'

    aeroo_invoice_template_id = fields.Many2one(
        'ir.actions.report', 'Aeroo Invoice Report',
        domain="[('report_type', '=', 'aeroo'), ('model', '=', 'account.move')]")

    @api.model
    def get_values(self):
        res = super().get_values()
        template = self.env.ref(
            'report_aeroo_invoice.aeroo_invoice_report', raise_if_not_found=False)
        res['aeroo_invoice_template_id'] = template.id if template else False
        return res

    @api.model
    def set_values(self):
        super().set_values()
        if self.aeroo_invoice_template_id:
            self._update_aeroo_invoice_template()
        else:
            self._empty_aeroo_invoice_template()

    def _update_aeroo_invoice_template(self):
        ref = self.env['ir.model.data'].search([
            ('module', '=', 'report_aeroo_invoice'),
            ('name', '=', 'aeroo_invoice_report'),
        ], limit=1)

        if ref:
            ref.res_id = self.aeroo_invoice_template_id.id
        else:
            self.env['ir.model.data'].create({
                'module': 'report_aeroo_invoice',
                'name': 'aeroo_invoice_report',
                'model': 'ir.actions.report',
                'res_id': self.aeroo_invoice_template_id.id,
                'noupdate': True,
            })

    def _empty_aeroo_invoice_template(self):
        self.env['ir.model.data'].search([
            ('module', '=', 'report_aeroo_invoice'),
            ('name', '=', 'aeroo_invoice_report'),
        ]).unlink()
