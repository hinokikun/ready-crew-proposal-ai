import type { HTMLAttributes, ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  tone?: "default" | "info" | "success" | "warning" | "danger";
};

export function Card({ children, className = "", tone = "default", ...props }: CardProps) {
  return (
    <article className={["pp-card", `pp-card-${tone}`, className].filter(Boolean).join(" ")} {...props}>
      {children}
    </article>
  );
}
