odoo.define('report_aeroo_invoice.AccountPortalSidebar', function (require) {
'use strict';

/**
    Override all methods of AccountPortalSidebar.

    These methods are tightly coupled with the qweb invoice report.

    Without overriding these methods, an error is raised because the content of
    the iframe is a pdf and not an html document.

    The solution was to rewrite the whole file, because there is not much code left.
**/

require('account.AccountPortalSidebar')
var publicWidget = require('web.public.widget');
var PortalSidebar = require('portal.PortalSidebar');

publicWidget.registry.AccountPortalSidebar = PortalSidebar.extend({
    selector: '.o_portal_invoice_sidebar',
});
});
