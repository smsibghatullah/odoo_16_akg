/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsKanbanRecord } from "@documents/views/kanban/documents_kanban_model";

import { XLSX_MIME_TYPE } from "@documents_spreadsheet/helpers";

patch(DocumentsKanbanRecord.prototype, "documents_spreadsheet_documents_kanban_record", {
    /**
     * @override
     */
    isViewable() {
        return (
            this.data.handler === "spreadsheet" ||
            this.data.mimetype === XLSX_MIME_TYPE ||
            this._super(...arguments)
        );
    },

    /**
     * @override
     * @param {MouseEvent} ev
     */
    async onClickPreview(ev) {
        if (this.data.mimetype === "application/vnd.ms-excel") {
            this.model.env.services.notification.add(
                this.model.env._t("Only XLSX files can be opened with Odoo Spreadsheet"),
                { type: "warning" }
            );
            return;
        }
        this._super(...arguments);
    },
});
