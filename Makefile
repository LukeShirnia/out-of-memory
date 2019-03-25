export TZ=Europe/London

test tests: unittests pycodestyle

unittests:
	@PYTHONPATH=. pytest --cov=oom_analyzer --cov-report xml:cobertura.xml --cov-report term-missing

pycodestyle:
	@pycodestyle oom_analyzer.py

pylint:
	@pylint --rcfile=.pylintrc oom_analyzer.py -j 4 -f parseable -r n 

clean:
	find . -name \*.pyc -delete
	rm -rf __pycache__ .cache .coverage .pytest_cache
	rm -rf tests/__pycache__ tests/.cache tests/.coverage tests/.pytest_cache
