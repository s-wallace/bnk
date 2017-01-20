TOP=`git rev-parse --show-toplevel`

coverage:
	coverage run -m unittest discover -t ${TOP} test "test*.py"

report: coverage
	coverage report -m

test:
	python -m unittest discover -t ${TOP} test "test*.py"

.PHONY: coverage report test
