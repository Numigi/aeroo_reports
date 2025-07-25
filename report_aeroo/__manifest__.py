# Copyright 2008-2014 Alistek
# Copyright 2016-2018 Savoir-faire Linux
# © Numigi (tm) and all its contributors (https://numigi.com/r/home)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

{
    "name": "Aeroo Reports",
    "version": "1.0.1",
    "category": "Generic Modules/Aeroo Reports",
    "summary": "Enterprise grade reporting solution",
    "author": "Alistek",
    "maintainer": "Numigi",
    "website": "https://numigi.com/r/home",
    "depends": ["mail"],
    "external_dependencies": {
        "python": ["aeroolib", "babel", "genshi"],
    },
    "data": [
        "security/security.xml",
        "views/ir_actions_report.xml",
        "views/mail_template.xml",
        "views/report_aeroo_assets.xml",
        "data/report_aeroo_data.xml",
        "security/ir.model.access.csv",
    ],
    "demo": ["demo/report_sample.xml"],
    "license": "GPL-3 or any later version",
    "installable": True,
}
