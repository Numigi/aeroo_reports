# -*- coding: utf-8 -*-
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
from odoo import api, fields, models, tools


class AerooTemplateLine(models.Model):

    _name = 'aeroo.template.line'
    _order = 'sequence'

    sequence = fields.Integer()
    report_id = fields.Many2one(
        'ir.actions.report', 'Report', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Company')
    lang_id = fields.Many2one('res.lang', 'Language')
    template_data = fields.Binary('Template', required=True)
    template_filename = fields.Binary('File Name')

    def get_aeroo_template(self, record):
        return base64.b64decode(self.template_data)
