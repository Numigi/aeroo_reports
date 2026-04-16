# Copyright 2008-2014 Alistek
# Copyright 2016-2018 Savoir-faire Linux
# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    aeroo_report_ids = fields.Many2many(
        "ir.actions.report",
        "mail_template_aeroo_report_rel",
        "mail_template_id",
        "aeroo_report_id",
        string="Aeroo Reports",
        domain="[('model', '=', model), ('report_type', '=', 'aeroo'), ('multi', '=', False)]",
    )

    def _generate_template(self, res_ids, render_fields):
        """Add aeroo reports to the generated emails."""
        results = super()._generate_template(res_ids, render_fields)
        if isinstance(res_ids, int):
            res_ids = [res_ids]

        for res_id in res_ids:
            values = results.get(res_id)
            if not values:
                continue

            for aeroo_report in self.aeroo_report_ids:
                content, content_type = aeroo_report._render_aeroo([res_id], {})
                content = base64.b64encode(content).decode('utf-8')

                record = self.env[self.model].browse(res_id)
                output_format = aeroo_report.aeroo_out_format_id.code
                file_name = aeroo_report.get_aeroo_filename(record, output_format)

                if "attachments" not in values:
                    values["attachments"] = []

                values["attachments"].append((file_name, content))

        return results
