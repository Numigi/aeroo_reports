# Aeroo Check Printing

This modules allows to create check reports using Aeroo.

Each journal (bank account) points its own proper check report template.
When clicking on 'Print Check' on the payment, the proper Aeroo template is selected.

## Configuration

To define an aeroo as check report:

* Go to Invoicing / Configuration / Journals
* Select your bank/check journal
* In the Advanced Settings tab, under Check Printing, select your check report template.

![Journal Form](static/description/account_journal_form.png?raw=true)

## Compatibility with US Accounting

In order to use this module with the United States accounting, you will need to disable the default US check layout.

![US Compatibility](static/description/disable_us_check_layout.png?raw=true)

## Check Stubs

A method `get_aeroo_check_stub_lines` is added on account.payment.
This method allows to get the info to display on the check stub.
This method can be called inside an libreoffice input field.
For a complete example, see the [demo template](demo/check_sample.odt)

Contributors
------------
* Savoir-faire Linux
* Numigi (tm) and all its contributors (https://bit.ly/numigiens)

More information
----------------
* Meet us at https://bit.ly/numigi-com
