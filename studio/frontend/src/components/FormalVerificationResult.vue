<script setup lang="ts">
import {
	AlertTriangle,
	CheckCircle2,
	ChevronDown,
	ChevronRight,
	HelpCircle,
	Hourglass,
	Play,
	XCircle,
} from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const { t } = useI18n();

/**
 * FormalVerificationResult 形式化验证结果组件（Task 5.5）
 *
 * 展示 Z3 SMT Solver + CBMC 对契约的形式化验证结果。
 * 状态分类对标 Frama-C 四态：
 *   - Valid（已证明）→ 绿
 *   - Fail（证伪/发现反例）→ 红
 *   - Unknown（无法自动证明，需人工）→ 黄
 *   - Timeout（求解超时）→ 灰
 * 后端仅返回 passed/failed/skipped，前端按 counter_example 文本把 skipped 细分为
 * Unknown（工具不可用等）与 Timeout（求解超时）。
 *
 * - 顶部状态徽章（四态颜色）
 * - Valid/Fail/Unknown/Timeout 统计徽章
 * - 各检查项列表（名称、状态图标、耗时、工具标签）
 * - 反例展示区（failed/skipped 项展开后显示）
 * - 工具标识（Z3 / CBMC / Z3+CBMC / Mock）
 * - 空状态：loading=false 且 result=null 时提示开始验证
 * - Loading 状态：骨架屏
 *
 * 使用 shadcn-vue Card / Skeleton / Button 组件 + 内联徽章样式
 * （与 ContractCheckResult.vue 风格保持一致）。
 */
import type {
	VerificationCheck,
	VerificationResult,
} from "@/types/verification";

interface Props {
	/** 验证结果对象（与 /api/verify 返回格式一致） */
	result: VerificationResult | null;
	/** 是否正在加载 */
	loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
	loading: false,
});

const emit = defineEmits<{
	/** 用户点击"开始验证"按钮 */
	// biome-ignore lint/style/useShorthandFunctionType: Vue defineEmits 需要调用签名语法
	(e: "start-verify"): void;
}>();

/** 当前展开的反例项（按 check.name 索引） */
const expanded = ref<Set<string>>(new Set());

const toggleExpand = (name: string) => {
	const next = new Set(expanded.value);
	if (next.has(name)) next.delete(name);
	else next.add(name);
	expanded.value = next;
};

/**
 * 当结果变化时，自动展开所有 skipped 项的 counter_example。
 *
 * 后端在 Z3/CBMC 不可用时会返回 skipped 检查项，并在 counter_example
 * 字段附带说明（如 "Z3 不可用（pip install z3-solver 启用）"）。
 * 默认展开使用户无需点击即可看到跳过原因，避免误以为前端未调用真实后端。
 */
watch(
	() => props.result,
	(newResult) => {
		const next = new Set<string>();
		if (newResult) {
			for (const c of newResult.checks) {
				if (c.status === "skipped" && c.counter_example) {
					next.add(c.name);
				}
			}
		}
		expanded.value = next;
	},
	{ immediate: true },
);

/** Frama-C 四态分类：Valid / Fail / Unknown / Timeout */
type FourState = "valid" | "fail" | "unknown" | "timeout";

/** 判断文本是否为超时（把 skipped 细分为 Unknown vs Timeout） */
const isTimeoutText = (text?: string | null): boolean =>
	/timeout|timed out|超时/i.test(text ?? "");

/** 单项检查 → 四态分类 */
const classifyCheck = (
	status: VerificationCheck["status"],
	counter?: string | null,
): FourState => {
	if (status === "passed") return "valid";
	if (status === "failed") return "fail";
	return isTimeoutText(counter) ? "timeout" : "unknown";
};

