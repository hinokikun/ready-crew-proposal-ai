import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ready Crew Proposal AI",
  description: "Ready Crewの案件概要からWeb制作提案書の初稿を生成するMVP"
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
