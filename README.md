
# bnk

Simple (personal) financial analysis with incomplete information

## Motivation

Tracking small transactions is a time consuming task. But
understanding and monitoring the performance of your investments is
important. bnk is is intended to help users examine accounts at periodic
intervals (e.g., quarterly).  Its critical feature is that instead of
forcing users to enter individual (small) transactions spread over days or
months, users can enter fewer (larger) transactions by giving up some knowledge
of when, precisely, the transactions occurred.

## How it works

bnk reads financial records stored in a plain text file.  Records indicate:
 - account names
 - account opening and closing dates
 - account balances at points in time
 - transfer of funds between accounts during a window of time

From this information, bnk computes how accounts change in value
between two points in time and how much of that change is attributable
to the explicit transfer of funds as opposed to 'gain' (e.g., via
dividends, interest, etc). This also allows bnk to compute the
internal rate of return (sometimes called 'personal rate of return')
on individual accounts to help evaluate what 'actual' growth is taking
place. This is in contrast to most quarterly/annual statements from
investments which don't take into account the timing of transactions
or management fees.

## An example

Below is a short plain text file representing account records:

```
  12-31-2000 open AlpineFund
  12-31-2000 open BankFund
  01-01-1900 open Assets

  from 01-31-2001 until 01-31-2001
  ---
  Assets -> AlpineFund  200
  Assets -> BankFund    200

  12-31-2001 balances
  ---
  AlpineFund      220
  BankFund        230

  from 01-01-2002 until 12-31-2002
  ---
  Assets -> AlpineFund  -50

  from 04-01-2002 until 06-30-2002
  ---
  AlpineFund  ->  BankFund   50

  12-31-2002 balances
  ---
  AlpineFund      128
  BankFund        290
```

Note in the example above that transactions (moving money from one account to another)
occur within a window of time (e.g., a month long window).  This window can be
arbitrarily precise. Note also that balances are obtained at specific moments in time.
That is, their timing is precise, while transaction timing may be arbitrarily imprecise.
Transaction windows are limited only in that they cannot span a moment in which the
balance of that specific account is measured.  So, for example, if you know that the
balance of an account is 100 dollars on 06-30-2001, then you should also know which
transactions occurred prior to that date and which occurred after that date. And there
should be no need for uncertainty to extend through that moment.

Allowing transactions to span a region of time can simplify bookkeeping in that users
can aggregate transactions to a monthly or quarterly amount. It has the side effect of
making some calculations imprecise.  So, for example, calculating the internal rate of
return (performance) will produce some uncertainty. bnk displays this uncertainty with
range values when needed.

For example, given the records above, bnk will generate reports over arbitrary periods
like those below.  Note how the Performance report indicates a range of possible
internal rates of returns based on the uncertainty in each account's transaction timing.

```
Performance Overview
------------------------------------------------------------------------------------------
Account                                       2002                2001            Lifetime
------------------------------------------------------------------------------------------
AlpineFund                       ^ (  4.10,  6.02)   v ( 10.98, 10.98)   v (  7.54,  8.98)
BankFund                         v (  3.74,  3.92)   ^ ( 16.50, 16.50)   ^ (  9.17,  9.43)



Gain Report
---------------------------------------------------------------------------
Account                                  2002           2001       Lifetime
---------------------------------------------------------------------------
AlpineFund                              8.00          20.00          28.00
BankFund                               10.00          30.00          40.00
---------------------------------------------------------------------------
Total:                                 18.00          50.00          68.00
```
