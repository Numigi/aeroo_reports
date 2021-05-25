# © 2017 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    check_report_id = fields.Many2one(
        'ir.actions.report', 'Check Report', ondelete='restrict',
        domain="[('report_type', '=', 'aeroo'), ('model', '=', 'account.payment')]")
