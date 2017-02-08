TOP=`git rev-parse --show-toplevel`

coverage:
	coverage run -m unittest discover -t ${TOP} bnk.tests "test*.py"

report: coverage
	coverage report -m

test:
	python -m unittest discover -t ${TOP} bnk.tests "test*.py"

run:	test
	@echo "press a key to continue"
	@read
	./run-readme-report.py

cleaner:
	find ${TOP} -name "*~" | xargs rm
	find ${TOP} -name "*__pycache__" | xargs rm -r	

lint-main:
	pylint bnk --ignore=parsetab.py,tests

lint-all:
	pylint bnk --ignore=parsetab.py

.PHONY: coverage report test cleaner
