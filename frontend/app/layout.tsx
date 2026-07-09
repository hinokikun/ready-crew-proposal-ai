import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI営業秘書",
  description: "案件メールからWeb制作提案書の初稿を作成するAI営業アシスタント"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="app-body">{children}</body>
    </html>
  );
}
