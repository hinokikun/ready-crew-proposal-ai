import type { PromptVersion } from "@/types/app";

export function promptStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "下書き",
    testing: "テスト中",
    active: "有効",
    archived: "保管"
  };
  return labels[status] ?? status;
}

export function groupPromptVersions(versions: PromptVersion[]) {
  return versions.reduce<Record<string, PromptVersion[]>>((groups, version) => {
    const key = version.prompt_name || "unknown";
    groups[key] = groups[key] ? [...groups[key], version] : [version];
    return groups;
  }, {});
}

export function sortPromptVersions(versions: PromptVersion[]) {
  return [...versions].sort((a, b) => {
    if (a.prompt_name !== b.prompt_name) {
      return a.prompt_name.localeCompare(b.prompt_name);
    }
    return b.id - a.id;
  });
}
