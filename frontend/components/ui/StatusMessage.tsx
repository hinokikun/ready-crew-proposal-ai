"use client";

import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type StatusMessageProps = {
  type: "info" | "success" | "error";
  title: string;
  children?: ReactNode;
};

export function StatusMessage({ type, title, children }: StatusMessageProps) {
  const Icon = type === "error" ? AlertCircle : type === "success" ? CheckCircle2 : Info;
  return (
    <div className={`status-message status-message-${type}`} role={type === "error" ? "alert" : "status"}>
      <Icon size={18} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {children}
      </div>
    </div>
  );
}
