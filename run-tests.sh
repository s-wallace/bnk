TOP=`git rev-parse --show-toplevel`
python -m unittest discover -t ${TOP} bnk.tests "test*.py"
