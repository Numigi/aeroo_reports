# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from collections import defaultdict
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

    def get_payment_lines(self):
        """
        In Odoo, the relational model does not allow to properly print
        what was paid on a payment.

        When you pay multiple invoices and credit note, you never know
        what invoice is actually partially reconciled with the payment.

        The amount of a credit not could be spread on multiple partial
        move reconciles.

        The idea of this method is to generate lines to print on a check
        stub or summary of paiement report.
        """
        lines = defaultdict(float)

        credits = (
            self.mapped('invoice_ids.move_id.line_ids.matched_debit_ids')
            .filtered(
                lambda l: l.debit_move_id in self.move_line_ids or
                l.debit_move_id.invoice_id in self.invoice_ids
            )
        )

        debits = (
            self.mapped('invoice_ids.move_id.line_ids.matched_credit_ids')
            .filtered(
                lambda l: l.credit_move_id in self.move_line_ids or
                l.credit_move_id.invoice_id in self.invoice_ids
            )
        )

        for line in credits:
            ref = line.credit_move_id.ref
            date = line.credit_move_id.date
            date_maturity = line.credit_move_id.date_maturity
            name = line.credit_move_id.name
            index = (ref, date, date_maturity, name)

            if line.currency_id:
                amount = line.amount_currency
            else:
                amount = line.amount

            lines[index] += self.to_payment_currency(amount, line.currency_id)

        for line in debits:
            ref = line.debit_move_id.ref
            date = line.debit_move_id.date
            date_maturity = line.debit_move_id.date_maturity
            name = line.debit_move_id.name
            index = (ref, date, date_maturity, name)

            if line.currency_id:
                amount = line.amount_currency
            else:
                amount = line.amount

            lines[index] -= self.to_payment_currency(amount, line.currency_id)

        # Round amounts globally after adding them together
        for key, amount in lines.items():
            lines[key] = self.currency_id.round(amount)

        res = [
            {
                'ref': key[0],
                'date': key[1],
                'date_maturity': key[2],
                'name': key[3],
                'amount': amount
            } for key, amount in lines.items()
        ]

        res.sort(key=lambda r: r['ref'])

        return res

    def to_payment_currency(self, amount, currency):
        if not currency:
            currency = self.company_id.currency_id

        if currency == self.currency_id:
            return amount

        return currency.compute(amount, self.currency_id, round=False)
