# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import imp
import logging
import os
import sys
import time
import psutil
import signal
import subprocess
import traceback

from aeroolib.plugins.opendocument import Template, OOSerializer
from io import BytesIO
from genshi.template.eval import StrictLookup
from genshi.template.base import Context as GenshiContext
from tempfile import NamedTemporaryFile

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.tools import file_open
from openerp.tools.safe_eval import safe_eval

from ..extra_functions import ExtraFunctions


class IrActionsReport(models.Model):

    _inherit = 'ir.actions.report'

    @api.model
    def _get_default_aeroo_out_format(self):
        return self.env['aeroo.mimetype'].search(
            [('code', '=', 'odt')], limit=1)

    report_type = fields.Selection(selection_add=[('aeroo', 'Aeroo Reports')])
    aeroo_in_format = fields.Selection(
        selection='_get_in_aeroo_mimetypes', string='Template Mime-type',
        default='oo-odt')
    aeroo_out_format_id = fields.Many2one(
        'aeroo.mimetype', 'Output Mime-type',
        default=_get_default_aeroo_out_format)
    aeroo_template_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
        ('lang', 'Different Template per Language'),
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
        if self.aeroo_template_source == 'lang':
            return self._get_aeroo_template_from_lines(record)
        elif self.aeroo_template_source == 'database':
            if not self.aeroo_template:
                raise ValidationError(
                    _('No template found for report %s' % self.report_name))
            return base64.b64decode(self.aeroo_template_data)
        else:
            return self._get_aeroo_template_from_file()

    def _get_aeroo_template_from_lines(self, record):
        lang = self._get_aeroo_lang(record)
        company = self._get_aeroo_company(record)
        line = next((
            l for l in self.aeroo_template_line_ids
            if l.lang_id.code == lang and
            (not l.company_id or l.company_id == company)
        ), None)

        if line is None:
            raise ValidationError(
                _('Could not render report %(report)s for the '
                  'company %(company)s in lang %(lang)s.') % {
                    'report': self.name,
                    'company': company.name,
                    'lang': lang,
                })

        return line.get_aeroo_template(record)

    def _get_aeroo_template_from_file(self):
        """Get an aeroo template from a file."""
        with file_open(self.aeroo_template_path, 'rb') as file:
            return file.read()

    def _get_aeroo_lang(self, record):
        """Get the lang to use in the report for a given record.

        :rtype: res.company
        """
        lang = safe_eval(self.aeroo_lang_eval, {'o': record})
        return lang or 'en_US'

    def _get_aeroo_company(self, record):
        """Get the company to use in the report for a given record.

        The company is used if the template of the report is different
        per company.

        :rtype: res.company
        """
        company = safe_eval(
            self.aeroo_company_eval, {'o': record, 'user': self.env.user})
        return company or 'en_US'

    def _get_aeroo_libreoffice_timeout(self):
        """Get the timeout of the Libreoffice process in seconds.

        :rtype: float
        """
        libreoffice_timeout = self.env['ir.config_parameter'].get_param(
            'report_aeroo.libreoffice_timeout')
        if not libreoffice_timeout:
            raise ValidationError(
                _('Aeroo reports are wrongly configured. '
                  'The global parameter report_aeroo.libreoffice_timeout '
                  'must be defined.'))

        return float(libreoffice_timeout)

    def render_aeroo(self, doc_ids, data=None):
        """Render an aeroo report.

        If doc_ids contains more than one record id, the report will
        be generated individually for each record. Then, all pdf outputs
        will be merged together.

        :param list doc_ids: the ids of the records.
        :param dict data: the data to send to the report as context.
        """
        if data is None:
            data = {}

        if len(doc_ids) > 1:
            return self._render_aeroo_multi(doc_ids, data)

        out_format = self.aeroo_out_format_id.code
        record = self.env[self.model].browse(doc_ids[0])

        # Check if an attachment already exists
        attachment_output = self._find_aeroo_report_attachment(record)
        if attachment_output:
            return attachment_output, out_format

        # Render the report
        output = self._render_aeroo(record, data)

        # Generate the attachment
        if self.attachment_use:
            self._create_aeroo_attachment(record, output)

        return output, out_format

    def _render_aeroo(self, record, data):
        """Generate the aeroo report binary from the template.

        :param record: the record for which to find the attachement
        :return: the report's binary data
        """
        self = self.with_context(lang=self._get_aeroo_lang(record))

        template_io = BytesIO()
        template_io.write(self._get_aeroo_template(record))

        serializer = OOSerializer(template_io)
        report_context = GenshiContext(**data)
        report_context.update(ExtraFunctions(self).functions)
        report_context['o'] = record
        output = Template(source=template_io, serializer=serializer)\
            .generate(report_context).render().getvalue()

        if self.aeroo_in_format != self.aeroo_out_format_id.code:
            output = self._convert_aeroo_report(output)

        return output

    def _get_aeroo_attachment_filename(self, record):
        """Get the attachement filename for the generated report.

        :param record: the record for which to find the attachement
        :return: the filename
        """
        output_format = self.aeroo_out_format_id.code
        if self.attachment:
            return "%s.%s" % (
                safe_eval(self.attachment, {'object': record, 'time': time}),
                output_format
            )
        else:
            return "%s.%s" % (self.name, output_format)

    def _find_aeroo_report_attachment(self, record):
        """Find an attachment of the Aeroo report on the given record.

        If the report is stored as an attachment, it will be generated
        only once for each record.

        If the report as already been generated, this method returns
        the binary data stored in the attachment. Otherwise, it returns None.

        :param record: the record for which to find the attachement
        :return: the report's binary data or None
        """
        if self.attachment_use:
            filename = self._get_aeroo_attachment_filename(record)
            attachment = self.env['ir.attachment'].search([
                ('res_id', '=', record.id),
                ('res_model', '=', record._name),
                ('datas_fname', '=', filename),
            ], limit=1)
            if attachment:
                return base64.decodestring(attachment.datas)
        return None

    def _create_aeroo_attachment(self, record, file_data):
        """Save the generated aeroo report as attachment.

        :param record: the record used to generate the report
        :param file_data: the generated report's binary file
        :return: the generated attachment
        """
        filename = self._get_aeroo_attachment_filename(record)
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodestring(file_data),
            'datas_fname': filename,
            'res_model': record._name,
            'res_id': record.id,
        })

    def _convert_aeroo_report(self, output):
        """Convert a generated aeroo report to the output format.

        :param string output: the aeroo data to convert.
        :return: the content of the generated report
        :rtype: bytes
        """
        in_format = self.aeroo_in_format
        out_format = self.aeroo_out_format_id.code

        temp_file = generate_temporary_file(in_format, output)
        filedir, filename = os.path.split(temp_file.name)

        libreoffice_location = (
            self.env['ir.config_parameter'].get_param(
                'report_aeroo.libreoffice_location'))

        if not libreoffice_location:
            raise ValidationError(
                _('Aeroo reports are wrongly configured. '
                  'The global parameter report_aeroo.libreoffice_location '
                  'must be defined.'))

        cmd = libreoffice_location.split(' ') + [
            "--headless",
            "--convert-to", out_format,
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
                    'output_format': out_format,
                    'error': exc,
                })

        output_file = temp_file.name[:-3] + out_format
        with open(output_file, 'rb') as f:
            output = f.read()

        os.remove(temp_file.name)
        os.remove(output_file)

        return output

    def _render_aeroo_multi(self, doc_ids, data):
        """Render an aeroo report for multiple records at the same time.

        All reports are generated individually and merged together using pdftk.
        Only reports in pdf formats are supported.

        :param list doc_ids: the ids of the records.
        :param dict data: the data to send to the report as context.
        :return: the content of the merged pdf reports
        :rtype: bytes
        """
        output_format = self.aeroo_out_format_id.code

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
            return self._merge_aeroo_pdf(input_files)
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
        pdftk_location = (
            self.env['ir.config_parameter'].get_param(
                'report_aeroo.pdftk_location')
        )

        if not pdftk_location:
            raise ValidationError(
                _('Aeroo reports are wrongly configured. '
                  'The global parameter report_aeroo.pdftk_location '
                  'must be defined.'))

        output_file = generate_temporary_file('pdf')

        cmd = [pdftk_location]
        cmd += input_files
        cmd += ['cat', 'output', output_file.name]

        print(cmd)

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


def run_subprocess(command, timeout):
    """Run a command in a subprocess with a given timeout.

    When the timeout expires, the process is terminated.

    :param string command: the command to execute
    :param float timeout: the timeout in seconds
    """
    process = subprocess.Popen(command)
    timetaken = 0

    while True:
        status = process.poll()
        if status is 0:
            break
        elif status is not None:
            raise ValidationError(
                _('Command %(command)s exited with status %(status)s.') % {
                    'command': command,
                    'status': status,
                })

        timetaken += 0.1
        time.sleep(0.1)

        if timetaken > timeout:
            terminate_process(process)
            raise ValidationError(
                _('Timeout (%(timeout)s seconds) expired while executing '
                  'the command: %(command)s') % {
                    'command': command,
                    'timeout': timeout,
                })


def terminate_process(self, process):
    """Attempt to terminate the process.

    Kill the process if it is still alive after 60 seconds.

    :param string process: the process pid to kill
    """
    process.terminate()
    for i in range(60):
        time.sleep(1)
        if process.poll() is not None:
            return

    parent = psutil.Process(process.pid)
    for child in parent.children(recursive=True):
        child.send_signal(signal.SIGKILL)
    parent.send_signal(signal.SIGKILL)
