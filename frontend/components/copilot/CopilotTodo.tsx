"use client";

import { memo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import type { CopilotTodoItem } from "./types";

type CopilotTodoProps = {
  todos: CopilotTodoItem[];
  onOpenPanel: (panelId: string) => void;
};

export const CopilotTodo = memo(function CopilotTodo({ todos, onOpenPanel }: CopilotTodoProps) {
  const [doneIds, setDoneIds] = useState<string[]>([]);
  const visibleTodos = todos.filter((todo) => !doneIds.includes(todo.id));

  return (
    <section className="copilot-todo" aria-label="AI ToDo">
      <div className="copilot-section-title">
        <span>人がやること</span>
        <small>{visibleTodos.length}件</small>
      </div>
      {visibleTodos.length ? (
        <div className="copilot-todo-list">
          {visibleTodos.map((todo) => (
            <label key={todo.id}>
              <input type="checkbox" onChange={() => setDoneIds((current) => [...current, todo.id])} />
              <span>{todo.label}</span>
              <button type="button" onClick={() => onOpenPanel(todo.targetPanelId)}>開く</button>
            </label>
          ))}
        </div>
      ) : (
        <p className="copilot-empty">
          <CheckCircle2 size={15} aria-hidden="true" />
          現時点のToDoは完了しています。
        </p>
      )}
    </section>
  );
});
