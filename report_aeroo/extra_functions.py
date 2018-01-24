# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import logging
import time
from datetime import datetime
from io import StringIO
from PIL import Image

from odoo import models
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)

from .barcode import barcode

logger = logging.getLogger(__name__)


class ExtraFunctions(object):
    """Extra functions that can be called from templates."""

    def __init__(self, report):
        self.env = report.env
        self.report = report
        self.context = report._context
        self.functions = {
            'asimage': self._asimage,
            'barcode': barcode.make_barcode,
            'time': time,
            'report': self.report,
            'format_date': self._format_date,
            'format_datetime': self._format_datetime,
        }

    def _format_date(self, value, date_format):
        if not value:
            return ''
        date = datetime.strptime(value, DEFAULT_SERVER_DATE_FORMAT)
        return date.strftime(date_format)

    def _format_datetime(self, value, datetime_format):
        if not value:
            return ''
        date = datetime.strptime(value, DEFAULT_SERVER_DATETIME_FORMAT)
        return date.strftime(datetime_format)

    def _asimage(
        self, field_value, rotate=None, size_x=None, size_y=None,
        uom='px', hold_ratio=False
    ):
        def size_by_uom(val, uom, dpi):
            if uom == 'px':
                result = str(val / dpi) + 'in'
            elif uom == 'cm':
                result = str(val / 2.54) + 'in'
            elif uom == 'in':
                result = str(val) + 'in'
            return result
        ##############################################
        if not field_value:
            return StringIO.StringIO(), 'image/png'
        field_value = base64.decodestring(field_value)
        tf = StringIO.StringIO(field_value)
        tf.seek(0)
        im = Image.open(tf)
        format = im.format.lower()
        dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))
        try:
            if rotate is not None:
                im = im.rotate(int(rotate))
                tf.seek(0)
                im.save(tf, format)
        except Exception:
            logger.error("Error in '_asimage' method", exc_info=True)

        if hold_ratio:
            img_ratio = im.size[0] / float(im.size[1])  # width / height
            if size_x and not size_y:
                size_y = size_x / img_ratio
            elif not size_x and size_y:
                size_x = size_y * img_ratio
            elif size_x and size_y:
                size_y2 = size_x / img_ratio
                size_x2 = size_y * img_ratio
                if size_y2 > size_y:
                    size_x = size_x2
                elif size_x2 > size_x:
                    size_y = size_y2

        size_x = size_x and size_by_uom(
            size_x,
            uom,
            dpi_x) or str(
            im.size[0] / dpi_x) + 'in'
        size_y = size_y and size_by_uom(
            size_y,
            uom,
            dpi_y) or str(
            im.size[1] / dpi_y) + 'in'
        return tf, 'image/%s' % format, size_x, size_y
