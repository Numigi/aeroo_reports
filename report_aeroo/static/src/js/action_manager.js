odoo.define("report_aeroo.action_manager", function (require) {
"use strict";

// Need to load qweb reports (report.report) before loading aeroo.
// The method ActionManager.ir_actions_report defined in report.report
// prevents generating reports other than qweb.
require("report.report");

var ActionManager = require("web.ActionManager");
var crashManager = require("web.crash_manager");
var framework = require("web.framework");
var session = require("web.session");
var pyeval = require("web.pyeval");

ActionManager.include({
    /**
     * Dispatch aeroo reports.
     */
    ir_actions_report(action, options) {
        if (action.report_type === "aeroo") {
            return this._printAerooReport(action, options);
        } else {
            return this._super(action, options);
        }
    },
    /**
     * Print an aeroo report.
     *
     * This function was taken from code removed by the editor and adapted.
     * https://github.com/odoo/odoo/commit/4787bc75
     */
    _printAerooReport(action, options) {
        framework.blockUI();

        action = _.clone(action);
        var evalContexts = ([session.user_context] || []).concat([action.context]);
        action.context = pyeval.eval("contexts", evalContexts);

        var self = this;
        return $.Deferred(function (deferred) {
            session.get_file({
                url: "/web/report_aeroo",
                data: {action: JSON.stringify(action)},
                complete: framework.unblockUI,
                success(){
                    if (!self.dialog) {
                        options.on_close();
                    }
                    self.dialog_stop();
                    deferred.resolve();
                },
                error(){
                    crashManager.rpc_error.apply(crashManager, arguments);
                    deferred.reject();
                },
            });
        });
    },
});

});
