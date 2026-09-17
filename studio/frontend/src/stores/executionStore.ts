import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { i18n } from "@/i18n";
import type { ExecutionProfile, ExecutionProfileId } from "@/types/execution";

/** localStorage key：execution profile 唯一持久化 key */
export const EXECUTION_PROFILE_STORAGE_KEY = "skyforge-execution-profile";

/**
 * 翻译 data 层标签：键可解析时返回译文，
 * 键缺失（t 返回键路径本身）时回退到中文默认文案。
 * 做成函数以便在 locale 模块加载后重新解析。
 */
function dataT(key: string, fallback: string): string {
	// 先用 te() 检查 key 是否存在，避免 t() 内部打印 intlify 缺失警告
	if (!i18n.global.te(key)) return fallback;
	const resolved = i18n.global.t(key);
	return resolved === key ? fallback : resolved;
}

/** profile 的静态元信息（不含 label，label 通过 computed 响应式解析） */
const PROFILE_META: Record<
	ExecutionProfileId,
	Omit<ExecutionProfile, "label">
> = {
	cloud: {
		id: "cloud",
		available: true,
		source: "live",
		provider: "server-managed",
	},
	local: {
		id: "local",
		available: true,
		source: "live",
		provider: "OpenAI-compatible",
	},
};

const PROFILE_FALLBACK_LABELS: Record<ExecutionProfileId, string> = {
	cloud: "云 API · 实时/回放",
	local: "本地模型 · 实时/回放",
};

const PROFILE_KEYS: Record<ExecutionProfileId, string> = {
	cloud: "data.status.executionProfile.cloud",
	local: "data.status.executionProfile.local",
};

export const useExecutionStore = defineStore("execution-profile", () => {
	const saved = localStorage.getItem(EXECUTION_PROFILE_STORAGE_KEY);
	const profileId = ref<ExecutionProfileId>(
		saved === "cloud" || saved === "local" ? saved : "cloud",
	);

	/** 响应式解析 profile 标签——locale 模块加载后自动更新 */
	const profiles = computed<ExecutionProfile[]>(() =>
		(Object.keys(PROFILE_META) as ExecutionProfileId[]).map((id) => ({
			...PROFILE_META[id],
			label: dataT(PROFILE_KEYS[id], PROFILE_FALLBACK_LABELS[id]),
		})),
	);

	const profile = computed<ExecutionProfile>(
		() => profiles.value.find((p) => p.id === profileId.value) ?? profiles.value[0],
	);

	function setProfile(id: ExecutionProfileId) {
		profileId.value = id;
		localStorage.setItem(EXECUTION_PROFILE_STORAGE_KEY, id);
	}

	return { profileId, profile, profiles, setProfile };
});
