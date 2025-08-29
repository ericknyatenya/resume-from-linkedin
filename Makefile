
## Makefile (nice-to-have)
```makefile
VENV=.venv
PY=$(VENV)/bin/python

init:
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate; pip install -r requirements.txt

gen:
	$(PY) -m src.resume_from_linkedin.cli LinkedIn_Profile.pdf -o resume.md

test:
	$(PY) -m pytest -q

