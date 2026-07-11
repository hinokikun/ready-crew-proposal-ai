"use client";

import { memo, useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { CrmProject } from "@/types/app";

type SearchBarProps = {
  projects: CrmProject[];
  onOpenProject: () => void;
};

export const SearchBar = memo(function SearchBar({ projects, onOpenProject }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const trimmedQuery = query.trim().toLowerCase();

  const results = useMemo(() => {
    if (!trimmedQuery) return [];
    return projects
      .filter((project) => {
        const target = [
          project.id,
          project.name,
          project.customer_name,
          project.status,
          project.next_action,
          project.summary
        ]
          .join(" ")
          .toLowerCase();
        return target.includes(trimmedQuery);
      })
      .slice(0, 5);
  }, [projects, trimmedQuery]);

  return (
    <section className="operations-search-panel" id="operations-search" aria-label="案件検索">
      <label>
        <Search size={17} aria-hidden="true" />
        <input
          onChange={(event) => setQuery(event.target.value)}
          placeholder="案件名、顧客名、担当者、Project IDで検索"
          type="search"
          value={query}
        />
      </label>
      {results.length ? (
        <div className="operations-search-results">
          {results.map((project) => (
            <button key={project.id} type="button" onClick={onOpenProject}>
              <strong>{project.name}</strong>
              <span>{project.customer_name || "顧客名未設定"} / ID: {project.id}</span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
});
