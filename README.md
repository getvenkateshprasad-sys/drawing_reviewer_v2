# drawing_reviewer_v2
V2 - Smart overlay dialogue boxes, improved fonts and UI

## Version History

### V2.0.2 - Enhanced Analysis Engine (Current)
**Date**: December 2024

**New Features**: 9 additional engineering drawing validation rules based on international standards

**Enhanced Rules**:
1. **Projection Method Indicator** - Verifies 1st or 3rd angle projection symbol presence (ISO standard)
2. **Scale Verification** - Ensures scale specification is clearly indicated (e.g., 1:1, 1:2)
3. **Surface Finish Symbols** - Checks for Ra/Rz surface roughness values on part drawings
4. **Units Specification** - Validates clear declaration of measurement units (mm/inches)
5. **Angular Tolerance** - Flags angular dimensions without tolerance specifications
6. **Thread Callout Completeness** - Verifies thread specifications include tolerance class (6H, 6g, 2B, etc.)
7. **GD&T Datum References** - Ensures geometric tolerancing includes proper datum references
8. **Chamfer/Fillet Notation** - Checks for unambiguous chamfer specifications
9. **Section View Labeling** - Validates section views include scale specifications

**Standards Referenced**:
- Manual of Engineering Drawing (Simmons & Maguire)
- Engineering Drawing (N.D. Bhatt)
- Engineering Drawing for Manufacture (Griffiths)

**Analysis Coverage**: 15 comprehensive rules (6 original + 9 enhanced)

---

### V2.0.1 - UI Improvements
**Date**: 2 days ago
- Removed blocking overlay bubbles
- Implemented non-blocking sidebar detail panel
- Added numbered dot markers on canvas
- Improved user experience for drawing review

### V2 - Smart Overlay
**Date**: Initial V2 release
- Smart overlay dialogue boxes
- Improved fonts and UI
- Interactive review interface

## Features
- **Local execution**: Privacy-focused, runs on localhost:5000
- **PDF analysis**: Automated rule-based anomaly detection
- **Interactive review**: Accept, reject, or edit suggested changes
- **Export capability**: Generate reviewed PDF with approved modifications
- **Non-blocking UI**: Sidebar detail panel maintains visibility of drawings

## Installation

```bash
pip install -r requirements.txt
python server.py
```

Open http://localhost:5000 in your browser.

## Usage
1. Upload PDF manufacturing drawing
2. Click "Analyze" to run validation engine
3. Review findings in sidebar detail panel
4. Click numbered dots to view specific anomalies
5. Accept, reject, or edit each suggestion
6. Export final reviewed PDF
