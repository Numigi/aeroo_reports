/** @odoo-module **/

import { Component, useRef } from '@odoo/owl';
import { registerPublicWidget } from 'web.public.widget';
import { PortalSidebar } from 'portal.PortalSidebar';

class AccountPortalSidebar extends PortalSidebar {
    setup() {
        super.setup();
        this.sidebarRef = useRef("sidebar");
    }
}


registerPublicWidget({
    selector: '.o_portal_invoice_sidebar',
    Component: AccountPortalSidebar,
});