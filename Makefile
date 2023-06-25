.PHONY: test

test:
	poetry run python -m pytest -s -v -vv -q \
	--maxfail=1 \
	--cov=./src/ \
	--cov-report term \
	--cov-report xml:test-reports/coverage.xml \
	--cov-fail-under=51 \
	--cache-clear \
	--junitxml=test-reports/report.xml \
	--durations=7

run: 
	poetry run python -m src.main

clean-data: 
	rm -rfv data/*/*
