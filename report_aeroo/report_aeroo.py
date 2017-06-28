# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import logging
import os

import subprocess
import time

from aeroolib.plugins.opendocument import Template, OOSerializer
from cStringIO import StringIO
from genshi.template.eval import StrictLookup

from odoo import api, models
from odoo.api import Environment
from odoo.report.report_sxw import report_sxw
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

from tempfile import NamedTemporaryFile

from .extra_functions import ExtraFunctions

logger = logging.getLogger('report_aeroo')


mime_dict = {
    'oo-odt': 'odt',
    'oo-ods': 'ods',
    'oo-pdf': 'pdf',
    'oo-doc': 'doc',
    'oo-xls': 'xls',
    'oo-csv': 'csv',
}


class DynamicLookup(StrictLookup):
    """
    Dynamically changes language in a context
    according to Parser's current language
    """

    @classmethod
    def lookup_name(cls, data, name):
        orig = super(DynamicLookup, cls).lookup_name(data, name)
        if isinstance(orig, models.Model):
            new_lang = data.get('getLang')()
            if orig.env.context.get('lang') != new_lang:
                orig = orig.with_context(lang=new_lang)
        return orig


class AerooReport(report_sxw):

    def create_aeroo_report(
            self, cr, uid, ids, data, report_xml, context):
        """ Return an aeroo report generated with aeroolib
        """
        context = context.copy()
        assert report_xml.out_format.code in (
            'oo-odt', 'oo-ods', 'oo-doc', 'oo-xls', 'oo-csv', 'oo-pdf',
        )
        assert report_xml.in_format in ('oo-odt', 'oo-ods')

        output_format = report_xml.out_format.code[3:]
        input_format = report_xml.in_format[3:]

        oo_parser = self.parser(cr, uid, self.name2, context=context)

        env = Environment(cr, uid, context)
        objects = env[self.table].browse(ids)

        oo_parser.localcontext.update(context)
        oo_parser.set_context(objects, data, ids, report_xml.report_type)

        oo_parser.localcontext['data'] = data
        oo_parser.localcontext['user_lang'] = context.get('lang', False)
        oo_parser.localcontext['o'] = objects[0]

        xfunc = ExtraFunctions(cr, uid, report_xml.id, oo_parser.localcontext)
        oo_parser.localcontext.update(xfunc.functions)

        template = report_xml.get_aeroo_report_template(objects[0])

        template_io = StringIO()
        template_io.write(template)
        serializer = OOSerializer(template_io)
        basic = Template(
            source=template_io, serializer=serializer, lookup=DynamicLookup)

        data = basic.generate(**oo_parser.localcontext).render().getvalue()

        if input_format != output_format:
            temp_file = NamedTemporaryFile(
                suffix='.%s' % input_format, delete=False)
            temp_file.close()

            with open(temp_file.name, 'w') as f:
                f.write(data)

            filedir, filename = os.path.split(temp_file.name)

            libreoffice_location = (
                report_xml.env['ir.config_parameter'].get_param(
                    'report_aeroo.libreoffice_location')
            )

            if not libreoffice_location:
                raise ValidationError(
                    _('Aeroo reports are wrongly configured. '
                      'The global parameter report_aeroo.libreoffice_location '
                      'must be defined.'))

            proc = subprocess.Popen([
                libreoffice_location, "--headless",
                "--convert-to", output_format,
                "--outdir", filedir, temp_file.name
            ])

            timetaken = 0

            libreoffice_timeout = (
                report_xml.env['ir.config_parameter'].get_param(
                    'report_aeroo.libreoffice_timeout')
            )

            if not libreoffice_timeout:
                raise ValidationError(
                    _('Aeroo reports are wrongly configured. '
                      'The global parameter report_aeroo.libreoffice_timeout '
                      'must be defined.'))

            libreoffice_timeout = float(libreoffice_timeout)

            while True:
                status = proc.poll()
                if status is 0:
                    break

                elif status is not None:
                    os.remove(temp_file.name)
                    raise ValidationError(
                        _('Could not convert the report %(report)s '
                          'from %(input_format)s to %(output_format)s.') % {
                            'report': report_xml.name,
                            'input_format': input_format,
                            'output_format': output_format,
                        })

                timetaken += 0.1
                time.sleep(0.1)

                if timetaken > libreoffice_timeout:
                    proc.kill()
                    os.remove(temp_file.name)
                    raise ValidationError(
                        _('Could not convert the report %(report)s '
                          'from %(input_format)s to %(output_format)s. '
                          'Timeout Exceeded.') % {
                            'report': report_xml.name,
                            'input_format': input_format,
                            'output_format': output_format,
                        })

            output_filename = temp_file.name[:-3] + output_format

            with open(output_filename, 'r') as f:
                data = f.read()

            os.remove(temp_file.name)
            os.remove(output_filename)

        return data, output_format

    def create(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        else:
            context = dict(context)

        if len(ids) > 1:
            raise ValidationError(
                _('Aeroo Reports do not support generating reports in batch. '
                  'You must select one record at a time.'))

        env = api.Environment(cr, uid, context)

        if 'tz' not in context:
            context['tz'] = env.user.tz

        data.setdefault('model', context.get('active_model', False))

        name = self.name.startswith('report.') and self.name[7:] or self.name

        report_xml = env['ir.actions.report.xml'].search(
            [('report_name', '=', name)])

        report_type = report_xml.report_type
        assert report_type == 'aeroo'

        if report_xml.attachment_use:
            obj = env[report_xml.model].browse(ids[0])
            output_format = report_xml.out_format.code[3:]

            if report_xml.attachment:
                filename = "%s.%s" % (
                    safe_eval(report_xml.attachment, {
                        'object': obj,
                        'time': time,
                    }), output_format)

            else:
                filename = "%s.%s" % (report_xml.name, output_format)

            attachment = env['ir.attachment'].search([
                ('res_id', '=', obj.id),
                ('res_model', '=', obj._name),
                ('datas_fname', '=', filename),
            ], limit=1)

            if attachment:
                return base64.decodestring(attachment.datas), output_format

        res = self.create_aeroo_report(
            cr, uid, ids, data, report_xml, context=context)

        if report_xml.attachment_use:
            env['ir.attachment'].create({
                'name': filename,
                'datas': base64.encodestring(res[0]),
                'datas_fname': filename,
                'res_model': obj._name,
                'res_id': obj.id,
            })

        return res
