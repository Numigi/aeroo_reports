# Copyright 2008-2014 Alistek
# Copyright 2016-2018 Savoir-faire Linux
# Copyright 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import datetime
import logging
import os
import subprocess
import traceback
from aeroolib.plugins.opendocument import Template, OOSerializer
from dateutil.relativedelta import relativedelta
from functools import wraps
from io import BytesIO
from genshi.template.base import Context as GenshiContext
from tempfile import NamedTemporaryFile

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import file_open

from ..namespace import AerooNamespace
from ..extra_functions import aeroo_function_registry

_logger = logging.getLogger(__name__)

# Odoo 18 / Python 3.11+ uses pypdf (wrapped by Odoo) instead of the dead PyPDF2 library.
try:
    from odoo.tools.pdf import OdooPdfFileReader, OdooPdfFileWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import red
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    _logger.warning("pypdf and/or reportlab not available, watermark feature will not work!")

try:
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        variable_start_string="${",
        variable_end_string="}",
        line_statement_prefix="%",
        trim_blocks=True,
    )
    mako_template_env.globals.update(
        {
            "str": str,
            "datetime": datetime,
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "filter": filter,
            "map": map,
            "round": round,
        }
    )
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _get_default_aeroo_out_format(self):
        return self.env["aeroo.mimetype"].search([("code", "=", "odt")], limit=1)

    @api.model
    def _get_in_aeroo_mimetypes(self):
        types = self.env["aeroo.mimetype"].search([])
        return (
            [(t.code, t.name) for t in types]
            if types
            else [("odt", "odt"), ("ods", "ods")]
        )

    active = fields.Boolean(default=True)
    report_type = fields.Selection(
        selection_add=[("aeroo", "Aeroo Reports")],
        ondelete={"aeroo": "cascade"},
    )
    aeroo_in_format = fields.Selection(
        selection="_get_in_aeroo_mimetypes",
        string="Template Mime-type",
        prefetch=False,
        default=lambda self: "odt",
    )
    aeroo_out_format_id = fields.Many2one(
        "aeroo.mimetype",
        "Output Mime-type",
        prefetch=False,
        default=_get_default_aeroo_out_format,
    )
    aeroo_template_source = fields.Selection(
        [
            ("database", "Database"),
            ("file", "File"),
            ("lines", "Different Template per Language / Company"),
        ],
        prefetch=False,
        string="Template source",
        default="database",
    )
    aeroo_template_data = fields.Binary(prefetch=False)
    aeroo_template_path = fields.Char(prefetch=False)
    aeroo_template_line_ids = fields.One2many(
        "aeroo.template.line", "report_id", "Templates by Language", prefetch=False
    )
    aeroo_lang_eval = fields.Char(
        "Language Evaluation",
        help="Python expression used to determine the language of the record being printed.",
        prefetch=False,
        default="user.lang",
    )
    aeroo_tz_eval = fields.Char(
        "Timezone Evaluation",
        help="Python expression used to determine the timezone used for formatting dates.",
        prefetch=False,
        default="user.tz",
    )
    aeroo_company_eval = fields.Char(
        "Company Evaluation",
        help="Python expression used to determine the company of the record being printed.",
        prefetch=False,
        default="user.company_id",
    )
    aeroo_country_eval = fields.Char(
        "Country Evaluation",
        help="Python expression used to determine the country of the record being printed.",
        prefetch=False,
        default="user.company_id.country_id",
    )
    aeroo_currency_eval = fields.Char(
        "Currency Evaluation",
        help="Python expression used to determine the currency of the record being printed.",
        prefetch=False,
        default="user.company_id.currency_id",
    )

    def report_action(self, docids, data=None, **kwargs):
        """ Passing **kwargs ensures compatibility with future Odoo framework signatures. """
        res = super().report_action(docids, data=data, **kwargs)
        res["id"] = self.id
        return res

    def read(self, fields=None):
        """ The 'load' argument has been removed from read() in recent Odoo versions. """
        if not fields:
            fields = [k for k, v in self._fields.items() if v.type != "binary"]
        return super().read(fields)

    def _get_aeroo_template(self, record):
        if self.aeroo_template_source == "file":
            return self._get_aeroo_template_from_file()
        if self.aeroo_template_source == "database":
            return self._get_aeroo_template_from_database()
        return self._get_aeroo_template_from_lines(record)

    def _get_aeroo_template_from_file(self):
        with file_open(self.aeroo_template_path, "rb") as file:
            return file.read()

    def _get_aeroo_template_from_database(self):
        return base64.b64decode(self.aeroo_template_data)

    def _get_aeroo_template_from_lines(self, record):
        template_line = self._get_aeroo_template_line(record)
        return template_line.get_aeroo_template(record)

    def _get_aeroo_template_line(self, record):
        lang = self._get_aeroo_lang(record)
        company = self._get_aeroo_company(record)

        def line_matches_lang(line):
            return not line.lang_id or line.lang_id.code == lang

        def line_matches_company(line):
            return not line.company_id or line.company_id == company

        line = next(
            (
                line for line in self.aeroo_template_line_ids
                if line_matches_lang(line) and line_matches_company(line)
            ),
            None,
        )

        if line is None:
            raise ValidationError(
                _(
                    "Could not render report {report} for the "
                    "company {company} in the language {lang}."
                ).format(
                    report=self.name,
                    company=company.name,
                    lang=lang,
                )
            )
        return line

    def _get_aeroo_variable_eval_context(self, record):
        return {"o": record, "user": self.env.user}

    def _get_aeroo_lang(self, record):
        lang = (
            safe_eval(self.aeroo_lang_eval, self._get_aeroo_variable_eval_context(record))
            if self.aeroo_lang_eval else None
        )
        return lang or "en_US"

    def _get_aeroo_timezone(self, record):
        return (
            safe_eval(self.aeroo_tz_eval, self._get_aeroo_variable_eval_context(record))
            if self.aeroo_tz_eval else None
        )

    def _get_aeroo_company(self, record):
        return (
            safe_eval(self.aeroo_company_eval, self._get_aeroo_variable_eval_context(record))
            if self.aeroo_company_eval else self.env.user.company_id
        )

    def _get_aeroo_country(self, record):
        return (
            safe_eval(self.aeroo_country_eval, self._get_aeroo_variable_eval_context(record))
            if self.aeroo_country_eval else None
        )

    def _get_aeroo_currency(self, record):
        return (
            safe_eval(self.aeroo_currency_eval, self._get_aeroo_variable_eval_context(record))
            if self.aeroo_currency_eval else None
        )

    def _get_aeroo_context(self, record):
        return {
            "lang": self._get_aeroo_lang(record),
            "tz": self._get_aeroo_timezone(record),
            "country": self._get_aeroo_country(record),
            "currency": self._get_aeroo_currency(record),
            "relativedelta": relativedelta,
        }

    def _get_aeroo_libreoffice_timeout(self):
        return 60

    def _render_aeroo(self, doc_ids, data=None, force_output_format=None):
        output_format = force_output_format or self.aeroo_out_format_id.code
        data = data or {}

        if len(doc_ids) > 1:
            return self._render_aeroo_multi(doc_ids, data, output_format)

        record = self.env[self.model].browse(doc_ids[0])
        report_context = self._get_aeroo_context(record)
        self = self.with_context(**report_context)

        attachment_output = self._find_aeroo_report_attachment(record, output_format)
        if attachment_output:
            return attachment_output, output_format

        template = self._get_aeroo_template(record)

        current_report_data = dict(
            data,
            o=record.with_context(**report_context),
            company=self._get_aeroo_company(record),
            **report_context
        )
        output = self._render_aeroo_content(template, current_report_data, output_format)

        if self.attachment_use:
            self._create_aeroo_attachment(record, output, output_format)

        return output, output_format

    def _render_aeroo_content(self, template, data, output_format):
        template_io = BytesIO()
        template_io.write(template)
        serializer = OOSerializer(template_io)

        report_context = GenshiContext(**data)
        report_context.update(self._get_aeroo_extra_functions())
        report_context["t"] = AerooNamespace()

        output = (
            Template(source=template_io, serializer=serializer)
            .generate(report_context)
            .render()
            .getvalue()
        )

        if self.aeroo_in_format != output_format:
            output = self._convert_aeroo_report(output, output_format)

        if output_format == "pdf" and self._should_add_test_watermark():
            output = self._add_test_watermark_to_pdf(output)

        return output

    def _get_aeroo_extra_functions(self):
        return {
            k: self._wrap_aeroo_function(v)
            for k, v in aeroo_function_registry.get_functions().items()
        }

    def _wrap_aeroo_function(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(self, *args, **kwargs)
        return wrapper

    def get_aeroo_filename(self, record, output_format):
        if self.attachment:
            filename = self._eval_aeroo_attachment_filename(self.attachment, record)
            return ".".join((filename, output_format))
        else:
            return ".".join((self.name, output_format))

    def _eval_aeroo_attachment_filename(self, filename, record):
        template = mako_template_env.from_string(tools.ustr(filename))
        context = {"o": record.with_context()}
        context.update(self._get_aeroo_extra_functions())
        return template.render(context)

    def _find_aeroo_report_attachment(self, record, output_format):
        if self.attachment_use:
            filename = self.get_aeroo_filename(record, output_format)
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_id", "=", record.id),
                    ("res_model", "=", record._name),
                    ("name", "=", filename),
                ],
                limit=1,
            )
            if attachment:
                return base64.decodebytes(attachment.datas)
        return None

    def _create_aeroo_attachment(self, record, file_data, output_format):
        filename = self.get_aeroo_filename(record, output_format)
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": base64.encodebytes(file_data),
                "res_model": record._name,
                "res_id": record.id,
            }
        )

    def _convert_aeroo_report(self, output, output_format):
        in_format = self.aeroo_in_format
        temp_file = generate_temporary_file(in_format, output)
        filedir, filename = os.path.split(temp_file.name)

        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            output_format,
            "--outdir",
            filedir,
            temp_file.name,
        ]
        timeout = self._get_aeroo_libreoffice_timeout()

        try:
            subprocess.call(cmd, timeout=timeout)
        except Exception as exc:
            os.remove(temp_file.name)
            raise ValidationError(
                _(
                    "Could not generate the report %(report)s using the format %(output_format)s. %(error)s"
                ) % {
                    "report": self.name,
                    "output_format": output_format,
                    "error": exc,
                }
            )

        output_file = temp_file.name[:-3] + output_format
        with open(output_file, "rb") as f:
            output = f.read()

        os.remove(temp_file.name)
        os.remove(output_file)
        return output

    def _render_aeroo_multi(self, doc_ids, data, output_format):
        if output_format != "pdf":
            raise ValidationError(
                _("Aeroo Reports do not support generating non-pdf reports in batch. You must select one record at a time.")
            )

        input_files = []
        for record_id in doc_ids:
            report = self._render_aeroo([record_id], data)
            temp_file = generate_temporary_file(output_format, report[0])
            input_files.append(temp_file.name)

        try:
            return self._merge_aeroo_pdf(input_files), "pdf"
        except Exception as exc:
            traceback.print_exc()
            raise ValidationError(
                _("Could not merge the pdf outputs of the report %(report)s.\n\n%(error)s") % {
                    "report": self.name,
                    "error": exc,
                }
            )
        finally:
            for file in input_files:
                os.remove(file)

    def _merge_aeroo_pdf(self, input_files):
        output_file = generate_temporary_file("pdf")
        cmd = ["pdfunite", *input_files, output_file.name]
        timeout = self._get_aeroo_libreoffice_timeout()

        try:
            subprocess.call(cmd, timeout=timeout)
        except BaseException:
            os.remove(output_file.name)
            raise

        with open(output_file.name, "rb") as f:
            output = f.read()

        os.remove(output_file.name)
        return output

    def _should_add_test_watermark(self):
        param_value = self.env["ir.config_parameter"].sudo().get_param("AEROO_REPORTS_TESTS", "False")
        return param_value.lower() == "true"

    def _add_test_watermark_to_pdf(self, pdf_data):
        if not PYPDF_AVAILABLE:
            _logger.warning("pypdf and reportlab not available, cannot add watermark")
            return pdf_data

        try:
            watermark_buffer = BytesIO()
            watermark_pdf = canvas.Canvas(watermark_buffer, pagesize=letter)

            watermark_pdf.setFillColor(red, alpha=0.3)
            watermark_pdf.setFont("Helvetica-Bold", 72)

            page_width, page_height = letter
            text_width = watermark_pdf.stringWidth("TEST", "Helvetica-Bold", 72)
            x = (page_width - text_width) / 2
            y = page_height / 2

            watermark_pdf.saveState()
            watermark_pdf.translate(x, y)
            watermark_pdf.rotate(45)
            watermark_pdf.drawString(-text_width / 2, 0, "TEST")
            watermark_pdf.restoreState()
            watermark_pdf.save()
            watermark_buffer.seek(0)

            # Updated for pypdf (Odoo 17/18 compatibility)
            original_pdf = OdooPdfFileReader(BytesIO(pdf_data))
            watermark_pdf_reader = OdooPdfFileReader(watermark_buffer)
            watermark_page = watermark_pdf_reader.pages[0]

            output_pdf = OdooPdfFileWriter()

            for page in original_pdf.pages:
                page.merge_page(watermark_page) # Uses snake_case merge_page
                output_pdf.add_page(page) # Uses snake_case add_page

            output_buffer = BytesIO()
            output_pdf.write(output_buffer)
            output_buffer.seek(0)

            return output_buffer.read()

        except Exception as e:
            _logger.error("Error adding watermark: %s", str(e))
            return pdf_data


