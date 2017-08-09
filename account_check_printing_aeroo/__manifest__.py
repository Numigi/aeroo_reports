# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Aeroo Check Printing',
    'version': '10.0.1.0.0',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': 'Check Printing With Aeroo',
    'depends': [
        'account_check_printing',
        'report_aeroo',
    ],
    'data': [
        'views/account_journal.xml',
        'views/account_payment.xml',
    ],
    'demo': [
        'demo/report.xml',
    ],
    'external_dependencies': {
        'python': ['num2words'],
    },
    'installable': True,
    'application': False,
}
