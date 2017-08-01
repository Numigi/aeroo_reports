# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from num2words import num2words
from odoo import api, models


class AccountPayment(models.Model):

    _inherit = "account.payment"

    @api.multi
    def do_print_checks(self):
        if self.journal_id.check_report_id:
            return self.env['report'].get_action(
                self, self.journal_id.check_report_id.report_name)
        return super(AccountPayment, self).do_print_checks()

    def _get_check_amount_in_words(self, amount):
        lang = self.journal_id.check_report_lang
        amount_in_word = num2words(int(amount), lang=lang or 'en_US')
        cents = int(amount * 100) % 100
        return '%s %s/100' % (amount_in_word, cents)
