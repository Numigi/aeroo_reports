/** @odoo-module **/

import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

async function aerooReportHandler(action, options, env) {
    if (action.report_type === "aeroo") {
        let cloned_action = { ...action };
        cloned_action.context = cloned_action.context || {};

        env.services.ui.block();
        try {
            await download({
                url: "/web/report_aeroo",
                data: {
                    report_id: cloned_action.id,
                    record_ids: JSON.stringify(cloned_action.context.active_ids || []),
                    // On retire la ligne "context: ..." qui faisait crasher le JS et le Python
                },
            });
        } finally {
            env.services.ui.unblock();
        }

        // Sécurisation avec options?.onClose pour éviter un autre undefined
        const onClose = options?.onClose;
        if (cloned_action.close_on_report_download) {
            return env.services.action.doAction(
                { type: "ir.actions.act_window_close" },
                { onClose }
            );
        } else if (onClose) {
            onClose();
        }

        return Promise.resolve(true);
    }
}

registry.category("ir.actions.report handlers").add("aeroo_handler", aerooReportHandler);