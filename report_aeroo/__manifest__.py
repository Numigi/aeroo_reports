# Copyright 2008-2014 Alistek
# Copyright 2016-2018 Savoir-faire Linux
# Copyright 2018-Today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

{
    "name": "Aeroo Reports",
    "version": "16.0.1.0.1",
    "category": "Generic Modules/Aeroo Reports",
    "summary": "Enterprise grade reporting solution",
    "author": "Alistek",
    "maintainer": "Numigi",
    "website": "https://bit.ly/numigi-com",
    "depends": ["mail"],
    "external_dependencies": {
        "python": ["aeroolib", "babel", "genshi"],
    },
    "data": [
        "security/security.xml",
        "views/ir_actions_report.xml",
        "views/mail_template.xml",
        "data/report_aeroo_data.xml",
        "security/ir.model.access.csv",
    ],
    "demo": ["demo/report_sample.xml"],
    "assets": {
        "web.assets_backend": [
            "report_aeroo/static/src/js/action_manager.js"
        ],
    },
    "license": "GPL-3 or any later version",
    "installable": True,
}
