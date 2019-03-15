export TZ=Europe/London

test tests: unittests

unittests:
	@PYTHONPATH=. pytest --cov=oom_analyzer --cov-report xml:cobertura.xml --cov-report term-missing

clean:
	find . -name \*.pyc -delete
	rm -rf __pycache__ .cache .coverage
