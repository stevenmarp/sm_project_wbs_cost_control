/** @odoo-module **/

import { visitXML } from "@web/core/utils/xml";

export class GanttArchParser {
    parse(arch) {
        const archInfo = {};
        visitXML(arch, (node) => {
            if (node.tagName === "sm_gantt") {
                archInfo.dateStart = node.getAttribute("date_start") || "sm_gantt_start";
                archInfo.duration = node.getAttribute("duration") || "sm_gantt_duration";
                archInfo.text = node.getAttribute("text") || "name";
                archInfo.progress = node.getAttribute("progress") || "progress";
                archInfo.open = node.getAttribute("open") || "sm_gantt_open";
                archInfo.linksJson = node.getAttribute("links_serialized_json") || "sm_gantt_links_serialized_json";
                archInfo.linkModel = node.getAttribute("link_model") || "";
                archInfo.linkSourceField = node.getAttribute("link_source_field") || "wbs_id";
                archInfo.linkTargetField = node.getAttribute("link_target_field") || "depending_wbs_id";
                archInfo.linkTypeField = node.getAttribute("link_type_field") || "relation_type";
                archInfo.idField = node.getAttribute("id_field") || "id";
            }
        });
        return archInfo;
    }
}
