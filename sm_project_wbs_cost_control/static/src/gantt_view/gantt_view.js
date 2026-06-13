/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GanttArchParser } from "./gantt_arch_parser";
import { GanttModel } from "./gantt_model";
import { GanttRenderer } from "./gantt_renderer";
import { GanttController } from "./gantt_controller";

export const smGanttView = {
    type: "sm_gantt",
    display_name: "Gantt",
    icon: "fa-tasks",
    multiRecord: true,
    Controller: GanttController,
    Renderer: GanttRenderer,
    Model: GanttModel,
    ArchParser: GanttArchParser,
    searchMenuTypes: ["filter", "favorite"],

    props: (genericProps, view) => {
        const { arch, fields, resModel } = genericProps;
        const archInfo = new view.ArchParser().parse(arch, fields);
        return {
            ...genericProps,
            modelParams: { resModel, fields, ...archInfo },
            Model: view.Model,
            Renderer: view.Renderer,
            archInfo,
        };
    },
};

registry.category("views").add("sm_gantt", smGanttView);