class IrActionsReportWithSudo(models.Model):
    _inherit = "ir.actions.report"

    def _get_aeroo_template(self, record):
        self = self.sudo()
        record = record.sudo()
        return super()._get_aeroo_template(record)


class AerooReportsGeneratedFromListViews(models.Model):
    _inherit = "ir.actions.report"

    def _render_aeroo(self, doc_ids, data=None, force_output_format=None):
        data = data or {}
        if self.multi:
            return self._render_aeroo_from_list_of_records(doc_ids, data, force_output_format)
        else:
            return super()._render_aeroo(doc_ids=doc_ids, data=data, force_output_format=force_output_format)

    def _render_aeroo_from_list_of_records(self, doc_ids, data=None, force_output_format=None):
        if len(doc_ids) == 0:
            raise ValidationError(
                _("At least one record must be selected to generate the report {report}.").format(report=self.name)
            )

        output_format = force_output_format or self.aeroo_out_format_id.code
        data = data or {}
        records = self.env[self.model].browse(doc_ids)

        template = self._get_aeroo_template(records[0])
        report_context = self._get_aeroo_context(records[0])
        report_data = dict(
            data,
            objects=records,
            company=self._get_aeroo_company(records[0]),
            **report_context
        )

        output = self.with_context(**report_context)._render_aeroo_content(template, report_data, output_format)

        if output_format == "pdf" and self._should_add_test_watermark():
            output = self._add_test_watermark_to_pdf(output)

        return output, output_format

    def _onchange_is_aeroo_list_report_set_multi(self):
        if self.is_aeroo_list_report:
            self.multi = True


