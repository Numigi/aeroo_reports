odoo.define("report_aeroo.action_manager", function (require) {
"use strict";

// Need to load qweb reports (report.report) before loading aeroo.
// The method ActionManager.ir_actions_report defined in report.report
// prevents generating reports other than qweb.
require("web.ReportActionManager");

var ActionManager = require("web.ActionManager");
var framework = require("web.framework");
var session = require("web.session");
var pyeval = require("web.py_utils");

ActionManager.include({
    /**
     * Dispatch aeroo reports.
     */
    _executeReportAction(action, options) {
        if (action.report_type === "aeroo") {
            return this._printAerooReport(action, options).then(() => {
                return this._afterAerooReportDownloaded(action, options);
            });
        } else {
            return this._super(action, options);
        }
    },
    /**
     * After the aeroo report is downloaded, execute post actions.
     *
     * This code is equivalent to the callback defined method _triggerDownload
     * at odoo/addons/web/static/src/js/chrome/action_manager_report.js
     */
    _afterAerooReportDownloaded(action, options){
        if (action.close_on_report_download) {
            var closeAction = {type: "ir.actions.act_window_close"};
            return this.doAction(closeAction, _.pick(options, "on_close"));
        } else {
            return options.on_close();
        }
    },
    /**
     * Print an aeroo report.
     *
     * This function was taken from code removed by the editor and adapted.
     * https://github.com/odoo/odoo/commit/4787bc75
     */
    _printAerooReport(action, options) {
        var self = this;
        framework.blockUI();

        action = _.clone(action);

        const context = session.user_context

        return new Promise(function (resolve, reject) {
            session.get_file({
                url: "/web/report_aeroo",
                data: {
                    report_id: action.id,
                    record_ids: JSON.stringify(action.context.active_ids),
                    context: JSON.stringify(context),
                },
                success: resolve,
                error: (err) => {
                    self.call('crash_manager', 'rpc_error', err);
                    reject();
                },
                complete: framework.unblockUI,
            });
        });
    },
});

});