/** 总体四态：passed→valid, failed→fail, skipped→按检查项细分 */
const overallFour = computed<FourState>(() => {
	if (!props.result) return "unknown";
	if (props.result.status === "passed") return "valid";
	if (props.result.status === "failed") return "fail";
	const hasTimeout = props.result.checks.some(
		(c) => c.status === "skipped" && isTimeoutText(c.counter_example),
	);
	return hasTimeout ? "timeout" : "unknown";
});

/** 四态统计计数 */
const fourCounts = computed(() => {
	const c = { valid: 0, fail: 0, unknown: 0, timeout: 0 };
	if (!props.result) return c;
	for (const check of props.result.checks) {
		c[classifyCheck(check.status, check.counter_example)] += 1;
	}
	return c;
});

/** 四态视觉配置（图标/颜色/文案） */
const fourVisual: Record<
	FourState,
	{ icon: unknown; color: string; symbol: string }
> = {
	valid: { icon: CheckCircle2, color: "#10b981", symbol: "✓" },
	fail: { icon: XCircle, color: "#dc2626", symbol: "✗" },
	unknown: { icon: HelpCircle, color: "#f59e0b", symbol: "?" },
	timeout: { icon: Hourglass, color: "#9ca3af", symbol: "⏱" },
};

/** 顶部状态配置（四态横幅） */
const statusConfig = computed(() => {
	if (!props.result) return null;
	const s = overallFour.value;
	const map: Record<
		FourState,
		{ icon: unknown; label: string; color: string; bg: string; border: string }
	> = {
		valid: {
			icon: CheckCircle2,
			label: t("formalVerify.stateValid"),
			color: "#10b981",
			bg: "linear-gradient(to right, #f0fdf4, #ecfdf5)",
			border: "#10b981",
		},
		fail: {
			icon: XCircle,
			label: t("formalVerify.stateFail"),
			color: "#dc2626",
			bg: "linear-gradient(to right, #fef2f2, #fff7ed)",
			border: "#f59e0b",
		},
		unknown: {
			icon: HelpCircle,
			label: t("formalVerify.stateUnknown"),
			color: "#f59e0b",
			bg: "linear-gradient(to right, #fffbeb, #fef3c7)",
			border: "#f59e0b",
		},
		timeout: {
			icon: Hourglass,
			label: t("formalVerify.stateTimeout"),
			color: "#6b7280",
			bg: "linear-gradient(to right, #f9fafb, #f3f4f6)",
			border: "#9ca3af",
		},
	};
	return map[s];
});

/** 总耗时（秒） */
const totalDurationSec = computed(() => {
	if (!props.result) return "0.000";
	return (props.result.total_duration_ms / 1000).toFixed(3);
});

/** 检查项状态图标与颜色（四态） */
const checkVisual = (status: VerificationCheck["status"], counter?: string | null) =>
	fourVisual[classifyCheck(status, counter)];

/** 单项耗时（秒） */
const formatDuration = (ms: number): string => (ms / 1000).toFixed(3);

/** 是否有可展开的反例 */
const hasCounterExample = (check: VerificationCheck): boolean => {
	return Boolean(check.counter_example);
};

const onStart = () => emit("start-verify");
</script>

