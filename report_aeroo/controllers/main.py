# © 2017 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import json
import time
from odoo import api, http, _
from odoo.modules import registry
from odoo.http import request, content_disposition
from odoo.addons.web.controllers.main import serialize_exception
from odoo.exceptions import ValidationError

MIMETYPES_MAPPING = {
    'doc': 'application/vnd.ms-word',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet',
    'odt': 'application/vnd.oasis.opendocument.text',
    'pdf': 'application/pdf',
    'xls': 'application/vnd.ms-excel',
}

DEFAULT_MIMETYPE = 'octet-stream'


class AerooReportController(http.Controller):

    @http.route('/web/report_aeroo', type='http', auth="user")
    @serialize_exception
    def generate_aeroo_report(self, report_id, record_ids, token, debug=False):
        """Generate an aeroo report.

        Add the filename of the generated report to the response headers.
        If the aeroo report is generated for multiple records, the
        file name is simply {report.name}.pdf.
        """
        report_id = int(report_id)
        record_ids = json.loads(record_ids)

        report = request.env['ir.actions.report'].browse(report_id)
        content, out_format = report._render_aeroo(record_ids, {})


        if len(record_ids) == 1:
            record = request.env[report.model].browse(record_ids[0])
            file_name = report.get_aeroo_filename(record, out_format)
        else:
            file_name = '%s.%s' % (report.name, out_format)

        report_mimetype = MIMETYPES_MAPPING.get(out_format, DEFAULT_MIMETYPE)

        response = request.make_response(
            content,
            headers=[
                ('Content-Disposition', content_disposition(file_name)),
                ('Content-Type', report_mimetype),
                ('Content-Length', len(content))],
            cookies={'fileToken': token})

        return response

    @staticmethod
    def _get_aeroo_report_from_name(report_name):
        """Get an aeroo report template from the given report name."""
        report = request.env['ir.actions.report'].search([
            ('report_name', '=', report_name),
        ])
        if not report:
            raise ValidationError(
                _('No aeroo report found with the name {report_name}.'),
                report_name=report_name)

        if len(report) > 1:
            report_display_names = '\n'.join(report.mapped('display_name'))
            raise ValidationError(_(
                'Multiple aeroo reports found with the same name ({report_name}):\n\n'
                '{report_display_names}').format(
                    report_name=report_name,
                    report_display_names=report_display_names))

        return report
