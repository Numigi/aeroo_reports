# © 2008-2014 Alistek
# © 2016-2018 Savoir-faire Linux
# © 2018 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import babel.numbers
import babel.dates
import base64
import logging
import time
from babel.core import localedata
from datetime import datetime, date
from html2text import html2text
from io import BytesIO
from PIL import Image

from odoo import fields, _
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT,
)

from .barcode.code128 import get_code
from .barcode.code39 import create_c39
from .barcode.EANBarCode import EanBarCode

logger = logging.getLogger(__name__)


class AerooFunctionRegistry(object):
    """Class responsible for registering functions usable in aeroo templates."""

    def __init__(self):
        self._functions = {}

    def register(self, func_name, func):
        """Register a function inside the registry.

        :param func_name: the name of the function
        :param func: the function
        """
        if func_name in self._functions:
            raise RuntimeError(
                'A function named {func_name} is already registered in the Aeroo registry.'
                .format(func_name=func_name))
        self._functions[func_name] = func

    def get_functions(self):
        """Get all functions registered inside the registry."""
        return dict(self._functions)

aeroo_function_registry = AerooFunctionRegistry()


def aeroo_util(function_name):
    """Register a function as an Aeroo utility.

    :param function_name: the function name available to call the function in Aeroo
    """
    def decorator(func):
        aeroo_function_registry.register(function_name, func)
        return func

    return decorator


@aeroo_util('format_date')
def format_date(report, value: date, date_format: str):
    """Format a date field value into the given format.

    The language of the template is used to format the date.

    :param report: the aeroo report
    :param value: the value to format
    :param format: the format to use
    """
    if not value:
        return ''
    lang = report._context.get('lang') or 'en_US'
    return babel.dates.format_date(value, date_format, locale=lang)


@aeroo_util('today')
def format_date_today(report, date_format: str = None):
    today_in_timezone = fields.Date.context_today(report)
    return format_date(report, value=today_in_timezone, date_format=date_format)


@aeroo_util('format_datetime')
def format_datetime(report, value: datetime, datetime_format: str):
    """Format a datetime field value into the given format.

    The language of the template is used to format the datetime.

    :param report: the aeroo report
    :param value: the value to format
    :param format: the format to use
    """
    if not value:
        return ''
    lang = report._context.get('lang') or 'en_US'
    datetime_in_timezone = fields.Datetime.context_timestamp(report, value)
    return babel.dates.format_datetime(datetime_in_timezone, datetime_format, locale=lang)


@aeroo_util('now')
def format_datetime_now(report, datetime_format: str = None):
    timestamp = datetime.now()
    return format_datetime(report, value=timestamp, datetime_format=datetime_format)


@aeroo_util('format_decimal')
def format_decimal(report, amount: float, amount_format='#,##0.00'):
    """Format an amount in the language of the user.

    :param report: the aeroo report
    :param amount: the amount to format
    :param amount_format: an optional format to use
    """
    lang = report._context.get('lang') or 'en_US'
    return babel.numbers.format_decimal(amount, format=amount_format, locale=lang)


def get_locale_from_odoo_lang_and_country(lang: str, country: 'res.country'):
    locale = '{}_{}'.format(lang.split('_')[0], country.code)

    if not localedata.exists(locale):
        locale = lang

    return locale


@aeroo_util('format_currency')
def format_currency(report, amount: float, currency=None, amount_format=None, country=None):
    """Format an amount into the given currency in the language of the user.

    :param report: the aeroo report
    :param amount: the amount to format
    :param currency: the currency object to use (o.currency_id)
    :param amount_format: the format to use
    """
    context = report._context

    lang = context.get('lang') or 'en_US'
    country = country or context.get('country')
    locale = get_locale_from_odoo_lang_and_country(lang, country) if country else lang

    currency = currency or context.get('currency')
    if currency is None:
        raise ValidationError(_(
            "The function `format_currency` can not be evaluated without a currency. "
            "You must either define a currency in the field `Currency Evaluation` of the "
            "Aeroo report or call the function with a currency explicitely."
        ))

    return babel.numbers.format_currency(amount, currency.name, format=amount_format, locale=locale)


@aeroo_util('asimage')
def asimage(
    report,
    field_value: str,
    rotate: bool = None,
    size_x: int = None,
    size_y: int = None,
    uom: str = 'px',
    hold_ratio: bool = False
):
    def size_by_uom(val, uom, dpi):
        if uom == 'px':
            result = str(val / dpi) + 'in'
        elif uom == 'cm':
            result = str(val / 2.54) + 'in'
        elif uom == 'in':
            result = str(val) + 'in'
        return result

    if not field_value:
        return BytesIO(), 'image/png'

    field_value = base64.decodestring(field_value)
    tf = BytesIO(field_value)
    tf.seek(0)
    im = Image.open(tf)
    format = im.format.lower()
    dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))

    if rotate is not None:
        im = im.rotate(int(rotate))
        tf.seek(0)
        im.save(tf, format)

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

    size_x = size_x and size_by_uom(size_x, uom, dpi_x) or str(im.size[0] / dpi_x) + 'in'
    size_y = size_y and size_by_uom(size_y, uom, dpi_y) or str(im.size[1] / dpi_y) + 'in'
    return tf, 'image/%s' % format, size_x, size_y


@aeroo_util('barcode')
def barcode(
    report,
    code: str,
    code_type: str = 'ean13',
    rotate: bool = None,
    height: int = 50,
    xw: int = 1,
):
    if code:
        if code_type.lower() == 'ean13':
            bar = EanBarCode()
            im = bar.getImage(code, height)
        elif code_type.lower() == 'code128':
            im = get_code(code, xw, height)
        elif code_type.lower() == 'code39':
            im = create_c39(height, xw, code)
    else:
        return BytesIO(), 'image/png'

    tf = BytesIO()

    if rotate is not None:
        im = im.rotate(int(rotate))

    im.save(tf, 'png')
    size_x = str(im.size[0] / 96.0) + 'in'
    size_y = str(im.size[1] / 96.0) + 'in'
    return tf, 'image/png', size_x, size_y


@aeroo_util('html2text')
def format_html2text(report, html: str):
    """Convert the given HTML field value into text.

    The bodywidth=0 parameter prevents line breaks after 79 chars.

    :param html: the html string to format into raw text
    :return: the raw text
    """
    return html2text(html or '', bodywidth=0)
