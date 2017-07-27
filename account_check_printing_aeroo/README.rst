# Aeroo Check Printing

This modules allows to create check reports using Aeroo.

Each journal (bank account) points its own proper check report template.
When clicking on 'Print Check' on the payment, the proper Aeroo template is selected.


## Num2words

Odoo defines its own helpers to convert amounts to words.
This module uses the python library num2words instead.

https://pypi.python.org/pypi/num2words


## Check Language

In standard Odoo, the amount in words depends on the language of the user.
This is wrong because checks are already pre-printed in a language, so the number in words needs to be printed in the same language.
Therefore, on the journal, there is a new field 'Check Report Language' used to specify the language of the check.


Contributors
------------
* David Dufresne (david.dufresne@savoirfairelinux.com)

More information
----------------
* Module developed and tested with Odoo version 10.0
* For questions, please contact our support services
(support@savoirfairelinux.com)
