a2t2b2a = """12-30-2001 open a
           01-01-1900 open Assets

           from 12-31-2001 until 12-31-2001
           ---
           Assets -> a  100

           12-31-2001 balances
           ---
           a      100
           Assets 100

           from 01-01-2002 until 12-31-2002
           ---
           Assets -> a  -50

           12-31-2002 balances
           ---
           a      100
           Assets 150
           """

a3t3b3a = """12-30-2001 open a
             12-30-2001 open b
            01-01-1900 open Assets

           from 12-31-2001 until 12-31-2001
           ---
           Assets -> a  200
           Assets -> b  200

           12-31-2001 balances
           ---
           a      100
           b      200
           Assets 100

           from 01-01-2002 until 12-31-2002
           ---
           Assets -> a  -50

           from 04-01-2002 until 06-30-2002
           ---
           a  ->  b   50

           12-31-2002 balances
           ---
           a      200
           b      300
           Assets 150
           """

a5t20b20a ="""
  09-01-2009 open a
  12-31-2010 open b
  12-31-2010 open c
  01-01-2012 open d
  05-20-2012 open e
  01-01-1900 open Assets

  during Q1-2011
  ---
  Assets -> a    10000
  Assets -> b    20000
  Assets -> c    10000

  03-30-2011 balances
  ---
  a  10100
  b  20100
  c   9900

  during Q2-2011
  ---
  Assets -> a  1000

  06-30-2011 balances
  ---
  a  11100
  b  20150
  c   9800

  during Q3-2011
  ---
  c -> a  1000
  Assets -> b 1000

  09-30-2011 balances
  ---
  a   12200
  b   21200
  c    8850

  during Q4-2011
  ---
  Assets -> a 1000
  Assets -> c 2000

  12-31-2011 balances
  ---
  a   13200
  b   21300
  c   10000

  during Q1-2012
  ---
  Assets -> d 20000
  a -> Assets  3000
  Assets -> b  1000

  balances 03-30-2012
  ---
  a  10300
  b  22400
  c  10200
  d  20100

  balances 06-30-2012
  ---
  a 10350
  b 22450
  c 10300
  d 20300

  balances 09-30-2012
  ---
  a 10400
  b 22500
  c 10300
  d 20300

  balances 12-31-2012
  ---
  a 10450
  b 22550
  c 10400
  d 20400
  """
