# coding=utf-8

import os
import csv
import datetime
import numpy as np
from Company import Company
from util import *
from plots import *


# TODO: Add function for tweaking weights. They must always sum up to 1.
# TODO: Add function for calculating the return/avkastningen, given a portfolio.
class Stockmarket(object):
	# TODO: add weights as input arguments, so that weights can be changed.
	def __init__(self, input_csv_ratios_file, input_csv_price_file, input_csv_index_file,
				 dict_of_parameters_and_weights={'roe': 0.2, 'fcfy': 0.2, 'roic_wacc': 0.2, 'revenue_growth': 0.2, 'dividend_yield': 0.2}):
		self.dict_of_parameters_and_weights = dict_of_parameters_and_weights

		self.ratios_file = input_csv_ratios_file
		self.price_file = input_csv_price_file
		self.index_file = input_csv_index_file

		# Placeholder values for the weights.
		self.weight_roe = None
		self.weight_fcfy = None
		self.weight_roic_wacc = None
		self.weight_revenue_growth = None
		self.weight_dividend_yield = None

		self.worst_scores = {'roe': -10000, 'stdev': 100000, 'fcfy': -10000, 'roic_wacc': -10000, 'revenue_growth': -1000000000, 'dividend_yield': -10000}

		# Set the weights.
		for parameter, weight in dict_of_parameters_and_weights.items():
			self.set_weight(parameter, weight)

		# Read data from csv-files.
		self.companies_and_their_data = []
		self.read_ratios_csv_file(input_csv_ratios_file)
		self.dates = []
		self.read_price_csv_file(input_csv_price_file)
		self.list_of_first_dates_each_year = []
		self.make_list_of_first_dates_each_year()
		self.list_of_first_dates_indices = []
		self.make_list_of_first_dates_indices()
		self.benchmark_index = []
		# self.benchmark_index_dates = []
		self.read_benchmark_index_csv_file(input_csv_index_file)
		# for i, _ in enumerate(self.dates):
		# 	if self.dates[i] != self.benchmark_index_dates[i]:
		# 		print('Not same: ', self.dates[i], self.benchmark_index_dates[i])
		# 		print('The dates in the benchmark_index-file are not the same as the dates in the total_return_gross-file.')

		self.number_of_companies = len(self.companies_and_their_data)
		self.removed_companies = []

	def get_dict_of_parameters_and_weights(self):
		return self.dict_of_parameters_and_weights

	def get_list_of_companies(self):
		return self.companies_and_their_data

	def get_number_of_companies(self):
		self.number_of_companies = len(self.companies_and_their_data)
		return self.number_of_companies

	def add_company(self, company):
		self.companies_and_their_data.append(company)
		return

	def remove_company(self, company):
		self.removed_companies.append(company)
		self.companies_and_their_data.remove(company)
		return

	def reset_removed_companies(self):
		for c in self.removed_companies[:]:
			self.add_company(c)
			self.removed_companies.remove(c)
		return

	def get_list_of_removed_companies(self):
		return self.removed_companies

	def get_number_of_removed_companies(self):
		return len(self.removed_companies)

	def get_list_of_first_dates_each_year(self):
		return self.list_of_first_dates_each_year

	def get_list_of_first_dates_indices(self):
		return self.list_of_first_dates_indices

	def get_first_date_and_its_index(self, index_year):
		return self.list_of_first_dates_each_year[index_year], self.list_of_first_dates_indices[index_year]

	def set_weight(self, parameter_name, new_weight):
		name_of_weight = 'weight_' + parameter_name
		setattr(self, name_of_weight, new_weight)
		self.dict_of_parameters_and_weights[parameter_name] = new_weight
		return

	def get_weight(self, parameter_name):
		name_of_weight = 'weight_' + parameter_name
		return getattr(self, name_of_weight)

	def create_company(self, data, input_file):
		ticker_temp = data[0]
		ticker_long = ticker_temp.split()
		ticker = ticker_long[0]
		bloomberg_ticker = data[0]
		name = data[1]
		industry = data[2]
		earnings_per_share = data[13:28]
		revenue_per_share = data[28:43]
		operating_income = data[43:58]
		dividends_paid = data[58:73]			# Används ej.
		free_cash_flow = data[73:88]
		roe = data[88:103]
		roic = data[103:118]
		company_value = data[118:133]
		market_cap = data[133:148]
		price = data[148:163]
		book_value = data[163:178]				# Borde läggas till.
		wacc = data[178:193]
		eqy_shares_out = data[193:208]			# Borde läggas till.
		dividend_forecast = data[208:223]
		px_volume = data[223:238]
		dividends = data[238:253]
		# company = Company(name, bloomberg_ticker, ticker_short, earnings_per_share, revenue_per_share, dividend_forecast, dividends, free_cash_flow, roe, roic, operating_income, price, wacc, company_value, px_volume)
		company = Company(name, bloomberg_ticker, ticker, industry, earnings_per_share, revenue_per_share, dividend_forecast, dividends, free_cash_flow, roe, roic, operating_income, price, wacc, company_value, market_cap, px_volume)

		return company


	# https://stackoverflow.com/questions/29254077/python-csv-reader-not-handling-quotes
	def read_ratios_csv_file(self, input_file):
		input_file = input_file + '.csv'
		path_to_data_folder = str(os.getcwd()) + '/inputfiles/'
		path_to_data_file = path_to_data_folder + input_file
		with open(path_to_data_file) as csvfile:
			if input_file.startswith('nasdaq'):
				# Skip first line in the CSV-file.
				next(csvfile)
			next(csvfile)
			csvreader = csv.reader(csvfile, quotechar='"', delimiter=';',
								   quoting=csv.QUOTE_ALL, skipinitialspace=True,
								   escapechar='\\')
			for data in csvreader:
				if not data[1].startswith('FINGERPR') and not data[1].startswith('SSAB AB-A'):
					company = self.create_company(data, input_file)
				self.add_company(company)

		return


	# Varje Company-objekt kommer få en instansvariabel self.daily_prices, som är
	# en lång lista med dagliga priser (där priset för ett givet index svarar
	# mot det datum som finns i samma index i Company.dates).
	# TODO: for some companies, for example HIFAB, the last daily price does not
	# seem to be the same as the last annual price, even though they are from
	# the same date, 2018-01-03.
	def read_price_csv_file(self, input_file):
		input_file = input_file + '.csv'
		path_to_data_folder = str(os.getcwd()) + '/inputfiles/'
		path_to_data_file = path_to_data_folder + input_file
		with open(path_to_data_file) as csvfile:

			if input_file.startswith('nasdaq'):
				# Skip the first three lines.
				next(csvfile)
				next(csvfile)
				next(csvfile)
			dates = next(csvfile).split(';')
			dates = dates[3:]
			dates[-1] = dates[-1].strip('\\\n')

			self.dates = dates
			Company.dates = dates

			csvreader = csv.reader(csvfile, quotechar='"', delimiter=';',
								   quoting=csv.QUOTE_ALL, skipinitialspace=True,
								   escapechar='\\')

			company_list = self.get_list_of_companies()

			for i, price_data in enumerate(csvreader):
				if input_file.startswith('nasdaq'):
					price_data.pop()
				price_data = price_data[3:]
				company_list[i].set_daily_prices(price_data)

		return


	def read_benchmark_index_csv_file(self, input_file):
		input_file = input_file + '.csv'
		path_to_data_folder = str(os.getcwd()) + '/inputfiles/'
		path_to_data_file = path_to_data_folder + input_file
		with open(path_to_data_file) as csvfile:
			dates_temp = next(csvfile)
			# dates_temp = dates_temp.split(';')
			# dates_temp[-1] = dates_temp[-1].strip('\n')
			# self.benchmark_index_dates = dates_temp
			benchmark_index_temp = next(csvfile)
			benchmark_index_temp = benchmark_index_temp.split(';')
			benchmark_index_temp[-1] = benchmark_index_temp[-1].strip('\n')
			self.benchmark_index = benchmark_index_temp

		return


	def make_list_of_first_dates_each_year(self):
		# If the price file is not nasdaq.
		if not self.price_file.startswith('nasdaq'):
			first_date = self.dates[-1]
			self.list_of_first_dates_each_year.append(first_date)
			current_year = first_date.split('-')[0]

			for date in reversed(self.dates):
				if not date.startswith(current_year):
					self.list_of_first_dates_each_year.append(date)
					current_year = date.split('-')[0]

			self.list_of_first_dates_each_year.reverse()
		# If it starts with "n" as in "nasdaq".
		else:
			previous_date = None
			previous_month = None
			for date in reversed(self.dates):
				_, current_month, _ = date.split('-')
				if date.endswith('04-30'):
					self.list_of_first_dates_each_year.append(date)
				elif not previous_date.endswith('04-30') and previous_month == '04' and current_month == '05':
					self.list_of_first_dates_each_year.append(date)
				previous_date = date
				previous_month = current_month

			self.list_of_first_dates_each_year.reverse()

		return


	def make_list_of_first_dates_indices(self):
		for first_date in self.get_list_of_first_dates_each_year():
			self.list_of_first_dates_indices.append(self.dates.index(first_date))

		return


	def assign_equal_weights(self, portfolio):
		for c in portfolio:
			c.set_weight(1/len(portfolio))

		return


	def assign_exponentially_lower_weights(self, portfolio):
		w_list = []
		s = 0
		for i, c in enumerate(portfolio):
			w = 1/(len(portfolio)+i)
			w_list.append(w)
			s += w

		for i, w in enumerate(w_list):
			portfolio[i].set_weight(w/s)

		return


	# Market cap is in millions <local currency>.
	# Input: a list of unwanted industries, a minimum market cap and the index
	# of the end year. Companies in unwanted industries, below the minimum
	# market cap will be removed, as well as companies lacking data.
	def remove_unwanted_companies(self, list_of_unwanted_industries, min_market_cap, index_year):
		_, idx = self.get_first_date_and_its_index(index_year)

		temp_list = self.get_list_of_companies()[:]

		for c in temp_list:
			# before = c.daily_prices[idx]
			if not is_float(c.daily_prices[idx]):
				c.fix_first_price(idx)
			# after = c.daily_prices[idx]
			# if before != after:
			# 	print(before, after, c.name)
			# 	print(c.daily_prices[idx-7:idx+1])
			# 	print()

			daily_prc = c.daily_prices[idx]
			mrk_cap = c.get_market_cap(index_year)
			# print(mrk_cap)
			ind = c.get_industry()
			prc = c.get_price(index_year)
			if (
				not is_float(daily_prc) or
				not is_float(mrk_cap) or
				float(mrk_cap) < min_market_cap or
				not is_float(prc) or
				ind in list_of_unwanted_industries
				):
				self.remove_company(c)

		return


	# Letar upp bolag som har mer än en aktie, dvs bolag med A-, B-aktier och så
	# vidare. Alla aktier som tillhör samma bolag jämförs. Den med högst trading
	# volume behålls.
	def keep_duplicates_with_the_highest_trading_volume(self, index_year):
		list_formatted_names = []

		temp_list = self.get_list_of_companies()
		for c in temp_list[:]:
			if c.formatted_name in list_formatted_names:
				duplicate = next((x for x in self.get_list_of_companies() if (x not in self.get_list_of_removed_companies() and x.formatted_name == c.formatted_name)), None)
				# print(duplicate.name, e.name)
				loser = self.which_company_has_the_lowest_trading_volume(duplicate, c, index_year)
				self.remove_company(loser)
			else:
				list_formatted_names.append(c.formatted_name)

		return


	def which_company_has_the_lowest_trading_volume(self, company1, company2, index_year):
		# if float(company1.px_volume[index_year]) > float(company2.px_volume[index_year]):
		if float(company1.get_px_volume(index_year)) > float(company2.get_px_volume(index_year)):
			return company2
		else:
			return company1


	def set_all_scores_and_ranks(self, index_year, remove=False):
		for parameter in self.get_dict_of_parameters_and_weights().keys():
			self.calculate_scores_for_this_parameter(index_year, parameter, remove)

		for parameter in self.get_dict_of_parameters_and_weights().keys():
			self.set_ranks_for_this_parameter(parameter, index_year)

		# self.calculate_total_scores(self.get_dict_of_parameters_and_weights())
		self.calculate_total_scores()
		self.set_ranks_for_this_parameter('total', index_year)

		return


	def calculate_total_scores(self):
		# for company in self.companies_and_their_data:
		for company in self.get_list_of_companies():
			# company.calculate_score_total(dict_of_parameters_and_corresponding_weight)
			company.calculate_score_total(self.get_dict_of_parameters_and_weights())

		return


	def calculate_scores_for_this_parameter(self, index_year, parameter_name, remove=False):
		method_name = 'calculate_score_' + parameter_name

		temp_list = self.get_list_of_companies()[:]
		for c in temp_list:
			try:
				# If parameter_name == 'roe', then this next line will call:
				# company.calculate_score_roe(index_year).
				getattr(c, method_name)(index_year)
			except:
				if remove:
					self.remove_company(c)
				else:
					c.set_score(parameter_name, self.worst_scores[parameter_name])
					if parameter_name == 'roe':
						c.set_score('stdev', self.worst_scores['stdev'])

			# except ValueError as ve:
			#     # print('ValueError in: ', method_name, ' - ', ve)
			#     self.remove_company(c)
			#     # self.give_worst_score_dict[parameter_name].append(c)
			# except ZeroDivisionError as zde:
			#     # print('ZeroDivisionError in: ', method_name, ' - ', zde)
			#     self.remove_company(c)
			#     # self.give_worst_score_dict[parameter_name].append(c)
			# except TypeError as te:
			#     # print('TypeError in: ', method_name, ' - ', te)
			#     self.remove_company(c)
			#     # self.give_worst_score_dict[parameter_name].append(c)

		return


	def set_ranks_for_this_parameter(self, parameter_name, index_year):
		special_cases = ['stdev', 'roe_plus_stdev', 'total']
		if parameter_name in special_cases:
			# https://stackoverflow.com/questions/29551840/how-to-sort-similar-values-in-a-sorted-list-based-on-second-value-of-tuples-ba
			self.companies_and_their_data.sort(key=lambda c: (c.get_score(parameter_name), -float(c.get_px_volume(index_year))))
			# self.companies_and_their_data.sort(key=lambda c: c.get_score(parameter_name))
		else:
			self.companies_and_their_data.sort(key=lambda c: c.get_score(parameter_name), reverse=True)

		rank = 1
		first = True
		for company in self.companies_and_their_data[:]:
			if first:
				company.set_rank(parameter_name, rank)
				first = False
			else:
				if previous_company.get_score(parameter_name) == company.get_score(parameter_name):
					company.set_rank(parameter_name, rank)
				else:
					rank += 1
					company.set_rank(parameter_name, rank)
			previous_company = company

		if parameter_name == 'roe':
			parameter_name = 'stdev'
			self.set_ranks_for_this_parameter(parameter_name, index_year)
			for company in self.companies_and_their_data[:]:
				score = company.get_rank('roe') + company.get_rank('stdev')
				company.set_score('roe_plus_stdev', score)
			self.set_ranks_for_this_parameter('roe_plus_stdev', index_year)

		return


	def print_this_many_companies(self, number=None):
		if not number:
			number = self.get_number_of_companies()
		for i, company in enumerate(self.companies_and_their_data):
			if i < number:
				s = str(i+1) + '.'
				while len(s) < 4:
					s += ' '
				print(s, company)

		return


	def print_these_companies(self, start, end):
		start = int(start)
		end = int(end)
		for i, c in enumerate(self.companies_and_their_data):
			i += 1
			if start <= i <= end:
				s = str(i) + '.'
				while len(s) < 4:
					s += ' '
				print(s, c)

		return


	def calculate_benchmark_index_holding_period_yield(self, start_idx, end_idx):
		start = float(self.benchmark_index[start_idx])
		end = float(self.benchmark_index[end_idx])
		diff = end - start
		y = (diff/start) * 100

		return y


	# TODO: den här borde egentligen vara en metod i Portfolio-klassen.
	# This function assumes an equal amount has been invested into each company.
	def calculate_holding_period_yield_portfolio(self, portfolio, start_date, end_date):
		holding_period_yield = 0

		list_of_tuples = self.partition_holding_period_dates(portfolio, start_date, end_date)
		# print(list_of_tuples)

		if list_of_tuples:
			tup = list_of_tuples[0]
			disappeared_company, date_company_disappeared = tup[0], tup[1]
			rest_of_portfolio = portfolio[:]
			rest_of_portfolio.remove(disappeared_company)
			rest_of_portfolio_yield = self.calculate_holding_period_yield_portfolio(rest_of_portfolio, date_company_disappeared, end_date)
			disappeared_company_yield = disappeared_company.calculate_holding_period_yield_share(start_date, date_company_disappeared)
			reinvestment_float = convert_yield_to_float(rest_of_portfolio_yield) * convert_yield_to_float(disappeared_company_yield)
			reinvestment_yield = convert_float_to_yield(reinvestment_float)
			holding_period_yield += reinvestment_yield
			for c in rest_of_portfolio:
				holding_period_yield += c.calculate_holding_period_yield_share(start_date, end_date)
		else:
			for c in portfolio:
				holding_period_yield += c.calculate_holding_period_yield_share(start_date, end_date)

		holding_period_yield = holding_period_yield / len(portfolio)
		# print('The holding period yield was {} between {} and {}.'.format(holding_period_yield, start_date, end_date))

		return holding_period_yield


	# Find which companies disappear from the market during the holding period
	# and return a list of tuples, where each tuples is on the form:
	# (company, date_company_disappeared). The list is sorted on the dates.
	def partition_holding_period_dates(self, portfolio, start_date, end_date):
		list_of_companies_that_disappeared = []
		start_idx = self.dates.index(start_date)
		end_idx = self.dates.index(end_date)
		for company in portfolio:
			date_company_disappeared = company.find_date_company_disappeared_from_market(start_idx, end_idx)
			if date_company_disappeared:
				tuple = (company, date_company_disappeared)
				list_of_companies_that_disappeared.append(tuple)

		list_of_companies_that_disappeared = sorted(list_of_companies_that_disappeared, key=lambda x: x[1])

		return list_of_companies_that_disappeared



	# Find which companies disappear from the market during the holding period
	# and return a list of tuples, where each tuples is on the form:
	# (company, index_company_disappeared). The list is sorted so that the
	# company that left the market the earliest, is displayed first.
	def partition_holding_period_indices(self, portfolio, start_idx, end_idx):
		d = {}
		for c in portfolio:
			idx_company_disappeared = c.find_index_company_disappeared_from_market(start_idx, end_idx)
			if idx_company_disappeared:
				d[c] = idx_company_disappeared

		# list_of_companies_that_disappeared = sorted(list_of_companies_that_disappeared, key=lambda x: x[1], reverse=True)
		# sorted_d = dict(sorted(d.items(), key=lambda t: t[1], reverse=True))

		return d


	# https://stackoverflow.com/questions/15036205/numpy-covariance-matrix
	# Returns-listorna/-vektorerna måste vara av samma längd för samtliga bolag.
	# start_idx är "tidigare" än end_idx. start_idx > end_idx.
	def create_covariance_matrix(self, portfolio, end_idx, start_idx=None):
		returns_matrix = []
		for company in portfolio:
			returns_matrix.append(company.get_company_returns_list_between_two_indices(end_idx, start_idx))
		covariance_matrix = np.cov(returns_matrix)

		return covariance_matrix


	# https://stackoverflow.com/questions/34480328/numpy-summing-up-a-list-of-vectors
	def get_portfolio_returns_list_between_two_indices(self, portfolio, end_idx, start_idx):
		list_of_share_returns_lists = []
		for c in portfolio:
			share_returns_list = c.get_company_returns_list_between_two_indices(end_idx, start_idx)
			list_of_share_returns_lists.append(np.asarray(share_returns_list))

		# for share in list_of_share_returns_lists:
		# 	print(share[:6])
		portfolio_returns_list = np.sum(list_of_share_returns_lists, axis=0)
		# print(portfolio_returns_list[:6])

		return portfolio_returns_list


	def get_benchmark_index_returns_array(self, start_idx, end_idx):
		date_indices = list(range(end_idx, start_idx))
		date_indices.reverse()

		first_price = float(self.benchmark_index[start_idx])
		r = np.empty(shape=len(date_indices))
		for i, date_index in enumerate(date_indices):
			r[i] = float(self.benchmark_index[date_index]) / first_price

		return r


	# p = portfolio, c = company, wl = weights list, dc = disappeared_company
	def get_daily_returns_matrix(self, p, start_idx, end_idx):
		matrix = np.empty(shape=(len(p), len(range(end_idx, start_idx))))
		companies_that_disappeared = self.partition_holding_period_indices(p, start_idx, end_idx)

		for c in p:
			if c not in companies_that_disappeared.keys():
				c.replace_missing_data(start_idx, end_idx)
			else:
				temp_idx = companies_that_disappeared[c]
				c.replace_missing_data(start_idx, temp_idx)

		if companies_that_disappeared:
			sorted_tuples = sorted(companies_that_disappeared.items(), key=lambda x:x[1], reverse=True)
			tup = sorted_tuples[0]
			dc, idx = tup[0], tup[1]

			rest_of_p = [c for c in p if not c == dc]

			wl = [comp.get_weight() for comp in rest_of_p]
			[comp.set_weight(comp.get_weight() * len(p) / len(rest_of_p)) for comp in rest_of_p]
			rest_matrix = self.get_daily_returns_matrix(rest_of_p, idx, end_idx)
			[comp.set_weight(wl[i]) for i, comp in enumerate(rest_of_p)]

			rest_summed_matrix = rest_matrix.sum(axis=0)
			dc.daily_returns_array[end_idx:idx] = np.flip(rest_summed_matrix, 0)

		for i, c in enumerate(p):
			if c not in companies_that_disappeared.keys():
				c.daily_returns_array[end_idx:start_idx+1] = c.get_daily_returns_array(start_idx, end_idx)
			else:
				# RICOH, 2008-01-02 -> 2008-08-14 -> 2009-01-02
				temp_idx = companies_that_disappeared[c]
				c.daily_returns_array[temp_idx:start_idx+1] = np.flip(c.get_daily_returns_array(start_idx, temp_idx), 0)
				c.daily_returns_array[end_idx:temp_idx] *= float(c.daily_returns_array[temp_idx])
				c.daily_returns_array[end_idx:start_idx+1] = np.flip(c.daily_returns_array[end_idx:start_idx+1], 0)
			c.return_this_year = c.daily_returns_array[start_idx]
			matrix[i] = c.daily_returns_array[end_idx:start_idx]
			# matrix[i] = c.daily_returns_array[end_idx+1:start_idx+1]
			matrix[i] *= c.get_weight()

			# if (start_idx-end_idx) > 250:
			# 	plot_returns(c.daily_returns_array[end_idx:start_idx], np.zeros(c.daily_returns_array[end_idx:start_idx].size), np.array(c.dates[end_idx:start_idx]))

		return matrix


	def get_covariance_matrix(self, matrix):
		cov_matrix = np.cov(matrix)

		return cov_matrix


	def get_portfolio_std_dev(self, portfolio, matrix):
		number_of_features = len(matrix[0])
		weights = [c.get_weight() for c in portfolio]
		weights = np.asarray(weights)
		cov_matrix = self.get_covariance_matrix(matrix)

		std_dev = round(np.sqrt(np.dot(weights.T,np.dot(cov_matrix, weights))) * np.sqrt(number_of_features),3)

		return std_dev


	def get_information_ratio(self, portfolio):
		return
