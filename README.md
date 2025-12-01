# DiscourseLens

## Versioning & Automation

Local development:
- Use normal `git add / commit / push`.
- If you want version + changelog updates:
  - `python tools/bump_version.py`
  - `python tools/gen_changelog.py`

GitHub Actions:
- Auto Backup Release runs nightly and produces a ZIP + Release based on `version.py`.
- Auto Commit on Push is now manual; trigger via Actions UI when you want CI-driven version bump + changelog.
