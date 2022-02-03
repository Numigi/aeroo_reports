=============
Aeroo Reports
=============
This is the main module required for using Aeroo reports.

.. contents:: Table of Contents

Context
=======

Qweb
----
Odoo comes with a native reporting engine called ``Qweb``.
This engine is very good for some kind of reports.
When you need a web report with dynamic behavior, qweb is an appropriate choice.

However, qweb has weaknesses when rendering PDF documents, such as invoices, quotations and delivery slips.

First, Qweb templates are hard to customize and maintain.

Second, a Qweb report has a single template for all languages.
The translations are edited separately and injected in the template at rendering.
When making a change to a template, you must verify that it renders appropriately for all active translations.

The most major point is portability of reports between major versions of Odoo.
When migrating your system to an earlier version, you want to minimize the time required to port your reports.

Aeroo
-----
Aeroo is an alternative to Qweb.

It uses ``Libreoffice`` documents as templates.
It aims to offer lattitude to the end user regarding the look of a report.

.. image:: static/description/libreoffice_invoice.png

The report can be rendered as ``PDF``.

.. image:: static/description/libreoffice_invoice_pdf.png

Installation
============
There are two linux packages required for running this module.

.. code-block:: bash

    sudo apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        poppler-utils

The module uses `libreoffice-writer <https://fr.libreoffice.org/discover/writer/>`_ in headless mode for rendering the reports.

When reports in pdf format for multiple records (in list view) it uses `poppler-utils <https://poppler.freedesktop.org>`_
to merge the rendered reports into a single pdf.

See the Dockerfile on this repository for details.

Configuration
=============
Aeroo reports can be found under the ``Dashboard`` application.

.. image:: static/description/aeroo_report_menu.png

When configuring an aeroo report, multiple parameters must be defined.

.. image:: static/description/report_form.png

Name
----
The field ``Name`` is the label that will appear on the print button.

.. image:: static/description/invoice_print_button.png

Model
-----
This is the technical value that links the report with a given type of document.

In the example, the model is an invoice, so the technical value is ``account.move``.
This technical value can be found in the url of the form view.

.. image:: static/description/invoice_url_model.png

Template Name
-------------
This is a technical value that identifies your report in Odoo.
The given value is arbitrary.

.. image:: static/description/report_technical_name.png

You should choose a value with no accent, no special caracters and no space.
Only letters and underscores.

The value must be unique throughout the system.

Template Mime-type
------------------
This field identifies the type of template.

.. image:: static/description/report_template_mime_type.png

Output Mime-type
----------------
Three formats are available for the generated report.

.. image:: static/description/report_output_mime_type.png

Typically, a report is printed as ``PDF``.

However, for testing a report, rendering as ``ODT`` can be useful.

Otherwise, rendering as ``Microsoft Word`` can be useful in case you
need to edit the document manually before printing it as ``PDF``.

Template
--------
There are 3 options for defining the report template.

.. image:: static/description/report_template_options.png

Database
~~~~~~~~
This option allows to upload a template file from your computer.

.. image:: static/description/report_template_database.png

File
~~~~
This option allows to use a file defined in a module.

.. image:: static/description/report_template_file.png

The given path must start with the name of the module,
followed by the path of the file inside that module.

This option is mostly intended for demo reports.

Multiple Templates
~~~~~~~~~~~~~~~~~~
The third option is ``Different Template per Language / Company``.

.. image:: static/description/report_template_multi.png

This option allows to define a specific template to use per company and / or language.

When managing a report that needs to be printed in the language of a partner,
it is easier to maintain completely separate templates for each language.

Also, mainting separate templates per company is useful if you want the look of the report
to be different per company.

.. image:: static/description/report_template_multi_form.png

Both the language and the company are optional fields.
Letting the field empty is a wildcard.

The first matching template is always used when printing a report.
Therefore, template lines with wildcards should be placed last.

.. image:: static/description/report_template_multi_filled.png

Report Context
--------------
When formating numbers, currencies and dates in a report, the report engine needs to know
for which language, timezone and localization to format these values.

This section allows the engine to evaluate these values.

.. image:: static/description/report_context.png

Typically, the values will be inherited from the user generating the report.

.. image:: static/description/report_context_user.png

Or linked to the partner related to the document.

.. image:: static/description/report_context_partner.png

List Views
----------
By default, aeroo reports can be generated from a list view.

.. image:: static/description/list_view_standard_report.png

The result is a merged ``PDF`` document containing the combined reports for all selected records.

.. image:: static/description/list_view_standard_report_pdf.png

However, it is sometime required to have a single report that takes as input a list of records.

One typical example is a report based on a selection of timesheet lines.

You can define such report by checking the box ``Generate Report From Record List``.

.. image:: static/description/report_from_record_list.png

