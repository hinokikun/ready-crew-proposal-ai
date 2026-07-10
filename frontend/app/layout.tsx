import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Workspace",
  description: "AI社員が協力して提案準備を進める社内業務支援ワークスペース"
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
