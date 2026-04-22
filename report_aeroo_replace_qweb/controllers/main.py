# Copyright 2024 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import json
import urllib.parse  # <-- Ajout de cette librairie standard
from odoo import http, models
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController
from typing import List


class ReportControllerWithAerooReplacement(ReportController):
    @http.route(["/report/download"], type="http", auth="user")
    def report_download(self, data, context=None, token=None, **kwargs):
        """Dowload a replacement aeroo report instead of a qweb report."""
        requestcontent = json.loads(data)
        url, type_ = requestcontent[0], requestcontent[1]

        if type_ == "qweb-pdf":
            report = _get_report_from_qweb_download_url(url)
            aeroo_report = report.aeroo_report_id

            if aeroo_report:
                record_ids = _get_doc_ids_from_qweb_download_url(url)

                # Odoo 18 : On encode proprement les paramètres de l'URL
                query_params = urllib.parse.urlencode(
                    {
                        "report_id": aeroo_report.id,
                        "record_ids": json.dumps(record_ids),
                        "token": token or "",
                    }
                )

                # Et on utilise le nouveau standard request.redirect
                return request.redirect(f"/web/report_aeroo?{query_params}", local=True)

        return super().report_download(
            data=data, context=context, token=token, **kwargs
        )


def _get_report_from_qweb_download_url(url_: str) -> models.Model:
    report_name = url_.split("/")[3]
    return request.env["ir.actions.report"]._get_report_from_name(report_name)


def _get_doc_ids_from_qweb_download_url(url_: str) -> List[int]:
    url_parts = url_.split("/")

    if len(url_parts) < 5:
        return []

    ids_string = url_parts[4]
    return [int(i) for i in ids_string.split(",")]