When printing the report, the template is rendered only one time with the given list of records.

.. image:: static/description/list_view_report.png

.. image:: static/description/list_view_report_pdf.png

Inside the Libreoffice template, instead of using the variable ``o``, you must iterate over the variable ``objects``.

.. image:: static/description/report_from_record_list_template.png

Attachments / Filename
----------------------
By default, when printing a report, the name of the file is the name of the report.

.. image:: static/description/default_filename.png

This can be customized.

.. image:: static/description/report_attachment_filename.png

You can also customize the file name per language.

.. image:: static/description/report_attachment_filename_multi.png

..

    A line with the field Language empty is interpreted as a wildcard.
    Such line must be placed last.

Reload From Attachment
----------------------
When this box is checked, the report will be saved as attachment to the document when printed.

.. image:: static/description/report_reload_from_attachment.png

Then, when printing again the report, the same file is returned instead of rerendering the report.

The report is rerendered if the file name changes.

This feature is typically used for invoices.
Once sent to a customer, the PDF of an invoice may not be changed.

Add To Print Menu
-----------------
The button ``Add in the Print menu`` adds an item in the print menu of the form view of the related model.

.. image:: static/description/report_add_print_menu.png

.. image:: static/description/form_print_menu.png

Editing a Template
==================

Fields
------
To display the value of a field inside a template, you must insert a field of type ``Placeholder``.

.. image:: static/description/libreoffice_insert_field.png

.. image:: static/description/libreoffice_insert_field_placeholder.png

In ``Placeholder``, you can define the expression to evaluate.

.. image:: static/description/libreoffice_placeholder_filled.png

Then click on insert.

.. image:: static/description/libreoffice_placeholder_insert.png

In this example, we are printing the name of the partner related to the document.

The variable ``o`` represents the document being printed (for example, an invoice or a sales order).

If Statements
-------------
It is possible to display a section of the report based on a condition.

.. image:: static/description/libreoffice_if_statement.png

For this to work, you need to insert two fields of type ``Input Field``.

.. image:: static/description/libreoffice_insert_input_field.png

Inside ``Reference``, you can write your condition.

.. image:: static/description/libreoffice_if_statement_reference.png

The condition must be formatted like an xml node.
The attribute test contains the expression to evaluate.

..

    <if test="place_your_condition_here">

The second input field contains the end statement.

.. image:: static/description/libreoffice_if_statement_end.png

For Loops
---------
It is possible to iterate over a list of records inside a table.

.. image:: static/description/libreoffice_for_loop.png

For this to work, the beginning and ending clauses of the loop must be placed in rows of the table.
The rows containing these clauses are removed when rendering the report.

The beginning clause must contain the code of the loop.
The format is similar to ``if statements``.

.. image:: static/description/libreoffice_for_loop_reference.png

The attribute each must contain the loop.

..

    <for each="line in o.invoice_line_ids">

1. The first part ``line`` is the name of the variable for the iteratee. It can be a variable name of your choice.

2. The second part ``o.invoice_line_ids`` is the iterator.

Images
------
The engine allows to render images in reports.

To do so, you must insert a frame.

.. image:: static/description/libreoffice_insert_frame.png

In the ``Options`` tab, enter the technical value in ``Name``.

.. image:: static/description/libreoffice_frame_options.png

The technical value is:

..

    image: asimage(your_expression)

Where ``your_expression`` is the python expression to get the content of your image.

In the ``Type`` tab, make sure that your image is sized relative to the paragraph.

.. image:: static/description/libreoffice_frame_type.png

Then, you may resize the frame to get the desired width and height.

.. image:: static/description/libreoffice_image_resize.png

Barcodes
--------
Barcodes can be inserted the same way as other images.

However, the technical value is a bit different.

.. image:: static/description/libreoffice_frame_barcode_options.png

..

    image: barcode(your_barcode, barcode_type, height)

For now, the available types of barcode are:

* ean13
* code128
* code39

Numbers
-------
When inserting a field that renders a number, you must use a utility function
to format the number properly.

.. image:: static/description/libreoffice_number_utilities.png

Aeroo defines 2 helpers for formatting numbers.

* format_decimal
* format_currency

Example for format_decimal
~~~~~~~~~~~~~~~~~~~~~~~~~~
This function takes a number.
It returns the amount formatted in the context of the report.

.. code-block:: python

    format_decimal(o.amount_total)

If the report is printed in Canada French, the output will look like:

.. code-block::

    1 500,00

Exemple for format_currency
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This function takes a number and a currency object.
It returns the amount and currency symbol formatted in the context of the report.

.. code-block:: python

    format_currency(o.amount_total, o.currency_id)

If the report is printed in Canada French, the output will look like:

.. code-block::

    1 500,00 $US