<template>
  <div class="formal-verification">
    <!-- Loading 状态：骨架屏 -->
    <Card v-if="loading" class="result-card">
      <CardHeader>
        <CardTitle class="card-title">
          {{ $t("formalVerify.loadingTitle") }}
          <span class="title-hint">{{ $t("formalVerify.titleHint") }}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="skeleton-list">
          <Skeleton class="skeleton-row" />
          <Skeleton class="skeleton-row" />
          <Skeleton class="skeleton-row" />
          <Skeleton class="skeleton-row short" />
        </div>
      </CardContent>
    </Card>

    <!-- 空状态：未验证 -->
    <Card v-else-if="!result" class="result-card empty-card">
      <CardHeader>
        <CardTitle class="card-title">
          {{ $t("formalVerify.title") }}
          <span class="title-hint">{{ $t("formalVerify.titleHint") }}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="empty-state">
          <AlertTriangle class="empty-icon" />
          <p class="empty-text">
            {{ $t("formalVerify.emptyText") }}
          </p>
          <p class="empty-hint">
            {{ $t("formalVerify.emptyHint") }}
          </p>
          <Button variant="outline" @click="onStart">
            <Play />
            {{ $t("formalVerify.startBtn") }}
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- 结果展示 -->
    <Card v-else class="result-card">
      <CardHeader>
        <CardTitle class="card-title">
          {{ $t("formalVerify.resultTitle") }}
          <span class="title-hint">{{ $t("formalVerify.titleHint") }}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <!-- 顶部状态徽章 -->
        <div
          v-if="statusConfig"
          class="status-banner"
          :style="{
            background: statusConfig.bg,
            borderColor: statusConfig.border,
          }"
        >
          <component :is="statusConfig.icon" class="status-icon" :style="{ color: statusConfig.color }" />
          <div class="status-text">
            <div class="status-label" :style="{ color: statusConfig.color }">
              {{ statusConfig.label }}
            </div>
            <div class="status-meta">
              {{ $t("formalVerify.metaTool") }} <strong>{{ result.tool }}</strong>
              · {{ $t("formalVerify.metaDuration", { seconds: totalDurationSec }) }}
            </div>
          </div>
        </div>

        <!-- 统计徽章 -->
        <div class="summary-badges">
          <span class="badge pass">{{ $t("formalVerify.badgeValid", { count: fourCounts.valid }) }}</span>
          <span class="badge fail">{{ $t("formalVerify.badgeFail", { count: fourCounts.fail }) }}</span>
          <span class="badge unknown">{{ $t("formalVerify.badgeUnknown", { count: fourCounts.unknown }) }}</span>
          <span class="badge timeout">{{ $t("formalVerify.badgeTimeout", { count: fourCounts.timeout }) }}</span>
          <span class="badge total">{{ $t("formalVerify.badgeTotal", { count: result.summary.total }) }}</span>
        </div>

        <!-- 错误信息（如契约文件不存在） -->
        <div v-if="result.error" class="error-banner">
          <AlertTriangle class="error-icon" />
          <span>{{ result.error }}</span>
        </div>

        <!-- 检查项列表 -->
        <ul class="check-list">
          <li
            v-for="check in result.checks"
            :key="check.name"
            class="check-item"
            :class="classifyCheck(check.status, check.counter_example)"
          >
            <div
              class="check-header"
              :class="{ clickable: hasCounterExample(check) }"
              @click="hasCounterExample(check) && toggleExpand(check.name)"
            >
              <component
                :is="checkVisual(check.status, check.counter_example).icon"
                class="check-icon"
                :style="{ color: checkVisual(check.status, check.counter_example).color }"
              />
              <span class="check-name">{{ check.name }}</span>
              <span v-if="check.tool" class="check-tool">[{{ check.tool }}]</span>
              <span class="check-status" :style="{ color: checkVisual(check.status).color }">
                [{{ classifyCheck(check.status, check.counter_example).toUpperCase() }}]
              </span>
              <span class="check-duration">({{ formatDuration(check.duration_ms) }}s)</span>
              <component
                v-if="hasCounterExample(check)"
                :is="expanded.has(check.name) ? ChevronDown : ChevronRight"
                class="chevron"
              />
            </div>
            <div
              v-if="hasCounterExample(check) && expanded.has(check.name)"
              class="counter-example"
            >
              <div class="ce-label">
                {{ check.status === "failed" ? $t("formalVerify.ceFailedLabel") : $t("formalVerify.ceSkippedLabel") }}
              </div>
              <pre class="ce-text">{{ check.counter_example }}</pre>
            </div>
          </li>
        </ul>

        <!-- 底部工具说明 -->
        <div class="tool-footer">
          <span class="tool-tag">{{ result.tool }}</span>
          <span class="tool-desc">
            {{ $t("formalVerify.toolDesc") }}
          </span>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.formal-verification {
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-card {
  border-radius: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
}

.title-hint {
  font-size: 12px;
  font-weight: 400;
  color: #6b7280;
}

/* ===== Loading 骨架屏 ===== */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px 0;
}

