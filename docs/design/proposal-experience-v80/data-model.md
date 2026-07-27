# Data Model

## 追加されたFrontend state

- `experienceView`
- `isExperienceSidebarCollapsed`
- `isExperienceMobileOpen`
- `selectedPresentationTemplate`

## localStorage

- `ready-crew-v80-prompt-builder`
- `ready-crew-v80-story-plan`

## API payload

`/api/download-pptx`に後方互換の任意項目を追加します。

```json
{
  "design_template": "corporate_clean",
  "brand_settings": {}
}
```

既存クライアントがこれらを送らない場合も動作します。

