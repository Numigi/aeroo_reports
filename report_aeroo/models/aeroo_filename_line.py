# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from odoo import fields, models


class AerooFilenameLine(models.Model):

    _name = 'aeroo.filename.line'
    _order = 'sequence'

    sequence = fields.Integer()
    report_id = fields.Many2one(
        'ir.actions.report', 'Report', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Company')
    lang_id = fields.Many2one('res.lang', 'Language')
    filename = fields.Char(required=True)
