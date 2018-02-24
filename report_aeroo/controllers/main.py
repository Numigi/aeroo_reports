# -*- coding: utf-8 -*-
# © 2017 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import json
import time
import simplejson
from odoo import api, http
from odoo.modules import registry
from odoo.http import request, content_disposition
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
        action_data = json.loads(action)
        if action_data.get('report_type') != 'aeroo':
            return super().index(action, token)

        ids = action_data['context']['active_ids']

        report = request.env['ir.actions.report'].browse(action_data['id'])
        content = report.render_aeroo(ids, {})

        code = report.aeroo_out_format_id.code
        file_name = action_data.get('name', 'report') + '.' + code
        report_mimetype = self.TYPES_MAPPING.get(code, 'octet-stream')

        response = request.make_response(
            content,
            headers=[
                ('Content-Disposition', content_disposition(file_name)),
                ('Content-Type', report_mimetype),
                ('Content-Length', len(content))],
            cookies={'fileToken': token})

        return response
