# Copyright 2024 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Aeroo Check Printing",
    "version": "18.0.1.0.0",
    "author": "Numigi",
    "maintainer": "numigi",
    "website": "http://www.savoirfairelinux.com",
    "license": "LGPL-3",
    "category": "Accounting",
    "summary": "Check Printing With Aeroo",
    "depends": [
        "account_check_printing",
        "report_aeroo",
    ],
    "data": [
        "views/account_journal.xml",
    ],
    "demo": [
        "demo/report.xml",
    ],
    "installable": True,
    "application": False,
}
