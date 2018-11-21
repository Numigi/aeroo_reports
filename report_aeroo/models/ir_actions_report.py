# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import imp
import logging
import os
import sys
import traceback
from aeroolib.plugins.opendocument import Template, OOSerializer
from datetime import datetime
from functools import wraps
from io import BytesIO
from genshi.template.eval import StrictLookup
from genshi.template.base import Context as GenshiContext
from tempfile import NamedTemporaryFile

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.tools import file_open, safe_eval
from odoo.addons.mail.models.mail_template import mako_template_env

from ..subprocess import run_subprocess
from ..extra_functions import aeroo_function_registry


class IrActionsReport(models.Model):

    _inherit = 'ir.actions.report'

    @api.model
    def _get_default_aeroo_out_format(self):
        return self.env['aeroo.mimetype'].search(
            [('code', '=', 'odt')], limit=1)

    report_type = fields.Selection(selection_add=[('aeroo', 'Aeroo Reports')])
    aeroo_in_format = fields.Selection(
        selection='_get_in_aeroo_mimetypes', string='Template Mime-type',
        default='odt')
    aeroo_out_format_id = fields.Many2one(
        'aeroo.mimetype', 'Output Mime-type',
        default=_get_default_aeroo_out_format)
    aeroo_template_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
        ('lines', 'Different Template per Language / Company'),
    ], string='Template source', default='database')
    aeroo_template_data = fields.Binary()
    aeroo_template_path = fields.Char()
    aeroo_template_line_ids = fields.One2many(
        'aeroo.template.line', 'report_id', 'Templates by Language')
    aeroo_lang_eval = fields.Char(
        'Language Evaluation',
        help="Python expression used to determine the language "
        "of the record being printed in the report.",
        default="o.partner_id.lang")
    aeroo_tz_eval = fields.Char(
        'Timezone Evaluation',
        help="Python expression used to determine the timezone "
        "used for formatting dates and timestamps.",
        default="user.tz")
    aeroo_company_eval = fields.Char(
        'Company Evaluation',
        help="Python expression used to determine the company "
        "of the record being printed in the report.",
        default="o.company_id")

    @api.model
    def _get_in_aeroo_mimetypes(self):
        mime_obj = self.env['aeroo.mimetype']
        domain = self.env.context.get('allformats') and [] or [
            ('filter_name', '=', False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]

    def _get_aeroo_template(self, record):
        """Get an aeroo template for the given record.

        There are 3 ways to store the aeroo template:

        1- a single template stored in the file system
        2- a single template stored in the database
        3- one template per combination (lang, company) stored in the database

        :param record: the record for which to generate the report
        :return: the template's binary file
        """
        if self.aeroo_template_source == 'file':
            return self._get_aeroo_template_from_file()

        if self.aeroo_template_source == 'database':
            return self._get_aeroo_template_from_database()

        return self._get_aeroo_template_from_lines(record)

    def _get_aeroo_template_from_file(self):
        """Get an aeroo template from a file."""
        with file_open(self.aeroo_template_path, 'rb') as file:
            return file.read()

    def _get_aeroo_template_from_database(self):
        """Get an aeroo template stored in the database."""
        return base64.b64decode(self.aeroo_template_data)

    def _get_aeroo_template_from_lines(self, record):
        """Get an aeroo template from the template lines.

        :param record: the record for which to generate the report
        :return: the template's binary file
        """
        template_line = self._get_aeroo_template_line(record)
        return template_line.get_aeroo_template(record)

    def _get_aeroo_template_line(self, record):
        """Get an aeroo template line matching the given record.

        An aeroo report can have different templates per company
        and per language.

        :param record: the record for which to generate the report
        :return: the template's binary file
        """
        lang = self._get_aeroo_lang(record)
        company = self._get_aeroo_company(record)

        line_matches_lang = (lambda l: not l.lang_id or l.lang_id.code == lang)
        line_matches_company = (lambda l: not l.company_id or l.company_id == company)

        line = next((
            l for l in self.aeroo_template_line_ids
            if line_matches_lang(l) and line_matches_company(l)
        ), None)

        if line is None:
            raise ValidationError(
                _('Could not render report {report} for the '
                  'company {company} in the language {lang}.').format(
                    report=self.name,
                    company=company.name,
                    lang=lang,
                ))

        return line

    def _get_aeroo_lang(self, record):
        """Get the lang to use in the report for a given record.

        :rtype: res.company
        """
        lang = (
            safe_eval(self.aeroo_lang_eval, {'o': record, 'user': self.env.user})
            if self.aeroo_lang_eval else None
        )
        return lang or 'en_US'

    def _get_aeroo_timezone(self, record):
        """Get the timezone to use in the report for a given record.

        :rtype: res.company
        """
        return (
            safe_eval(self.aeroo_tz_eval, {'o': record, 'user': self.env.user})
            if self.aeroo_tz_eval else None
        )

    def _get_aeroo_company(self, record):
        """Get the company to use in the report for a given record.

        The company is used if the template of the report is different
        per company.

        :rtype: res.company
        """
        return (
            safe_eval(self.aeroo_company_eval, {'o': record, 'user': self.env.user})
            if self.aeroo_company_eval else self.env.user.company_id
        )

    def _get_aeroo_libreoffice_timeout(self):
        """Get the timeout of the Libreoffice process in seconds.

        :rtype: float
        """
        libreoffice_timeout = self._get_aeroo_config_parameter('libreoffice_timeout')
        return float(libreoffice_timeout)

    def render_aeroo(self, doc_ids, data=None, force_output_format=None):
        """Render an aeroo report.

        If doc_ids contains more than one record id, the report will
        be generated individually for each record. Then, all pdf outputs
        will be merged together.

        :param list doc_ids: the ids of the records.
        :param dict data: the data to send to the report as context.
        :param str force_output_format: whether to force a given output report format.
            If not given the standard output format defined on the report is used.
        """
        output_format = force_output_format or self.aeroo_out_format_id.code

        if data is None:
            data = {}

        if len(doc_ids) > 1:
            return self._render_aeroo_multi(doc_ids, data, output_format)

        record = self.env[self.model].browse(doc_ids[0])

        report_lang = self._get_aeroo_lang(record)
        report_timezone = self._get_aeroo_timezone(record)
        self = self.with_context(lang=report_lang, tz=report_timezone)

        # Check if an attachment already exists
        attachment_output = self._find_aeroo_report_attachment(record, output_format)
        if attachment_output:
            return attachment_output, output_format

        template = self._get_aeroo_template(record)

        # Render the report
        current_report_data = dict(
            data, o=record.with_context(lang=report_lang, tz=report_timezone))
        output = self._render_aeroo(template, current_report_data, output_format)

        # Generate the attachment
        if self.attachment_use:
            self._create_aeroo_attachment(record, output, output_format)

        return output, output_format

    def _render_aeroo(self, template, data, output_format):
        """Generate the aeroo report binary from the template.

        :param template: the Libreoffice template to use
        :param data: the data used for rendering the report
        :param output_format: the output format
        :return: the report's binary data
        """
        # The first given record is
        template_io = BytesIO()
        template_io.write(template)
        serializer = OOSerializer(template_io)

        report_context = GenshiContext(**data)
        report_context.update(self._get_aeroo_extra_functions())

        output = Template(source=template_io, serializer=serializer)\
            .generate(report_context).render().getvalue()

        if self.aeroo_in_format != output_format:
            output = self._convert_aeroo_report(output, output_format)

        return output

    def _get_aeroo_extra_functions(self):
        """Get a dictionnary of extra functions available inside an aeroo template."""
        return {
            k: self._wrap_aeroo_function(v)
            for k, v in aeroo_function_registry.get_functions().items()
        }

    def _wrap_aeroo_function(self, func):
        """Wrap an extra function for the current aeroo report.

        The wrapping automatically adds the report as first parameter of the function.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    def get_aeroo_filename(self, record, output_format):
        """Get the attachement filename for the generated report.

        :param record: the record for which to generate the report
        :return: the filename
        """
        if self.attachment:
            filename = self._eval_aeroo_attachment_filename(self.attachment, record)
            return '.'.join((filename, output_format))
        else:
            return '.'.join((self.name, output_format))

    def _eval_aeroo_attachment_filename(self, filename, record):
        """Evaluate the given attachment filename for the given record.

        :param filename: the filename mako template
        :param record: the record for which to evaluate the filename
        :return: the rendered attachment filename
        """
        template = mako_template_env.from_string(tools.ustr(filename))
        context = {'o': record.with_context()}
        context.update(self._get_aeroo_extra_functions())
        return template.render(context)

    def _find_aeroo_report_attachment(self, record, output_format):
        """Find an attachment of the Aeroo report on the given record.

        If the report is stored as an attachment, it will be generated
        only once for each record.

        If the report as already been generated, this method returns
        the binary data stored in the attachment. Otherwise, it returns None.

        :param record: the record for which to find the attachement
        :return: the report's binary data or None
        """
        if self.attachment_use:
            filename = self.get_aeroo_filename(record, output_format)
            attachment = self.env['ir.attachment'].search([
                ('res_id', '=', record.id),
                ('res_model', '=', record._name),
                ('datas_fname', '=', filename),
            ], limit=1)
            if attachment:
                return base64.decodestring(attachment.datas)
        return None

    def _create_aeroo_attachment(self, record, file_data, output_format):
        """Save the generated aeroo report as attachment.

        :param record: the record used to generate the report
        :param file_data: the generated report's binary file
        :return: the generated attachment
        """
        filename = self.get_aeroo_filename(record, output_format)
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodestring(file_data),
            'datas_fname': filename,
            'res_model': record._name,
            'res_id': record.id,
        })

    def _convert_aeroo_report(self, output, output_format):
        """Convert a generated aeroo report to the output format.

        :param string output: the aeroo data to convert.
        :return: the content of the generated report
        :rtype: bytes
        """
        in_format = self.aeroo_in_format

        temp_file = generate_temporary_file(in_format, output)
        filedir, filename = os.path.split(temp_file.name)

        libreoffice_location = self._get_aeroo_config_parameter('libreoffice_location')

        cmd = libreoffice_location.split(' ') + [
            "--headless",
            "--convert-to", output_format,
            "--outdir", filedir, temp_file.name
        ]

        timeout = self._get_aeroo_libreoffice_timeout()

        try:
            run_subprocess(cmd, timeout)
        except Exception as exc:
            os.remove(temp_file.name)
            raise ValidationError(
                _('Could not generate the report %(report)s '
                  'using the format %(output_format)s. '
                  '%(error)s') % {
                    'report': self.name,
                    'output_format': output_format,
                    'error': exc,
                })

        output_file = temp_file.name[:-3] + output_format
        with open(output_file, 'rb') as f:
            output = f.read()

        os.remove(temp_file.name)
        os.remove(output_file)

        return output

    def _render_aeroo_multi(self, doc_ids, data, output_format):
        """Render an aeroo report for multiple records at the same time.

        All reports are generated individually and merged together using pdftk.
        Only reports in pdf formats are supported.

        :param list doc_ids: the ids of the records.
        :param dict data: the data to send to the report as context.
        :return: the content of the merged pdf reports
        :rtype: bytes
        """
        if output_format != 'pdf':
            raise ValidationError(
                _('Aeroo Reports do not support generating non-pdf '
                  'reports in batch. You must select one record at a time.'))

        input_files = []

        for record_id in doc_ids:
            report = self.render_aeroo([record_id], data)
            temp_file = generate_temporary_file(output_format, report[0])
            input_files.append(temp_file.name)

        try:
            return self._merge_aeroo_pdf(input_files), 'pdf'
        except Exception as exc:
            traceback.print_exc()
            raise ValidationError(
                _('Could not merge the pdf outputs of the report %(report)s.'
                  '\n\n%(error)s') % {
                    'report': self.name,
                    'error': exc,
                })
        finally:
            for file in input_files:
                os.remove(file)

    def _merge_aeroo_pdf(self, input_files):
        """Merge the given pdf files together using pdftk.

        :param list input_files: the paths to the pdf files to merge.
        :return: the content of the merged pdf reports
        :rtype: bytes
        """
        pdftk_location = self._get_aeroo_config_parameter('pdftk_location')

        output_file = generate_temporary_file('pdf')

        cmd = [pdftk_location]
        cmd += input_files
        cmd += ['cat', 'output', output_file.name]

        timeout = self._get_aeroo_libreoffice_timeout()

        try:
            run_subprocess(cmd, timeout)
        except:
            traceback.print_exc()
            os.remove(output_file.name)
            raise

        with open(output_file.name, 'rb') as f:
            output = f.read()

        os.remove(output_file.name)

        return output

    def _get_aeroo_config_parameter(self, parameter_name):
        """Get a configuration parameter related to aeroo reports.

        The sudo() is required because since Odoo version 11.0, all config parameters
        are restricted in read access.

        :param parameter_name: the name of the configuration parameter.
        """
        param = (
            self.env['ir.config_parameter'].sudo()
            .get_param('.'.join(('report_aeroo', parameter_name)))
        )

        if not param:
            raise ValidationError(
                _('Aeroo reports are wrongly configured. '
                  'The global parameter report_aeroo.{parameter_name} '
                  'must be defined.').format(parameter_name=parameter_name))

        return param


class IrActionsReportWithSudo(models.Model):

    _inherit = 'ir.actions.report'

    def _get_aeroo_template(self, record):
        """Prevent access rights from impacting the aeroo template selection."""
        self = self.sudo()
        record = record.sudo()
        return super()._get_aeroo_template(record)


class AerooReportsGeneratedFromListViews(models.Model):
    """Enable rendering aeroo reports from a list view.

    Instead of generating one report per record and merging the rendered pdf,
    a single report is generated.

    A variable `objects` is passed to the renderer instead of a variable `o`.
    This new variable contains the recordset for which to render the report.
    """

    _inherit = 'ir.actions.report'

    def render_aeroo(self, doc_ids, data=None, force_output_format=None):
        if self.multi:
            return self._render_aeroo_from_list_of_records(doc_ids, data, force_output_format)
        else:
            return super().render_aeroo(doc_ids, data, force_output_format)

    def _render_aeroo_from_list_of_records(self, doc_ids, data=None, force_output_format=None):
        """Render an aeroo report for a list of record ids.

        :param list doc_ids: the ids of the records.
        :param dict data: the data to send to the report as context.
        :param str force_output_format: whether to force a given output report format.
            If not given the standard output format defined on the report is used.
        """
        if len(doc_ids) == 0:
            raise ValidationError(_(
                'At least one record must be selected to generate the report {report}.'
            ).format(report=self.name))

        output_format = force_output_format or self.aeroo_out_format_id.code

        if data is None:
            data = {}

        records = self.env[self.model].browse(doc_ids)

        template = self._get_aeroo_template(records[0])
        report_lang = self._get_aeroo_lang(records[0])
        report_timezone = self._get_aeroo_timezone(records[0])
        report_data = dict(data, objects=records)

        # Render the report
        output = self.with_context(lang=report_lang, tz=report_timezone)._render_aeroo(
            template, report_data, output_format)

        return output, output_format

    def _onchange_is_aeroo_list_report_set_multi(self):
        if self.is_aeroo_list_report:
            self.multi = True


class AerooReportsWithAttachmentFilenamePerLang(models.Model):
    """Enable one attachment filename per language."""

    _inherit = 'ir.actions.report'

    aeroo_filename_per_lang = fields.Boolean('Different Filename per Language')
    aeroo_filename_line_ids = fields.One2many(
        'aeroo.filename.line', 'report_id', 'Filenames by Language')

    def get_aeroo_filename(self, record, output_format):
        """Get the attachement filename for the generated report.

        :param record: the record for which to generate the freport
        :return: the filename
        """
        if not self.aeroo_filename_per_lang:
            return super().get_aeroo_filename(record, output_format)

        mako_filename = self._get_aeroo_filename_from_lang(record)
        rendered_filename = self._eval_aeroo_attachment_filename(mako_filename, record)
        return '.'.join((rendered_filename, output_format))

    def _get_aeroo_filename_from_lang(self, record):
        """Get the attachment filename for the record based on the rendering language.

        :param record: the record for which to generate the file name
        :return: the filename mako template
        """
        lang = self._get_aeroo_lang(record)
        line_matches_lang = (lambda l: l.lang_id.code == lang)

        line = next((l for l in self.aeroo_filename_line_ids if line_matches_lang(l)), None)

        if line is None:
            raise ValidationError(
                _("Could not render the attachment filename for the report "
                  "{report} in the language {lang}.").format(report=self.name, lang=lang))

        return line.filename


def generate_temporary_file(format, data=None):
    """Generate a temporary file containing the given data.

    :param string format: the extension of the file to create
    :param bytes data: the data to write in the file
    """
    temp_file = NamedTemporaryFile(suffix='.%s' % format, delete=False)
    temp_file.close()
    if data is not None:
        with open(temp_file.name, 'wb') as f:
            f.write(data)
    return temp_file
