# Copyright 2017 Savoir-faire Linux
# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):

    _inherit = "account.payment"

    def do_print_checks(self):
        journal = self.mapped("journal_id")
        if len(journal) != 1:
            raise UserError(
                _(
                    "In order to generate checks in batch, all selected "
                    "payments must belong to the same journal (bank account)."
                )
            )
        if journal.check_report_id:
            return journal.check_report_id.report_action(self)
        return super().do_print_checks()