Force a number format
~~~~~~~~~~~~~~~~~~~~~
Both format_decimal and format_currency functions accept an optional `amount_format` parameter.

This parameter accepts a number format using the variables documented on the babel website:

http://babel.pocoo.org/en/latest/numbers.html#pattern-syntax

Forcing a Country
~~~~~~~~~~~~~~~~~
Languages in Odoo are very complex to maintain.
For example, having all ``en_CA``, ``en_US``, ``fr_CA``, ``fr_FR`` loaded in Odoo would lead to a lot of maintainance effort.

Depending on the country, the amount in currency should be formatted differently:

* If you have a customer in United-States, he might expect the default ``$`` symbol to represent ``USD``, and ``CA$`` to represent ``CAD``.
* If your customer is in Canada, he might however expect ``$`` to represent ``CAD``, and ``US$`` to represent ``USD``.

Aeroo mitigates this issue by combining the contextual Odoo language and country together.

If your Odoo language is ``fr_FR`` and your country is Canada, you get the locale ``fr_CA``.

To use this feature, you may call the ``format_currency`` with an optional ``country`` parameter.

.. code-block:: python

    format_currency(o.amount_total, o.currency_id, country=o.partner_id.country_id)


Default Countries and Currencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since version ``2.2.0`` of ``report_aeroo``, it is possible to define a default country and currency on the report.

.. image:: static/description/report_context_country_and_currency.png

These fields are evaluated at rendering, like ``Language Evaluation`` and ``Company Evaluation``.

The values are used by default in the ``format_currency`` function.
Therefore, in your template, each time you need to show an amount in currency, you only need to pass the amount as parameter:

.. code-block:: python

    format_currency(o.amount_total)

Suppose the language is evaluated to ``fr_FR``, the country is ``Canada`` and the currency is ``USD``,
you would get an amount format as follow:

.. code-block::

    1 500,00 $US

Date and Time
-------------
Similarly to numbers, you can format a date field.

.. image:: static/description/libreoffice_date_field.png

Aeroo defines the following helpers for formatting dates and time.

* format_date
* format_datetime
* today
* now

The variables that you can use in these functions are documented on the babel website:

http://babel.pocoo.org/en/latest/dates.html#date-fields

Exemple for format_date
~~~~~~~~~~~~~~~~~~~~~~~
This function formats a date object into a string.

.. code-block:: python

    format_date(o.date_invoice, 'dd MMMM yyyy')

If the report is printed in French, the output will look like:

.. code-block::

    06 avril 2018

Exemple for format_datetime
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This function formats a datetime object into a string.

.. code-block:: python

    format_datetime(o.confirmation_date, 'dd MMMM yyyy hh:mm a')

If the report is printed in French, the output will look like:

.. code-block::

    6 avril 2018 10:34 AM

Exemple for today
~~~~~~~~~~~~~~~~~
The function ``today`` is the same as ``format_date``, but with the current date in the user's timezone.

.. code-block:: python

    today('dd MMMM yyyy')

Suppose we are on the 6 of April 2018 and the report is printed in French, the output will look like:

.. code-block::

    06 avril 2018

Exemple for now
~~~~~~~~~~~~~~~
The function ``now`` is the same as ``format_datetime``, but with the current time in the user's timezone.

.. code-block:: python

    now('dd MMMM yyyy hh:mm a')

Suppose we are on the 6 of April 2018, 10:34 AM and the report is printed in French, the output will look like:

.. code-block::

    06 avril 2018 10:34 AM

Grouping Rows
-------------
It is possible to group rows to display in a table.

In the following example, the invoice lines are grouped by per product category:

.. code-block:: xml

    <for each="(month, lines) in group_by(objects, lambda line: (line.date).replace(day=1))">

Each tuple contains:

1. The groupment key
2. The records matching this groupment key

Example
~~~~~~~
Here is a preview on how to organize the for/each statements in your libreoffice template.

.. image:: static/description/libreoffice_group_by.png

In this example, we define two nested ``For Each`` loops.

The outer loop groups the records by month.

Inside the outer loop, the month is printed in one line, followed by one line
per record for this month.

Grouping Rows in a Particular Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By default, the groupment keys are sorted in natural order.
If the groupment key is a string, it will be sorted alphabetically.

Usually, we will require to sort the grouped records by some criteria.
This can be done using the argument ``sort`` of the ``group_by`` function.

The ``sort`` argument expects a function.
This function takes as argument the groupment key.

In the following example, the groupment keys (the products) are sorted by their ``Display Name``.

.. code-block:: xml

    <for each="(product, lines) in group_by(objects, lambda line: line.product_id, lambda product: product.display_name)">

Contributors
============
* Alistek
* Savoir-faire Linux
* Numigi (tm) and all its contributors (https://bit.ly/numigiens)
