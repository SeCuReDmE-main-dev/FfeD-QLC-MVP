# Design Asset Intake

Design assets are tracked through `assets/Mascotte/MANIFEST.json`. Before closing a design session:

1. Run `git status --short assets`.
2. Add new logo, font schema, mascot, or full-logo files to the manifest.
3. Run `python -m pytest tests/test_mascotte_manifest.py`.
4. Commit the binary asset and the manifest together.

The manifest is only local asset governance. It is not a trademark, licensing, or security certification.
