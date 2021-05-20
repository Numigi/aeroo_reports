Aeroo Reports
-------------
This module is the main module required for using Aeroo reports.

.. contents:: Table of Contents

Installation
------------
There are two linux packages required for running this module.

.. code-block:: bash

    sudo apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        poppler-utils

The module uses `libreoffice-writer <https://fr.libreoffice.org/discover/writer/>`_ in headless mode for rendering the reports.

When reports in pdf format for multiple records (in list view) it uses `poppler-utils <https://poppler.freedesktop.org>`_
to merge the rendered reports into a single pdf.

See the Dockerfile on this repository for details.

Contributors
------------
* Alistek
* Savoir-faire Linux
* Numigi (tm) and all its contributors (https://bit.ly/numigiens)

More information
----------------
* Meet us at https://bit.ly/numigi-com
