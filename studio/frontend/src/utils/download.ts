/**
 * 触发浏览器下载文本文件。
 *
 * 统一 Blob + objectURL + anchor 下载逻辑，避免在多个视图中重复实现。
 * 需要 UTF-8 BOM（如 Excel 打开的 CSV/TXT）时，由调用方在 content 前拼接 "\uFEFF"。
 *
 * @param filename 下载文件名
 * @param content 文本内容
 * @param mime MIME 类型（默认纯文本）；内部自动追加 ;charset=utf-8
 */
export function downloadTextFile(
	filename: string,
	content: string,
	mime = "text/plain",
): void {
	const blob = new Blob([content], { type: `${mime};charset=utf-8` });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}
