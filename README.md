# README

This repository includes responses to the `Python` and `SQL` question sets. The relevant files are:

* `stock_performance.py`: this file contains the `Python` class `StockPerformance` and the methods that compute the five financial statistics specified in the assessment prompt, as well as a function `unittests` that tests all five methods in `StockPerformance` using two small sample datasets. When `stock_performance.py` is run from the command line, the unit tests are run and the results printed to the console. The five methods in question are:
  + `calc_total_returns`
  + `calc_cagrs`
  + `calc_alphas`
  + `calc_betas`
  + `calc_sharpe_ratios`
* `Entelligent SQL Assessment Answers.pdf`: this file contains `SQL` queries that attempt to answer the questions specified in the assessment prompt.
  
 There is a sixth method in the `StockPerformance` class, `capm_regression`, that is a helper function called by the two CAPM methods. 
 
 The assumptions I made in implementing the `StockPerformance` class are documented in the code, but it's worth noting that my code relies on the S&P 500 return series in the file `sp50_returns.csv` (total returns downloaded from FactSet), as S&P returns weren't available in the sample database (at least not by ISIN) and I wanted a reasonable benchmark to test my CAPM related methods. Assuming benchmark returns are also available in the same database tables as the stock returns, it would be easy to modify my code to pull the benchmark returns in the same manner as the stock returns.
 
 The `SQL` queries should be self explanatory. The assumptions I made are listed in the PDF.
 
 
