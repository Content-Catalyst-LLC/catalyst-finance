# Export Specification

The Catalyst Finance export should preserve both calculated results and interpretive context.

## Required sections

- `project`: initiative name and category
- `inputs`: cost, benefit, time horizon, discount rate, emissions, confidence, risk
- `results`: NPV, payback, ROI estimate, benefit-cost ratio, carbon cost per ton, risk-adjusted score
- `interpretation`: risk level, review flags, decision note
- `metadata`: generated timestamp and tool/version notes

## Why export matters

Financial scenario work is often copied into slides or spreadsheets without the assumptions that produced it. The export is designed to keep the reasoning trail attached to the result.