.skeleton-row {
  height: 28px;
  width: 100%;
}

.skeleton-row.short {
  width: 60%;
}

/* ===== 空状态 ===== */
.empty-card .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 24px 12px;
  text-align: center;
}

.empty-icon {
  width: 40px;
  height: 40px;
  color: #f59e0b;
}

.empty-text {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.empty-hint {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 8px 0;
  max-width: 480px;
}

/* ===== 顶部状态横幅 ===== */
.status-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 8px;
  border: 2px solid;
  margin-bottom: 12px;
}

.status-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.status-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 17px;
  font-weight: 700;
}

.status-meta {
  font-size: 12px;
  color: #6b7280;
}

.status-meta strong {
  color: #1f2937;
}

/* ===== 统计徽章 ===== */
.summary-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}

.badge.pass {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}

.badge.fail {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.badge.unknown {
  background: #fffbeb;
  color: #b45309;
  border-color: #fcd34d;
}

.badge.timeout {
  background: #f3f4f6;
  color: #4b5563;
  border-color: #d1d5db;
}

.badge.total {
  background: #eff6ff;
  color: #1e40af;
  border-color: #bfdbfe;
}

/* ===== 错误横幅 ===== */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 6px;
  color: #92400e;
  font-size: 13px;
  margin-bottom: 12px;
}

.error-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* ===== 检查项列表 ===== */
.check-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.check-item {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px 12px;
  transition: all 0.15s;
}

.check-item.valid {
  border-left: 3px solid #10b981;
}

.check-item.fail {
  border-left: 3px solid #dc2626;
  background: #fef2f2;
}

.check-item.unknown {
  border-left: 3px solid #f59e0b;
  background: #fffbeb;
}

.check-item.timeout {
  border-left: 3px solid #9ca3af;
  background: #f9fafb;
}

.check-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  cursor: default;
}

.check-header.clickable {
  cursor: pointer;
}

.check-header:hover.clickable {
  background: #f9fafb;
}

.check-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.check-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  min-width: 200px;
}

.check-tool {
  font-family: 'Consolas', monospace;
  font-size: 11px;
  font-weight: 600;
  background: #0F1623;
  color: #F0F4F8;
  padding: 1px 6px;
  border-radius: 3px;
}

.check-status {
  font-family: 'Consolas', monospace;
  font-size: 12px;
  font-weight: 700;
}

.check-duration {
  font-family: 'Consolas', monospace;
  font-size: 11px;
  color: #6b7280;
}

.chevron {
  width: 14px;
  height: 14px;
  color: #9ca3af;
  flex-shrink: 0;
}

/* ===== 反例展示 ===== */
.counter-example {
  margin-top: 8px;
  padding: 10px 12px;
  background: #1e1e1e;
  border-radius: 4px;
  border: 1px solid #374151;
}

.check-item.unknown .counter-example,
.check-item.timeout .counter-example {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.ce-label {
  font-size: 11px;
  font-weight: 600;
  color: #fca5a5;
  margin-bottom: 4px;
}

.check-item.unknown .ce-label,
.check-item.timeout .ce-label {
  color: #6b7280;
}

.ce-text {
  margin: 0;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}

.check-item.unknown .ce-text,
.check-item.timeout .ce-text {
  color: #4b5563;
}

/* ===== 底部工具说明 ===== */
.tool-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}

.tool-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: #0F1623;
  color: #4ec9b0;
  font-family: 'Consolas', monospace;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
}

.tool-desc {
  font-size: 11px;
  color: #6b7280;
  line-height: 1.4;
}
</style>
