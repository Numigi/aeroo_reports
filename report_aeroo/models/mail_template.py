# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
from odoo import api, fields, models


class MailTemplate(models.Model):

    _inherit = 'mail.template'

    aeroo_report_ids = fields.Many2many(
        'ir.actions.report',
        'mail_template_aeroo_report_rel',
        'mail_template_id',
        'aeroo_report_id',
        string='Aeroo Reports',
        domain="[('model', '=', model), ('report_type', '=', 'aeroo'), ('multi', '=', False)]")

    @api.multi
    def generate_email(self, res_ids, fields=None):
        """Add aeroo reports to the generated emails."""
        results = super().generate_email(res_ids, fields=fields)

        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        # When the super method receives a single record,
        # it returns a single dictionnary of values.
        if not multi_mode:
            results = {res_ids[0]: results}

        for res_id in res_ids:
            values = results[res_id]

            for aeroo_report in self.aeroo_report_ids:
                content, content_type = aeroo_report.render_aeroo([res_id], {})
                content = base64.b64encode(content)

                record = self.env[self.model].browse(res_id)
                output_format = aeroo_report.aeroo_out_format_id.code
                file_name = aeroo_report.get_aeroo_filename(record, output_format)

                if 'attachments' not in values:
                    values['attachments'] = []

                values['attachments'].append((file_name, content))

        return multi_mode and results or results[res_ids[0]]
