/** @odoo-module **/

import { Model } from "@web/model/model";
import { KeepLast } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";

function parseDate(value) {
    if (!value) {
        return null;
    }
    if (value instanceof Date) {
        return value;
    }
    const parts = String(value).split(/[- :T]/).map((part) => parseInt(part, 10));
    return new Date(parts[0], (parts[1] || 1) - 1, parts[2] || 1, parts[3] || 0, parts[4] || 0, parts[5] || 0);
}

export class GanttModel extends Model {
    static services = ["orm"];

    setup(params) {
        super.setup(params);
        this.metaData = params;
        this.ganttData = { data: [], links: [] };
        this.dataVersion = 0;
        this.keepLast = new KeepLast();
    }

    async load(searchParams) {
        this.searchParams = searchParams;
        await this.keepLast.add(this._fetchData());
        if (this.isReady) {
            this.notify();
        }
    }

    hasData() {
        return this.ganttData.data.length > 0;
    }

    async _fetchData() {
        const { dateStart, duration, text, progress, open, linksJson } = this.metaData;
        const fieldNames = [...new Set([text, dateStart, duration, progress, open, linksJson, "project_id", "state", "planned_cost", "actual_cost", "variance_cost"].filter(Boolean))];
        const records = await this.orm.searchRead(
            this.metaData.resModel,
            (this.searchParams && this.searchParams.domain) || [],
            fieldNames,
            { order: `${dateStart} asc, id asc` }
        );
        this._convertData(records);
    }

    _convertData(records) {
        const { dateStart, duration, text, progress, open, linksJson } = this.metaData;
        const data = [];
        const links = [];
        const projects = {};

        for (const record of records) {
            const project = record.project_id;
            if (project && Array.isArray(project) && !projects[project[0]]) {
                const projectId = `project-${project[0]}`;
                projects[project[0]] = projectId;
                data.push({
                    id: projectId,
                    serverId: project[0],
                    text: project[1],
                    isProject: true,
                    progress: 0,
                    open: true,
                    state: "project",
                });
            }

            const start = parseDate(record[dateStart]) || new Date();
            const taskDuration = Math.max(parseInt(record[duration] || 1, 10), 1);
            const row = {
                id: record.id,
                text: record[text] || "",
                start,
                duration: taskDuration,
                end: new Date(start.getTime() + taskDuration * 86400000),
                progress: Math.max(record[progress] || 0, 0),
                open: record[open] !== undefined ? record[open] : true,
                state: record.state || "",
                plannedCost: record.planned_cost || 0,
                actualCost: record.actual_cost || 0,
                varianceCost: record.variance_cost || 0,
                projectName: project && Array.isArray(project) ? project[1] : "",
                parent: project && Array.isArray(project) ? projects[project[0]] : false,
            };
            data.push(row);

            const rawLinks = record[linksJson];
            if (rawLinks) {
                try {
                    links.push(...JSON.parse(rawLinks));
                } catch {
                    continue;
                }
            }
        }

        const seen = new Set();
        const uniqueLinks = [];
        for (const link of links) {
            if (!seen.has(link.id)) {
                seen.add(link.id);
                uniqueLinks.push(link);
            }
        }

        this.ganttData = { data, links: uniqueLinks };
        this.dataVersion++;
    }

    async updateTask(taskId, values) {
        await rpc("/web/dataset/call_kw", {
            model: this.metaData.resModel,
            method: "write",
            args: [[taskId], values],
            kwargs: {},
        });
    }

    async createLink(values) {
        if (!this.metaData.linkModel) {
            return false;
        }
        return rpc("/web/dataset/call_kw", {
            model: this.metaData.linkModel,
            method: "create",
            args: [values],
            kwargs: {},
        });
    }
}
