.PHONY: install test samples app

install:
	python -m pip install -e ".[dev]"

test:
	pytest

samples:
	ops-narrative samples

app:
	streamlit run src/ops_narrative/app.py --server.port 8741 --server.address 0.0.0.0
