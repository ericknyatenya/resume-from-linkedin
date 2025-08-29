# Resume from LinkedIn

Generate a clean Markdown resume from your LinkedIn PDF export.

## Quick Start
```bash
cd resume-from-linkedin
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate resume.md from your LinkedIn PDF
python -m src.resume_from_linkedin.cli ~/Downloads/LinkedIn_Profile.pdf -o resume.md

# Optional: convert to PDF (requires pandoc installed)
# pandoc resume.md -o resume.pdf

