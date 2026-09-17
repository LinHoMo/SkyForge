<script setup lang="ts">
/**
 * ComplianceTrendChart 合规趋势柱状图
 *
 * 抽为独立组件并由 dashboard 以 defineAsyncComponent 异步加载：
 * 这样 echarts/vue-echarts（~700KB chunk）只在确实有趋势数据、
 * 需要渲染图表时才下载，不占用 dashboard 首屏关键路径。
 * 图表类型仍按需注册（BarChart + Grid/Tooltip/Legend + CanvasRenderer）。
 */
import { BarChart, LineChart } from "echarts/charts";
import {
	GridComponent,
	LegendComponent,
	TooltipComponent,
} from "echarts/components";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";

use([
	CanvasRenderer,
	LineChart,
	BarChart,
	GridComponent,
	TooltipComponent,
	LegendComponent,
]);

defineProps<{
	/** ECharts option，由父组件计算好后传入 */
	option: unknown;
}>();
</script>

<template>
	<v-chart :option="(option as any)" class="compliance-chart" autoresize />
</template>

<style scoped>
.compliance-chart {
	height: 240px;
	width: 100%;
}
</style>
