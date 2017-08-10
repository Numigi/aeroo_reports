# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from num2words import num2words
from odoo import api, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):

    _inherit = "account.payment"

    @api.multi
    def do_print_checks(self):
        if len(self.mapped('journal_id')) != 1:
            raise UserError(_(
                'In order to generate checks in batch, all selected '
                'payments must belong to the same journal (bank account).'
            ))
        journal = self[0].journal_id
        if journal.check_report_id:
            return self.env['report'].get_action(
                self, journal.check_report_id.report_name)
        return super(AccountPayment, self).do_print_checks()

    def _get_check_amount_in_words(self, amount):
        if self.currency_id.rounding != 0.01:
            return (
                super(AccountPayment, self)._get_check_amount_in_words(amount)
            )
        lang = self.journal_id.check_report_lang
        amount_in_word = num2words(int(amount), lang=lang or 'en_US')
        cents = int(amount * 100) % 100
        return '%s %s/100' % (amount_in_word, cents)
