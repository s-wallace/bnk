
#PYTHONPATH=myrecords python -m bnk --carry-last --report myannual myrecords/records-normalized-tweaked.r
python -m bnk  --carry-forward 365 --report bnk.tests.samplereport bnk/tests/records/5accounts-2000-2016.r
