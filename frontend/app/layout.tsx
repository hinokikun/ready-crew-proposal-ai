import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI営業秘書",
  description: "案件メールから提案準備、見積、商談確認までを支援する社内AIワークスペース"
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