class AerooReportsWithAttachmentFilenamePerLang(models.Model):
    _inherit = "ir.actions.report"

    aeroo_filename_per_lang = fields.Boolean("Different Filename per Language", prefetch=False)
    aeroo_filename_line_ids = fields.One2many("aeroo.filename.line", "report_id", "Filenames by Language")

    def get_aeroo_filename(self, record, output_format):
        if not self.aeroo_filename_per_lang:
            return super().get_aeroo_filename(record, output_format)

        mako_filename = self._get_aeroo_filename_from_lang(record)
        rendered_filename = self._eval_aeroo_attachment_filename(mako_filename, record)
        return ".".join((rendered_filename, output_format))

    def _get_aeroo_filename_from_lang(self, record):
        lang = self._get_aeroo_lang(record)

        def line_matches_lang(line):
            return line.lang_id.code == lang

        line = next((line for line in self.aeroo_filename_line_ids if line_matches_lang(line)), None)

        if line is None:
            raise ValidationError(
                _("Could not render the attachment filename for the report {report} in the language {lang}.").format(
                    report=self.name, lang=lang
                )
            )
        return line.filename


def generate_temporary_file(format, data=None):
    temp_file = NamedTemporaryFile(suffix=".%s" % format, delete=False)
    temp_file.close()
    if data is not None:
        with open(temp_file.name, "wb") as f:
            f.write(data)
    return temp_file
