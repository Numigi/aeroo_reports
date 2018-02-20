# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
from odoo import api, fields, models, tools


class AerooTemplateLine(models.Model):

    _name = 'aeroo.template.line'

    report_id = fields.Many2one(
        'ir.actions.report', 'Report', required=True,
        ondelete='cascade')
    lang_id = fields.Many2one('res.lang', 'Language', required=True)
    company_id = fields.Many2one('res.company', 'Company')

    template_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
    ], string='Template source', default='database')

    template_data = fields.Binary('Template')
    template_filename = fields.Binary('File Name')
    template_location = fields.Char('File Location')

    def get_aeroo_template(self, record):
        if self.template_source == 'file':
            with tools.file_open(self.template_location, mode='rb') as file:
                return file.read()
        else:
            return base64.b64decode(self.aeroo_template_data)
