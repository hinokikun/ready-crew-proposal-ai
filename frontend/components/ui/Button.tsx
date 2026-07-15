"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ReactNode;
  isLoading?: boolean;
  variant?: ButtonVariant;
};

export function Button({ children, className = "", disabled, icon, isLoading = false, type = "button", variant = "primary", ...props }: ButtonProps) {
  const classNames = ["pp-button", `pp-button-${variant}`, className].filter(Boolean).join(" ");
  return (
    <button className={classNames} disabled={disabled || isLoading} type={type} {...props}>
      {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : icon}
      <span>{children}</span>
    </button>
  );
}
