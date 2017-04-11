clean:
	rm -rf build dist .tox .cache .eggs *.egg-info .coverage .DS_Store
	find . -name '*.pyc' -exec rm '{}' ';'

sort:
	isort -rc shopit example -s migrations -l 119

coverage:
	coverage erase
	coverage run -m pytest
	coverage report
