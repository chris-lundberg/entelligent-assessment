######################################################################
# The `StockPerformance` class implements methods for computing 
# the five financial statistics specified in the project prompt
######################################################################

import os
import psycopg2
from datetime import datetime as dt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Class Definition
class StockPerformance:
    
    """
    This class contains methods for computing various financial metrics:
    
      __init__: this method is required to initialize the class. This method
        queries the sample database for daily returns data on the specified
        tickers and benchmark for the specified date range. It is assumed that
        the desired benchmark is also available in the database. The returns in 
        the database are stated in percentage terms, so upon initialization, this method
        transforms the returns by dividing them by 100 to facilitate computations 
        performed by the other methods in this class.

      capm_regression: this method is a helper function for the two CAPM methods.
        The specified risk free rate is subtracted from both the benchmark and stock returns.

      calc_total_returns: this method computes the compound total return for each
        ticker in the pandas dataframe `daily_returns` and returns a pandas dataframe
        containing the tickers and total returns.

      calc_cagrs: this method computes the compound annual growth rate for each
        ticker in the pandas dataframe `daily_returns` and returns a pandas dataframe
        containing the tickers and compound annual growth rates.

      calc_betas: this method calls the helper function `capm_regression` and
        returns a pandas dataframe containing the tickers and CAPM betas.

      calc_alphas: this method calls the helper function `capm_regression` and
        returns a pandas dataframe containing the tickers and CAPM alphas.

      calc_sharpe_ratios: this method computes the sharpe ratio for each ticker
        in the pandas dataframe `daily_returns` and returns a pandas dataframe
        containing the tickers and sharpe ratios. The specified risk free rate is 
        subtracted from the mean of the daily returns. Note that these are daily 
        sharpe ratios, and that annualized values can be computed by multiplying 
        the daily values by the square root of 252. 
    """
    
    def __init__(self, tickers, start_date, end_date, bench_returns_filename):
    
        # Query database for stock and benchmark returns data
        con = psycopg2.connect('dbname=postgres user=epic_einstein \
                               password=#pbscbg13! host=35.188.222.122 \
                               port=5432')
        db_cursor = con.cursor()
        db_query = db_cursor.execute("""SELECT p_date, 
                                   ticker_region, one_day_pct
                                   FROM security_reference 
                                   LEFT JOIN daily_returns 
                                   ON security_reference.isin_code = daily_returns.isin_code
                                   WHERE ticker_region IN %s
                                   AND p_date>=%s
                                   AND p_date<=%s""", 
                                   (tickers, start_date, end_date))
        
        # Transform data to seperate out benchmark returns
        daily_returns = pd.DataFrame(db_cursor.fetchall(),
                                     columns=['date', 'ticker', 'return'])
        daily_returns['return'] = daily_returns['return'] / 100
        daily_returns['date'] = pd.to_datetime(daily_returns['date'])
        bench_returns = pd.read_csv(bench_returns_filename)
        bench_returns = bench_returns[['date', 'benchmark', 'bench_return']]
        bench_returns['date'] = pd.to_datetime(bench_returns['date'])
        daily_returns = daily_returns.merge(bench_returns, on='date', 
                                            how='left').dropna(subset=['bench_return'])
        con.close()
        
        # Set state variables 
        self.days_in_year = 365.25
        self.risk_free_rate = 0.00007
        self.tickers = tickers
        self.start_date = dt.strptime(start_date, '%Y-%m-%d')
        self.end_date = dt.strptime(end_date, '%Y-%m-%d')
        self.interval = (self.end_date - self.start_date).days + 1
        self.daily_returns = daily_returns
     
    # Helper function for CAPM methods
    def capm_regression(self, data, port_returns, bench_returns, stat):
        
        reg = LinearRegression()
        X = data[['bench_return']] - self.risk_free_rate
        y = data[['return']] - self.risk_free_rate
        reg.fit(X, y)
        
        if stat == 'beta':
            return float(reg.coef_)
        elif stat == 'alpha':
            return float(reg.intercept_)
        
    def calc_total_returns(self):
        
        returns_df = pd.DataFrame(self.daily_returns.groupby(['ticker'])
                                  ['return'].apply(lambda x: (1 + x).prod() - 1))
        returns_df.columns = ['total_return']
        
        return returns_df
        
    def calc_cagrs(self):
        
        cagr_df = self.calc_total_returns()
        cagr_df['cagr'] = (1 + cagr_df['total_return']) ** (self.days_in_year / self.interval) - 1
        cagr_df = cagr_df[['cagr']]
        
        return cagr_df
        
    def calc_alphas(self):
        
        alpha_df = self.daily_returns.groupby(['ticker'])
        alpha_df = alpha_df.apply(self.capm_regression, 'return', 'bench_return', 'alpha')
        alpha_df = pd.DataFrame(alpha_df)
        alpha_df.columns = ['capm_alpha']
        
        return alpha_df
        
    def calc_betas(self):
        
        beta_df = self.daily_returns.groupby(['ticker'])
        beta_df = beta_df.apply(self.capm_regression, 'return', 'bench_return', 'beta')
        beta_df = pd.DataFrame(beta_df)
        beta_df.columns = ['capm_beta']
        
        return beta_df
        
    def calc_sharpe_ratios(self):
        
        sharpe_df = self.daily_returns.groupby(['ticker'])['return']
        sharpe_df = sharpe_df.apply(lambda x: (np.mean(x) - self.risk_free_rate) / np.std(x))
        sharpe_df = pd.DataFrame(sharpe_df)
        sharpe_df.columns = ['sharpe_ratio']
        
        return sharpe_df

