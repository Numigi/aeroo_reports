# -*- coding: utf-8 -*-
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Report Aeroo Invoice',
    'version': '1.0.0',
    'category': 'Generic Modules/Aeroo Reports',
    'summary': 'Allow Printing an Aeroo Invoice',
    'author': 'Numigi',
    'maintainer': 'Numigi',
    'website': 'https://bit.ly/numigi-com',
    'depends': [
        'account',
        'report_aeroo',
    ],
    'data': [
        'views/res_config_settings.xml',
        'views/portal.xml',
    ],
    'demo': [
        'demo/invoice.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
