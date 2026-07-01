# Assets

This directory holds static brand and presentation assets used in documentation and the README.

## Contents (add as you build)

| File | Description |
|---|---|
| `aws-architecture-banner.png` | Architecture diagram exported as PNG from draw.io |
| `pipeline-flow.png` | Simplified pipeline flow diagram for README |
| `logo.svg` | Project logo or icon (optional) |

## Generating the Architecture PNG

1. Open `architecture/architecture.drawio` in [draw.io](https://app.diagrams.net/)
2. File → Export As → PNG
3. Set resolution to 2x for retina-quality output
4. Save as `assets/aws-architecture-banner.png`
5. Reference in README.md with:
   ```markdown
   ![Architecture](assets/aws-architecture-banner.png)
   ```
