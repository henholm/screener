# coding=utf-8

import statistics
import itertools
import math
import numpy as np
from functools import reduce
from util import *


class Company(object):
	dates = []

	# def __init__(self, name, bloomberg_ticker, ticker_short, earnings_per_share, revenue_per_share, dividend_forecast, dividends, free_cash_flow, roe, roic, operating_income, price, wacc, company_value, px_volume):
	def __init__(self, name, bloomberg_ticker, ticker, industry, earnings_per_share, revenue_per_share, dividend_forecast, dividends, free_cash_flow, roe, roic, operating_income, price, wacc, company_value, market_cap, px_volume, daily_prices=None, invested=None):
		# Data collected from file.
		self.name = name						   	 # e.g. 'LYKO GROUP AB-A SHARES'
		self.formatted_name = self.format_name(name) # e.g. 'LYKO GROUP'

		self.bloomberg_ticker = bloomberg_ticker   	 # e.g. 'HIFAB SS Equity'
		self.ticker = ticker					   	 # e.g. 'HIFAB'
		# self.ticker_short = bloomberg_ticker[:-11] # e.g. 'HIFA'

		self.industry = industry
		self.earnings_per_share = earnings_per_share
		self.revenue_per_share = revenue_per_share
		self.dividend_forecast = dividend_forecast
		self.dividends = dividends
		self.free_cash_flow = free_cash_flow
		self.roe = roe
		self.roic = roic
		self.operating_income = operating_income
		self.price = price
		self.wacc = wacc
		self.company_value= company_value
		self.market_cap = market_cap
		self.px_volume = px_volume
		self.last_year = 0

		self.daily_prices = daily_prices
		self.indices_for_missing_price_data = []
		self.daily_prices = []

		self.return_this_year = ''
		self.daily_returns_array = []

		# This "weight" equals the proportion invested in to the company, i.e.
		# whether the company takes up 20% (weight == 0.2) of the portfolio or
		# if the company takes up 0.08 of the portfolio.
		self.weight = 0.0
		self.previous_weight = 0.0

		# Variables for roe score and rank.
		self.score_roe = None
		self.score_stdev = None
		self.rank_roe = None
		self.rank_stdev = None
		self.score_roe_plus_stdev = None
		self.rank_roe_plus_stdev = None

		# Variables for fcfy score and rank.
		self.score_fcfy = None
		self.rank_fcfy = None

		# Variables for roic_wacc score and rank.
		self.score_roic_wacc = None
		self.rank_roic_wacc = None

		# Variables for revenue_growth score and rank.
		self.score_revenue_growth = None
		self.rank_revenue_growth = None

		# Variables for dividend_yield score and rank.
		self.score_dividend_yield = None
		self.rank_dividend_yield = None

		# Total score and total rank.
		self.score_total = None
		self.rank_total = None

	def __repr__(self):
		rank_string = str(self.rank_total)
		while not len(rank_string) == 3:
			rank_string += ' '
		if is_int(self.return_this_year):
			return ('Total rank: {} \tTotal score: {} \t{} % \t{}'.format(rank_string, str(self.score_total),  format_decimal(convert_float_to_yield(self.return_this_year)), str(self.name)))
		else:
			return ('Total rank: {} \tTotal score: {} \t{}'.format(rank_string, str(self.score_total),  str(self.name)))
		# return ('Total rank: {}. \tTotal score: {}.\t{}'.format(str(self.rank_total), str(self.score_total), str(self.formatted_name)))

	def set_yield(self, ID, input_yield):
		self.holding_period_yields[ID] = input_yield
		return

	def get_yield(self, ID):
		return self.holding_period_yields[ID]

	def set_yield_from_float(self, ID, yield_as_float):
		self.holding_period_yields[ID] = (yield_as_float - 1) * 100

	def get_yield_as_float(self, ID):
		yield_as_float = 1 + (self.holding_period_yields[ID] / 100)
		return yield_as_float

	def get_score(self, parameter_name):
		score_attr = 'score_' + parameter_name
		return getattr(self, score_attr)

	def get_rank(self, parameter_name):
		rank_attr = 'rank_' + parameter_name
		return getattr(self, rank_attr)

	def set_score(self, parameter_name, score):
		score_attr = 'score_' + parameter_name
		setattr(self, score_attr, score)
		return

	def set_rank(self, parameter_name, rank):
		rank_attr = 'rank_' + parameter_name
		setattr(self, rank_attr, rank)
		return

	def get_industry(self):
		return self.industry

	def get_market_cap(self, index_year):
		return self.market_cap[index_year]

	def get_price(self, index_year):
		return self.price[index_year]

	def get_px_volume(self, index_year):
		return self.px_volume[index_year]

	def set_weight(self, weight):
		self.previous_weight = self.weight
		self.weight = weight
		return

	def get_weight(self):
		return self.weight

	def get_previous_weight(self):
		return self.previous_weight

	def set_daily_prices(self, price_data):
		self.daily_prices = price_data
		self.daily_returns_array = np.ones(len(price_data))
		return


	def fix_first_price(self, idx):
		sub = 0
		while not is_float(self.daily_prices[idx]):
			if sub > 7:
				break
			self.daily_prices[idx] = self.daily_prices[idx-sub]
			sub += 1

		return


	def format_name(self, input_name):
		name_list = input_name.split()
		length_name_list = len(name_list)
		half_length_name_list = math.ceil(length_name_list/2)
		new_name_list = name_list[:half_length_name_list]
		new_name = ' '.join(new_name_list)

		if new_name[-2:] in ['-A', '-B', '-C', '-D']:
			new_name = new_name[:-2]
		if new_name.endswith('-'):
			new_name = new_name.strip('-')
			new_name = new_name.strip()
		if new_name.endswith(' AB'):
			new_name = new_name[:-3]

		new_name = new_name.strip()

		return new_name


	# 40 försvinner 2008
	# TODO: Istället för att dela med längden på listan, ska man alltid dela
	# med 5? På så vis 'bestraffas' de som saknar värden. Nu, ifall de saknar
	# värden för de två senaste åren, kommer listan bara bli 3 values lång och
	# sedan delas med längden på listan, dvs 3. De bestraffas alltså inte.
	def calculate_score_roe(self, index_year):
		temp_roe = self.roe[index_year:(index_year + 5)]
		temp_roe = self.error_handling_roe(temp_roe)
		temp_roe = list(map(float, temp_roe))
		#https://stackoverflow.com/questions/9039961/finding-the-average-of-a-list
		average_roe = reduce(lambda x, y: x + y, temp_roe) / float(len(temp_roe))
		self.score_roe = average_roe/100.0
		temp_stdev = statistics.stdev(temp_roe)/100.0
		self.score_stdev = temp_stdev

		return


	def error_handling_roe(self, list_roe):
		# If any of the first 3 values are invalid, this if-clause is skipped.
		# We will not try to fix it. ValueError will be thrown -> remove company.
		#		If all the first three values are valid numbers however, this
		# if-clause will be used to check if the remaining two values are valid.
		if sum(is_float(value) == True for value in list_roe[:3]) == 3:
			# If both value 4 and 5 are floats, no error-handling is needed.
			if is_float(list_roe[3]) and is_float(list_roe[4]):
				pass
			# If value 4 is invalid but value 5 is valid, set value 4 = value 5.
			# This saves 3 companies, which would otherwise be removed.
			elif not is_float(list_roe[3]) and is_float(list_roe[4]):
				list_roe[3] = list_roe[4]
			# If value 5 is invalid but value 4 is valid, set the temp_fcf list
			# to be a list containing only the first 4 values (which are valid).
			# This 'saves' 21 companies, which would otherwise be removed.
			elif is_float(list_roe[3]) and not is_float(list_roe[4]):
				list_roe = list_roe[:4]
			# This else-clause sets the temp_roe-list to contain only the first
			# 3 values if the remaining two are invalid. 'Saves' 37 companies.
			else:
				list_roe = list_roe[:3]

		return list_roe


	# 159 försvann 2008.
	# 98  försvann 2009.
	# 130 försvann 2010.
	# 118 försvann 2011.
	# 95  försvann 2012.
	# 173 försvann 2018.
	# TODO: Istället för att dela med längden på listan, ska man alltid dela
	# med 5? På så vis 'bestraffas' de som saknar värden. Nu, ifall de saknar
	# värden för de två senaste åren, kommer listan bara bli 3 values lång och
	# sedan delas med längden på listan, dvs 3. De bestraffas alltså inte.
	def calculate_score_fcfy(self, index_year):
		temp_fcf = self.free_cash_flow[index_year:(index_year + 5)]
		temp_fcf = self.error_handling_fcfy(temp_fcf)
		temp_fcf = list(map(float, temp_fcf))
		average_fcf = reduce(lambda x, y: x + y, temp_fcf) / float(len(temp_fcf))
		temp_price = float(self.price[index_year])
		self.score_fcfy = average_fcf / temp_price

		return


	def error_handling_fcfy(self, list_fcf):
		# If any of the first 3 values are invalid, this if-clause is skipped.
		# We will not try to fix it. ValueError will be thrown -> remove company.
		#		If all the first three values are valid numbers however, this
		# if-clause will be used to check if the remaining two values are valid.
		if sum(is_float(value) == True for value in list_fcf[:3]) == 3:
			# If both value 4 and 5 are floats, no error-handling is needed.
			if is_float(list_fcf[3]) and is_float(list_fcf[4]):
				pass
			# If value 4 is invalid but value 5 is valid, set value 4 = value 5.
			# This saves 3 companies, which would otherwise be removed.
			elif not is_float(list_fcf[3]) and is_float(list_fcf[4]):
				list_fcf[3] = list_fcf[4]
			# If value 5 is invalid but value 4 is valid, set the temp_fcf list
			# to be a list containing only the first 4 values (which are valid).
			# This 'saves' 29 companies, which would otherwise be removed.
			elif is_float(list_fcf[3]) and not is_float(list_fcf[4]):
				list_fcf = list_fcf[:4]
			# This else-clause sets the fcf-list to contain only the first
			# 3 values if the remaining two are invalid. 'Saves' 37 companies.
			else:
				list_fcf = list_fcf[:3]

		return list_fcf


	# 106 försvann 2008.
	def calculate_score_roic_wacc(self, index_year):
		temp_roic = self.roic[index_year:(index_year + 5)]
		temp_roic = self.error_handling_roic(temp_roic)
		temp_roic = list(map(float, temp_roic))
		average_roic = reduce(lambda x, y: x + y, temp_roic) / float(len(temp_roic))

		temp_wacc = self.wacc[index_year]
		temp_wacc = self.error_handling_wacc(temp_wacc, index_year)
		temp_wacc = float(temp_wacc)

		self.score_roic_wacc = average_roic / temp_wacc
		# self.score_roic_wacc = average_roic

		return


	# TODO: evaluate the error-handling.
	def error_handling_roic(self, list_roic):
		# If any of the first 3 values are invalid, this if-clause is skipped.
		# We will not try to fix it. ValueError will be thrown -> remove company.
		# 		If all the first three values are valid numbers however, this
		# if-clause will be used to check if the remaining two values are valid.
		if sum(is_float(value) == True for value in list_roic[:3]) == 3:
			# If both value 4 and 5 are floats, no error-handling is needed.
			if is_float(list_roic[3]) and is_float(list_roic[4]):
				pass
			# If value 4 is invalid but value 5 is valid, set value 4 = value 5.
			# This saves 3 companies, which would otherwise be removed.
			elif not is_float(list_roic[3]) and is_float(list_roic[4]):
				list_roic[3] = list_roic[4]
			# If value 5 is #N/A N/A but value 4 is valid, set the list_roic list
			# to be a list containing only the first 4 values (which are valid).
			# This 'saves' ~78 companies, which would otherwise be removed.
			elif is_float(list_roic[3]) and not is_float(list_roic[4]):
				list_roic = list_roic[:4]
			# This else-clause sets the list_roic-list to contain only the first
			# 3 values if the remaining two are invalid. 'Saves' 59 companies.
			else:
				list_roic = list_roic[:3]

		# This snippet prevents 10 companies from being removed. These 16 have
		# only 1 missing value. It is replaced with another year's value.
		if sum(is_float(value) == False for value in list_roic) == 1:
			indx = next(i for i, v in enumerate(list_roic) if not is_float(v))
			# Replace it with the value from the previous year.
			list_roic[indx] = list_roic[indx+1]

		return list_roic


	def error_handling_wacc(self, value_wacc, end_year):
		# This code snippet saves 3 companies from being removed. If the WACC is
		# missing from the current year, the previous year's WACC will be used.
		if not is_float(value_wacc):
			if is_float(self.wacc[end_year+1]):
				value_wacc = self.wacc[end_year+1]

		return value_wacc


	# 28 försvann 2008.
	# TODO: måste vara säkra på att vi hämtar rätt värden.
	# years_back = 4 means we look 5 years back, since index starts at 0.
	def calculate_score_revenue_growth(self, index_year, failed_attempts=0, denominator=5.0, years_back=4):
		revenue_per_share_y0 = self.revenue_per_share[index_year]
		revenue_per_share_y5 = self.revenue_per_share[index_year + years_back]
		revenue_per_share_y0 = self.error_handling_revenue_growth(revenue_per_share_y0)
		revenue_per_share_y5 = self.error_handling_revenue_growth(revenue_per_share_y5)

		# Remove companies missing too much data.
		if failed_attempts > 2:
			raise ValueError(self.name, 'Too many unsuccessful attempts to find valid data. The company was removed.')
			# If you'd rather keep them and assign them a bad score instead of
			# removing them: self.score_revenue_growth = -1.0, return

		# If data is missing from the current year, use the previous year's CAGR.
		if not is_float(revenue_per_share_y0) or revenue_per_share_y0 == '0':
			# If data is missing from 2008 (the last index), use a CAGR from
			# 2004 to 2007 instead (a 4-year period).
			if index_year > 9:
				self.calculate_score_revenue_growth(index_year+1, failed_attempts+1, denominator-1, years_back-1)
				return
			else:
				# print(self.name, ' y0 saknades, så bytte till y1 och y6 istället.')
				self.calculate_score_revenue_growth(index_year+1, failed_attempts+1)
				return

		# If data is missing from five years back, use data from four years back.
		# Set the denominator to 4, since we're only using data from 4 years back.
		if not is_float(revenue_per_share_y5) or revenue_per_share_y5 == '0':
			# print(self.name, ' y5 saknades, så bytte till y4 istället.')
			self.calculate_score_revenue_growth(index_year, failed_attempts+1, denominator-1, years_back-1)
			return

		revenue_per_share_y0 = float(revenue_per_share_y0)
		revenue_per_share_y5 = float(revenue_per_share_y5)

		cagr = ((revenue_per_share_y0 / revenue_per_share_y5) ** (1/denominator)) - 1.0
		self.score_revenue_growth = cagr

		return


	def error_handling_revenue_growth(self, rev_per_share):
		# In order to check if a value is negative, you should first check if
		# the value can be converted to a float. Otherwise, a ValueError occurs.
		# Remove sketchy-looking companies with negative revenue.
		if is_float(rev_per_share) and float(rev_per_share) < 0:
			raise ValueError(self.name, 'This company had negative revenue. Therefore it was removed.')

		return rev_per_share


	# 0 försvann 2008.
	# The dividend yield we look at is an average over the last 3 years
	# regardless of the timespan we're looking at.
	def calculate_score_dividend_yield(self, index_year):
		temp_dividends = self.dividends[index_year:index_year + 3]
		temp_dividend_forecast = self.dividend_forecast[index_year]
		temp_dividends.append(temp_dividend_forecast)
		temp_dividends = self.error_handling_dividend_yield(temp_dividends)
		temp_dividends = list(map(float, temp_dividends))
		average_dividends = reduce(lambda x, y: x + y, temp_dividends) / float(len(temp_dividends))
		temp_price = float(self.price[index_year])
		self.score_dividend_yield = average_dividends / temp_price

		return


	def error_handling_dividend_yield(self, list_dividends):
		# Replace all invalid values with 0.
		for index, value in enumerate(list_dividends):
			if not is_float(value):
				list_dividends[index] = 0

		return list_dividends


	def calculate_score_total(self, dict_of_parameters_and_corresponding_weights):
		self.score_total = 0
		for parameter_name, weight in dict_of_parameters_and_corresponding_weights.items():
			if parameter_name == 'roe':
				parameter_name = 'roe_plus_stdev'
			parameter_rank = self.get_rank(parameter_name)
			weighted_rank = parameter_rank * weight
			self.score_total += weighted_rank
		self.score_total = round(self.score_total, 4)

		return


	def calculate_holding_period_yield_share(self, start_date, end_date):
		start_date_index = self.dates.index(start_date)
		end_date_index = self.dates.index(end_date)

		start_price = fetch_closest_valid_float(self.daily_prices, start_date_index, True)
		end_price = fetch_closest_valid_float(self.daily_prices, end_date_index, False)
		holding_period_yield = ((end_price / start_price) - 1) * 100
		# print('Growth: {}\t End: {}\tStart: {}\t {}'.format(holding_period_yield, end_price, start_price, company.name))

		return holding_period_yield


	# TODO: Kanske använda pstdev istället för stdev:
	# https://stackoverflow.com/questions/15389768/standard-deviation-of-a-list
	# Använd population standard deviation om du använder ALLA priser för
	# bolaget. Använd sample standard deviation om bara använder ett stickprov.
	def get_volatility_share(self, end_date, start_date=None):
		end_idx = Company.dates.index(end_date)
		if start_date is None:
			counter = 0
			start_idx = end_idx
			while is_float(self.daily_prices[start_idx]):
				start_idx += 1
				counter += 1
			start_idx -= 1
			print('Stdev: ', counter)
		else:
			start_idx = Company.dates.index(start_date)

		normalized_prices = np.asarray(self.daily_prices[end_idx:start_idx+1]) / self.daily_prices[end_idx]
		daily_ret = [0.0]
		for i in range(1, len(normalized_prices)):
			daily_ret.append(normalized_prices[i] / normalized_prices[i-1] - 1)
		# ddof = 1 sätter N-ddof till N-1 -> för sample stdev.
		# volatility = np.std(daily_ret, ddof=1)
		# ddof = 0 är default -> population stdev.
		volatility = np.std(daily_ret)

		# Should the daily_prices-list be reversed?
		daily_ret = [0.0]
		for i in range(1, len(normalized_prices)):
			daily_ret.append(normalized_prices[i] / normalized_prices[i-1] - 1)
		volatility = np.std(daily_ret)

		return volatility


	# This function counts the number of consecutive invalid values in the daily
	# price list of an company.
	def find_date_company_disappeared_from_market(self, start_idx, end_idx):
		date_company_disappeared = None
		#if not is_float(company.daily_prices[start_idx]):
		#    print('First date missing for: ', company.name)

		consecutive_invalid_prices = 0
		for i in range(start_idx, end_idx, -1):
			# If no price for a week, return the last valid date.
			if consecutive_invalid_prices > 7:
				date_company_disappeared = self.dates[i+consecutive_invalid_prices+1]
				return date_company_disappeared

			if not is_float(self.daily_prices[i]):
				consecutive_invalid_prices += 1
			elif is_float(self.daily_prices[i]) and consecutive_invalid_prices != 0:
				consecutive_invalid_prices = 0

		return date_company_disappeared


	# This function counts the number of consecutive invalid values in the daily
	# price list of an company.
	def find_index_company_disappeared_from_market(self, start_idx, end_idx):
		index_company_disappeared = None

		consecutive_invalid_prices = 0
		for i in range(start_idx, end_idx, -1):
			# If no price for a week, return the last valid date.
			if consecutive_invalid_prices > 7:
				# index_company_disappeared = i + consecutive_invalid_prices + 1
				index_company_disappeared = i + consecutive_invalid_prices
				return index_company_disappeared

			if not is_float(self.daily_prices[i]):
				consecutive_invalid_prices += 1
			elif is_float(self.daily_prices[i]) and consecutive_invalid_prices != 0:
				consecutive_invalid_prices = 0

		return index_company_disappeared


	# For all missing prices between the input indices, replace #N/A N/A with
	# the previous day's price.
	# https://grollchristian.wordpress.com/2014/08/13/missing-data/
	# TODO: Kan eventuellt skriva över med ett medelvärde av föregående och
	# nästföljande dags priser istället.
	def replace_missing_price_data(self, end_idx, start_idx):
		self.daily_prices = self.daily_prices[:]
		for i in reversed(self.indices_for_missing_price_data):
			if i in range(end_idx, start_idx+1):
				self.daily_prices[i] = self.daily_prices[i+1]

		return


	# For all missing prices between the input indices, replace #N/A N/A with
	# the previous day's data.
	# https://grollchristian.wordpress.com/2014/08/13/missing-data/
	# TODO: Kan eventuellt skriva över med ett medelvärde av föregående och
	# nästföljande dags priser istället.
	def replace_missing_data(self, start_idx, end_idx):
		indices = list(range(end_idx, start_idx+1))
		for i in reversed(indices):
			if not is_float(self.daily_prices[i]):
				self.daily_prices[i] = self.daily_prices[i+1]

		return


	def get_daily_returns_array(self, start_idx, end_idx):
		date_indices = list(range(end_idx, start_idx+1))
		date_indices.reverse()

		first_price = float(self.daily_prices[start_idx])
		r = np.empty(shape=len(date_indices))
		for i, date_index in enumerate(date_indices):
			r[i] = float(self.daily_prices[date_index]) / first_price

		return r


	# start_idx är "tidigare" än end_idx. start_idx > end_idx.
	# In case of start_idx=None:
	# If you invest in a portfolio 2018-01-01, then "end_idx" equals the index
	# in the daily_prices_list for 2018-01-01. This function will then, from the
	# input index go as far back as there are daily prices. It will then return
	# a list of the daily returns.
	def get_company_returns_list_between_two_indices(self, end_idx, start_idx):
		l = [float(i) for i in self.daily_prices[end_idx:start_idx+1]]
		l = np.asarray(l)
		# daily_ret_list = [0.0]
		# Denna for-loop användes på http://www.arngarden.com/2013/06/02/calculating-volatility-of-multi-asset-portfolio-example-using-python/#comments
		# men kör den inte åt "fel håll" typ?
		# for i in range(1, len(normalized_prices)):
		# 	daily_ret_list.append(normalized_prices[i] / normalized_prices[i-1] - 1)
		daily_ret_list = []
		for i in range(len(l)-1):
			daily_ret_list.append(l[i] / l[i+1] - 1)
		daily_ret_list.append(0.0)

		return daily_ret_list
