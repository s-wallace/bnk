TOP=`git rev-parse --show-toplevel`

coverage:
	coverage run -m unittest discover -t ${TOP} bnk.tests "test*.py"

report: coverage
	coverage report -m

test:
	python -m unittest discover -t ${TOP} bnk.tests "test*.py"

cleaner:
	find ${TOP} -name "*~" | xargs rm

lint-main:
	pylint bnk --ignore=parsetab.py,tests

lint-all:
	pylint bnk --ignore=parsetab.py

.PHONY: coverage report test cleaner
