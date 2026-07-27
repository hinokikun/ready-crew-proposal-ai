# Known Limitations

- Slide Intent is deterministic and does not call an LLM.
- It does not inspect actual rendered slides.
- It does not create diagrams, charts, layout, colors, fonts, or PowerPoint files.
- It does not validate final visual quality.
- Some upstream Message Designer fixture text may be synthetic and should be reviewed before customer-facing use.
- Chart selection is intentionally conservative when numeric evidence is missing.
- Image-dominant slides use placeholder intent only and do not assume external image availability.
