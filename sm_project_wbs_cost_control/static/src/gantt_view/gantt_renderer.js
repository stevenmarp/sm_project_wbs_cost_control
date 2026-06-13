/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

const DAY = 86400000;
const COLORS = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626", "#0891b2", "#db2777"];

function cloneDate(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function addDays(date, days) {
    const result = cloneDate(date);
    result.setDate(result.getDate() + days);
    return result;
}

function addMonths(date, months) {
    const result = cloneDate(date);
    result.setMonth(result.getMonth() + months);
    return result;
}

function startOfWeek(date) {
    const result = cloneDate(date);
    const day = result.getDay() || 7;
    result.setDate(result.getDate() - day + 1);
    return result;
}

function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
}

function startOfQuarter(date) {
    return new Date(date.getFullYear(), Math.floor(date.getMonth() / 3) * 3, 1);
}

function startOfYear(date) {
    return new Date(date.getFullYear(), 0, 1);
}

function formatDate(date) {
    return date.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

function formatShort(date, scale) {
    if (scale === "day") {
        return date.toLocaleDateString(undefined, { day: "2-digit", month: "short" });
    }
    if (scale === "week") {
        return `W${Math.ceil((((date - startOfYear(date)) / DAY) + startOfYear(date).getDay() + 1) / 7)}`;
    }
    if (scale === "month") {
        return date.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
    }
    if (scale === "quarter") {
        return `Q${Math.floor(date.getMonth() / 3) + 1} ${date.getFullYear()}`;
    }
    return String(date.getFullYear());
}

export class GanttRenderer extends Component {
    static template = "sm_project_wbs_cost_control.GanttRenderer";
    static props = ["model", "archInfo", "onRowOpen?"];

    setup() {
        this.state = useState({
            currentScale: "month",
            showGrid: true,
            fullscreen: false,
            sortMode: "date_asc",
        });
    }

    getScaleButtons() {
        return [
            { name: "day", label: "Day" },
            { name: "week", label: "Week" },
            { name: "month", label: "Month" },
            { name: "quarter", label: "Quarter" },
            { name: "year", label: "Year" },
        ];
    }

    onScaleChange(scale) {
        this.state.currentScale = scale;
    }

    onToggleGrid() {
        this.state.showGrid = !this.state.showGrid;
    }

    onToggleFullscreen() {
        this.state.fullscreen = !this.state.fullscreen;
    }

    onSort(mode) {
        this.state.sortMode = mode;
    }

    onRowOpen(row) {
        if (this.props.onRowOpen) {
            this.props.onRowOpen(row);
        }
    }

    getRows() {
        const ganttData = this.props.model.ganttData || { data: [], links: [] };
        const rows = [...(ganttData.data || [])];
        const projectRows = rows.filter((row) => row.isProject);
        const taskRows = rows.filter((row) => !row.isProject);
        taskRows.sort((a, b) => {
            if (this.state.sortMode === "name_asc") {
                return a.text.localeCompare(b.text);
            }
            if (this.state.sortMode === "name_desc") {
                return b.text.localeCompare(a.text);
            }
            if (this.state.sortMode === "progress_desc") {
                return b.progress - a.progress;
            }
            if (this.state.sortMode === "progress_asc") {
                return a.progress - b.progress;
            }
            if (this.state.sortMode === "date_desc") {
                return b.start - a.start;
            }
            return a.start - b.start;
        });
        const grouped = [];
        for (const project of projectRows) {
            const children = taskRows.filter((row) => row.parent === project.id);
            if (children.length) {
                const progress = children.reduce((sum, row) => sum + row.progress, 0) / children.length;
                grouped.push({ ...project, progress, key: project.id });
                grouped.push(...children.map((row, index) => ({ ...row, key: row.id, color: COLORS[index % COLORS.length] })));
            }
        }
        const withoutProject = taskRows.filter((row) => !row.parent);
        grouped.push(...withoutProject.map((row, index) => ({ ...row, key: row.id, color: COLORS[index % COLORS.length] })));
        return grouped;
    }

    getTimeline() {
        const ganttData = this.props.model.ganttData || { data: [], links: [] };
        const tasks = (ganttData.data || []).filter((row) => !row.isProject);
        const today = cloneDate(new Date());
        let minDate = today;
        let maxDate = addDays(today, 30);
        if (tasks.length) {
            minDate = tasks.reduce((min, row) => row.start < min ? row.start : min, tasks[0].start);
            maxDate = tasks.reduce((max, row) => row.end > max ? row.end : max, tasks[0].end);
        }
        const scale = this.state.currentScale;
        const cells = [];
        let cursor;
        let end;
        let step;
        let cellWidth;

        if (scale === "day") {
            cursor = addDays(minDate, -3);
            end = addDays(maxDate, 7);
            step = (date) => addDays(date, 1);
            cellWidth = 58;
        } else if (scale === "week") {
            cursor = startOfWeek(addDays(minDate, -14));
            end = addDays(maxDate, 21);
            step = (date) => addDays(date, 7);
            cellWidth = 96;
        } else if (scale === "quarter") {
            cursor = startOfQuarter(addMonths(minDate, -3));
            end = addMonths(maxDate, 6);
            step = (date) => addMonths(date, 3);
            cellWidth = 154;
        } else if (scale === "year") {
            cursor = startOfYear(addMonths(minDate, -12));
            end = addMonths(maxDate, 12);
            step = (date) => addMonths(date, 12);
            cellWidth = 190;
        } else {
            cursor = startOfMonth(addMonths(minDate, -1));
            end = addMonths(maxDate, 2);
            step = (date) => addMonths(date, 1);
            cellWidth = 126;
        }

        while (cursor <= end) {
            cells.push({ date: cursor, label: formatShort(cursor, scale), key: cursor.toISOString() });
            cursor = step(cursor);
        }
        const start = cells.length ? cells[0].date : today;
        const finish = step(cells.length ? cells[cells.length - 1].date : addDays(today, 1));
        const gridWidth = this.state.showGrid ? 320 : 0;
        const availableWidth = Math.max((window.innerWidth || 1280) - gridWidth - 32, 600);
        const width = Math.max(cells.length * cellWidth, availableWidth);
        cellWidth = Math.max(cellWidth, Math.floor(width / Math.max(cells.length, 1)));
        return { cells, start, finish, width, cellWidth, scale };
    }

    getTimelineGridStyle(timeline) {
        return `width:${timeline.width}px;grid-template-columns:repeat(${timeline.cells.length}, ${timeline.cellWidth}px);`;
    }

    getBarStyle(row, timeline) {
        const range = Math.max(timeline.finish - timeline.start, DAY);
        const left = Math.max(((row.start - timeline.start) / range) * timeline.width, 0);
        const right = Math.min(((row.end - timeline.start) / range) * timeline.width, timeline.width);
        const width = Math.max(right - left, 22);
        const color = row.varianceCost < 0 ? "#dc2626" : row.color || "#2563eb";
        return `left:${left}px;width:${width}px;background:${color};`;
    }

    getProgressStyle(row) {
        return `width:${Math.min(Math.max(row.progress || 0, 0), 100)}%;`;
    }

    getBarTitle(row) {
        return `${row.text} | ${formatDate(row.start)} | ${row.duration} day(s) | ${Math.round(row.progress || 0)}%`;
    }

    getLinkPaths(rows, timeline) {
        const rowIndex = {};
        for (let index = 0; index < rows.length; index++) {
            rowIndex[rows[index].id] = index;
        }
        const taskById = Object.fromEntries(rows.filter((row) => !row.isProject).map((row) => [row.id, row]));
        const range = Math.max(timeline.finish - timeline.start, DAY);
        const paths = [];
        const ganttData = this.props.model.ganttData || { data: [], links: [] };
        for (const link of ganttData.links || []) {
            const source = taskById[link.source];
            const target = taskById[link.target];
            if (!source || !target) {
                continue;
            }
            const sourceX = Math.min(((source.end - timeline.start) / range) * timeline.width, timeline.width);
            const targetX = Math.max(((target.start - timeline.start) / range) * timeline.width, 0);
            const sourceY = rowIndex[source.id] * 44 + 22;
            const targetY = rowIndex[target.id] * 44 + 22;
            const midX = sourceX + Math.max((targetX - sourceX) / 2, 18);
            paths.push({ key: link.id, d: `M ${sourceX} ${sourceY} C ${midX} ${sourceY}, ${midX} ${targetY}, ${targetX} ${targetY}` });
        }
        return paths;
    }

    getLinksHeight(rows) {
        return rows.length * 44;
    }

    getMoney(value) {
        return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(value || 0);
    }

    onExportCSV() {
        const rows = this.getRows().filter((row) => !row.isProject);
        let csv = "WBS,Project,Start,Duration,Progress,Planned Cost,Actual Cost,Variance\n";
        for (const row of rows) {
            const values = [row.text, row.projectName, formatDate(row.start), row.duration, Math.round(row.progress || 0), row.plannedCost, row.actualCost, row.varianceCost];
            csv += values.map((value) => `"${String(value === null || value === undefined ? "" : value).replace(/"/g, '""')}"`).join(",") + "\n";
        }
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "wbs_gantt_export.csv";
        link.click();
        URL.revokeObjectURL(url);
    }
}