######################################################################
# All code below is used for unit testing
# Data for the test cases is from FactSet and Yahoo! Finance
######################################################################

def unittests(test_case, start_date, end_date, benchmark_returns_filename):
    
    """
    This function takes a given test case and tests all five
    methods from the `StockPerformance` class that compute 
    and return financial statistics.
    """
    
    # Initialize flag and `StockPerformance` object
    passing = True
    stocks = StockPerformance(tuple(list(test_case['ticker'])),
                              start_date, end_date,
                              benchmark_returns_filename)
    # Total Return Test
    try:
        actual = np.array(stocks.calc_total_returns().round(3)[['total_return']])
        expected = np.array(test_case.round(4)[['total_return']])
        np.testing.assert_allclose(actual, expected, rtol=1e-02)
    except AssertionError:
        print('Total Return Test Failed')
        passing = False
        
    # CAGR Test
    try:
        actual = np.array(stocks.calc_cagrs().round(3)[['cagr']])
        expected = np.array(test_case.round(4)[['cagr']])
        np.testing.assert_allclose(actual, expected, rtol=1e-02)
    except AssertionError:
        print('CAGR Test Failed')
        passing = False
        
    # Alpha Test
    try:
        actual = np.array(stocks.calc_alphas().round(4)[['capm_alpha']])
        expected = np.array(test_case.round(4)[['capm_alpha']])
        np.testing.assert_allclose(actual, expected, rtol=1e-04)
    except AssertionError:
        print('Alpha Test Failed')
        passing = False
        
    # Beta Test
    try:
        actual = np.array(stocks.calc_betas().round(2)[['capm_beta']])
        expected = np.array(test_case.round(4)[['capm_beta']])
        np.testing.assert_allclose(actual, expected, rtol=1e-02)
    except AssertionError:
        print('Beta Test Failed')
        passing = False
        
    # Sharpe Ratio Test
    try:
        actual = np.array(stocks.calc_sharpe_ratios().round(2)[['sharpe_ratio']])
        expected = np.array(test_case.round(4)[['sharpe_ratio']])
        np.testing.assert_allclose(actual, expected, rtol=1e-02)
    except AssertionError:
        print('Sharpe Ratio Test Failed')
        passing = False
        
    if passing:
        print('All Tests Passed!')
        
    return passing

# Test cases
test_case_one = pd.DataFrame({'ticker':['AAPL-US', 'AMZN-US', 'MSFT-US'],
                            'total_return':[0.347, 0.282, 0.219],
                            'cagr':[0.491, 0.395, 0.305],
                            'capm_beta':[1.33, 1.14, 1.19],
                            'capm_alpha':[0.0007, 0.0006, 0.0002],
                            'sharpe_ratio':[0.14, 0.12, 0.12]})

test_case_two = pd.DataFrame({'ticker':['INTC-US', 'PG-US', 'V-US'],
                            'total_return':[-0.109, 0.280, 0.054],
                            'cagr':[-0.169, 0.486, 0.088],
                            'capm_beta':[1.35, 0.40, 1.36],
                            'capm_alpha':[-0.0004, 0.0016, 0.0006],
                            'sharpe_ratio':[-0.03, 0.13, 0.02]})

# Only run the tests automatically if this file was executed from the command line.
if __name__ == "__main__":
    unittests(test_case_one, '2017-01-01', '2017-09-30', 'sp50_returns.csv')
    unittests(test_case_two, '2018-06-01', '2019-01-15', 'sp50_returns.csv')
