# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import time
import simplejson
from odoo import api, http
from odoo.modules import registry
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from odoo.addons.web.controllers.main import (
    Reports as ReportController,
    serialize_exception,
)


class Reports(ReportController):

    @http.route('/web/report', type='http', auth="user")
    @serialize_exception
    def index(self, action, token):
        """Add the correct filename to the generated report.

        Otherwise the filename is merely the name of the report.
        """
        response = super(Reports, self).index(action, token)

        action_data = simplejson.loads(action)
        if action_data.get('report_type') != 'aeroo':
            return response

        context = dict(request.context)
        context.update(action_data["context"])

        ids = context.get("active_ids", None)
        if 'datas' in action_data:
            if 'ids' in action_data['datas']:
                ids = action_data['datas'].pop('ids')

        with registry.RegistryManager.get(request.session.db).cursor() as cr:
            env = api.Environment(
                cr, request.session.uid, context)
            report_xml = env['ir.actions.report.xml'].search(
                [('report_name', '=', action_data['report_name'])])

            if report_xml.attachment:
                response.headers['Content-Disposition'] = (
                    "attachment; filename*=UTF-8''%s.%s" % (
                        safe_eval(report_xml.attachment, {
                            'object': env[report_xml.model].browse(ids[0]),
                            'time': time,
                        }),
                        report_xml.out_format.code[3:],
                    )
                )

        return response
