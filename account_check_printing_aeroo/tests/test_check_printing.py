# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import common


class TestCheckPrinting(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestCheckPrinting, cls).setUpClass()
        fr_ca = cls.env['res.lang'].search(
            [('code', '=', 'fr_CA'), ('active', '=', False)])
        if fr_ca:
            fr_ca.active = True

        cls.partner = cls.env['res.partner'].search([], limit=1)
        cls.report = cls.env.ref('account_check_printing_aeroo.sample_report')
        cls.journal = cls.env['account.journal'].create({
            'name': 'BMO CAD',
            'code': 'BMO',
            'type': 'bank',
            'check_report_id': cls.report.id,
        })
        cls.payment = cls.env['account.payment'].create({
            'partner_id': cls.partner.id,
            'amount': 1234.56,
            'journal_id': cls.journal.id,
            'payment_type': 'outbound',
            'payment_method_id': cls.env.ref(
                'account_check_printing.account_payment_method_check').id,
        })

    def test_01_print_check(self):
        self.payment.do_print_checks()

    def test_02_amount_in_words_fr(self):
        self.journal.check_report_lang = 'fr_CA'
        self.payment._onchange_amount()
        self.assertEquals(
            self.payment.check_amount_in_words,
            'mille deux cent trente-quatre 56/100')

    def test_03_amount_in_words_en(self):
        self.journal.check_report_lang = 'en_US'
        self.payment._onchange_amount()
        self.assertEquals(
            self.payment.check_amount_in_words,
            'one thousand, two hundred and thirty-four 56/100')

    def test_04_amount_in_words_no_lang(self):
        self.journal.check_report_lang = False
        self.payment._onchange_amount()
        self.assertEquals(
            self.payment.check_amount_in_words,
            'one thousand, two hundred and thirty-four 56/100')
