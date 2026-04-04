BACKEND_VENV_PYTHON := backend/.venv/bin/python

.PHONY: backend-setup-minimal backend-setup-full backend-run backend-test

backend-setup-minimal:
	python3 backend/tools/bootstrap_env.py minimal

backend-setup-full:
	python3 backend/tools/bootstrap_env.py full

backend-run:
	@test -x $(BACKEND_VENV_PYTHON) || (echo "backend/.venv is missing. Run 'make backend-setup-minimal' or 'make backend-setup-full' first." && exit 1)
	$(BACKEND_VENV_PYTHON) -m uvicorn app.main:app --reload --app-dir backend

backend-test:
	@test -x $(BACKEND_VENV_PYTHON) || (echo "backend/.venv is missing. Run 'make backend-setup-minimal' or 'make backend-setup-full' first." && exit 1)
	$(BACKEND_VENV_PYTHON) -m pytest backend/tests
