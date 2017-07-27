# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.addons.base.res.res_partner import _lang_get


class AccountJournal(models.Model):

    _inherit = "account.journal"

    check_report_id = fields.Many2one(
        'ir.actions.report.xml', 'Check Report', ondelete='restrict')

    check_report_lang = fields.Selection(
        _lang_get, string='Check Report Language')
