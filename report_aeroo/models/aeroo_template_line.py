# Copyright 2016-2018 Savoir-faire Linux
# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
from odoo import fields, models


class AerooTemplateLine(models.Model):

    _name = "aeroo.template.line"
    _order = "sequence"
    _description = "Aeroo Template Line"

    sequence = fields.Integer()
    report_id = fields.Many2one(
        "ir.actions.report", "Report", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one("res.company", "Company")
    lang_id = fields.Many2one("res.lang", "Language")
    template_data = fields.Binary("Template", required=True)
    template_filename = fields.Char("File Name")

    def get_aeroo_template(self, record):
        return base64.b64decode(self.template_data)
