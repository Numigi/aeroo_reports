# © 2019 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import json
from odoo import http, models
from odoo.http import request
from odoo.addons.web.controllers.main import ReportController
from typing import List


class ReportControllerWithAerooReplacement(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        """Dowload a replacement aeroo report instead of a qweb report.

        If the report is qweb-pdf and it has a replacement aeroo report,
        the request is redirected to /web/report_aeroo.

        Without inheriting this method, the replacement report is printed,
        but with the filename defined on the qweb report.
        """
        requestcontent = json.loads(data)
        url, type_ = requestcontent[0], requestcontent[1]

        if type_ == "qweb-pdf":
            report = _get_report_from_qweb_download_url(url)
            aeroo_report = report.aeroo_report_id

            if aeroo_report:
                record_ids = _get_doc_ids_from_qweb_download_url(url)
                return http.local_redirect('/web/report_aeroo', {
                    'report_id': aeroo_report.id,
                    'record_ids': json.dumps(record_ids),
                    'token': token,
                })

        return super().report_download(data, token)


def _get_report_from_qweb_download_url(url_: str) -> models.Model:
    """Get the report object from the download URL of a qweb report.

    The url is expected to have the following format:

        /report/download/report_name/doc_ids?query_string
    """
    report_name = url_.split('/')[3]
    return request.env['ir.actions.report']._get_report_from_name(report_name)


def _get_doc_ids_from_qweb_download_url(url_: str) -> List[int]:
    """Get the report object from the download URL of a qweb report.

    The url is expected to have the following format:

        /report/download/report_name/doc_ids?query_string

    The parameter doc_ids inside the URL contains the ids of the
    objects seperated by commas.
    """
    url_parts = url_.split('/')

    if len(url_parts) < 5:
        return []

    ids_string = url_parts[4]
    return [int(i) for i in ids_string.split(',')]
