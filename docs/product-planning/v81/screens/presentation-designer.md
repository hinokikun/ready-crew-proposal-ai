# SCR-090 Presentation Designer

## Purpose

提案内容に合うテンプレート、配色、レイアウト方針を選ぶ。

## Layout

```text
[Template cards]
[Preview]
[Quality score]
[Brand settings summary]
[Apply to PPTX]
```

## Template Choices

Corporate Clean, Modern Dark, Creative Agency, Executive Minimal, Data Driven, Warm Professional, Japanese Business, Bold Vision.

## Current Implementation

`design_template`をPPTX requestへ送信し、Backendでテーマ解決する。Brand settingsは受け取り可能だが全ページ反映は限定。

