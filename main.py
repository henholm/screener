# coding=utf-8

import os
import csv
import re
import itertools
import datetime
import numpy as np
from itertools import islice
from Company import Company
from Stockmarket import Stockmarket
from util import *
from user_interface import *
from plots import *
# TODO: Kanske använda pstdev istället för stdev:
# https://stackoverflow.com/questions/15389768/standard-deviation-of-a-list


def filter_and_sort_stockmarket(ratios_file,
								daily_prices_file,
								index_file,
								min_market_cap,
								list_of_unwanted_industries,
								year,
								remove=False,
								dict_of_parameters_and_weights={'roe': 0.2, 'fcfy': 0.2, 'roic_wacc': 0.2, 'revenue_growth': 0.2, 'dividend_yield': 0.2}):
	stockmarket = Stockmarket(ratios_file, daily_prices_file, index_file, dict_of_parameters_and_weights)
	index_year = get_index_year(year)

	# Finns bara 341 bolag med pris 2004.
	# Finns bara 347 bolag med pris 2005.
	# Finns bara 367 bolag med pris 2006.
	# Finns bara 402 bolag med pris 2007.
	# Finns bara 433 bolag med pris 2008.
	# Finns bara 428 bolag med pris 2009.
	# Finns bara 421 bolag med pris 2010.
	# Finns bara 419 bolag med pris 2011.
	# Finns bara 419 bolag med pris 2012.
	# Finns bara 419 bolag med pris 2013.
	# Finns bara 427 bolag med pris 2014.
	# Finns bara 468 bolag med pris 2015.
	# Finns bara 523 bolag med pris 2016.
	# Finns bara 571 bolag med pris 2017.
	# Finns bara 634 bolag med pris 2018.

	# print('Original amount of companies read from file:\t\t\t\t', stockmarket.get_number_of_companies())
	stockmarket.remove_unwanted_companies(list_of_unwanted_industries, min_market_cap, index_year)
	# print('After removing unwanted industries, too low market cap and not belonging to the current year: ', stockmarket.get_number_of_companies())
	stockmarket.keep_duplicates_with_the_highest_trading_volume(index_year)
	# print('After removing duplicates (the share with the lowest trading volume):\t', stockmarket.get_number_of_companies())
	stockmarket.set_all_scores_and_ranks(index_year, remove)
	# print('After running calculate_score-function(s):\t\t\t\t', stockmarket.get_number_of_companies())

	return stockmarket


def backtest(ratios_file, daily_prices_file, index_file, min_market_cap,
			 list_of_unwanted_industries, years, portfolio_size, remove,
			 dict_of_parameters_and_weights={'roe': 0.2, 'fcfy': 0.2, 'roic_wacc': 0.2, 'revenue_growth': 0.2, 'dividend_yield': 0.2},
			 v=True, plot=False, weighted=False):
	start, end = years.split('-')
	start, end = int(start), int(end)
	list_of_years = make_list_of_intermediate_values(start, end)

	summed_matrices = []
	list_of_benchmark_index_arrays = []
	list_of_IR = []
	list_of_annual_return = []
	list_of_excess_return = []
	list_of_std_dev = []
	list_of_annual_return_index = []
	stockmarket = Stockmarket(ratios_file, daily_prices_file, index_file, dict_of_parameters_and_weights)


	for start_year in list_of_years:
		end_year = start_year + 1
		start_year_index = get_index_year(start_year)
		end_year_index = get_index_year(end_year)
		start_date, start_idx = stockmarket.get_first_date_and_its_index(start_year_index)
		end_date, end_idx = stockmarket.get_first_date_and_its_index(end_year_index)

		stockmarket.remove_unwanted_companies(list_of_unwanted_industries, min_market_cap, start_year_index)
		stockmarket.keep_duplicates_with_the_highest_trading_volume(start_year_index)
		stockmarket.set_all_scores_and_ranks(start_year_index, remove)

		pf = stockmarket.get_list_of_companies()[:portfolio_size]
		if weighted:
			stockmarket.assign_exponentially_lower_weights(pf)
		else:
			stockmarket.assign_equal_weights(pf)

		pf_daily_returns_matrix = stockmarket.get_daily_returns_matrix(pf, start_idx, end_idx)
		pf_std_dev = stockmarket.get_portfolio_std_dev(pf, pf_daily_returns_matrix)
		list_of_std_dev.append(pf_std_dev)

		benchmark_index = stockmarket.get_benchmark_index_returns_array(start_idx, end_idx)
		list_of_benchmark_index_arrays.append(benchmark_index)

		# Sum all the arrays for each company's daily return to get the daily
		# return of the whole portfolio.
		summed_matrix = pf_daily_returns_matrix.sum(axis=0)
		# Save the summed_matrix for this year, so that we can concatenate the
		# summed matrices later, in order to get the portfolio daily return for
		# the whole time period.
		summed_matrices.append(summed_matrix)

		excess_return_matrix = summed_matrix - benchmark_index
		mean = excess_return_matrix.mean()
		# Information ratio
		IR = mean / pf_std_dev
		list_of_IR.append(IR)
		pfy = summed_matrix[-1]
		list_of_annual_return.append(pfy)
		pfy = convert_float_to_yield(pfy)

		if v:
			spy = benchmark_index[-1]
			spy = convert_float_to_yield(spy)
			list_of_annual_return_index.append(spy)
			exr = pfy - spy
			list_of_excess_return.append(exr)
			# mean_as_yield = convert_float_to_yield(mean + 1)

			formatted_pfy = format_decimal(pfy)
			formatted_spy = format_decimal(spy)
			formatted_exr = format_decimal(exr)
			# formatted_mean = format_decimal(mean_as_yield)
			# formatted_stdev = format_decimal(pf_std_dev)
			formatted_volatility = format_decimal(pf_std_dev*100)
			# formatted_volatility = format_decimal(pf_std_dev * 100)
			formatted_IR = format_decimal(IR)

			stockmarket.print_this_many_companies(portfolio_size)
			print()
			# Generally, an information ratio in the 0.40-0.60 range is good.
			# Exempel på IR-kvoter: https://www.avanza.se/placera/redaktionellt/2010/09/30/fonder-med-fria-tyglar-gar-inte-alltid-battre-an-index.html
			print('Holding period:      \t\t\t\t  {} to {}'.format(start_date, end_date))
			print('Holding period yield:\t\t\t\t', formatted_pfy, '%')
			print('Return of index:     \t\t\t\t', formatted_spy, '%')
			print('Excess return:       \t\t\t\t', formatted_exr, '%')
			# print('Mean excess return:  \t', formatted_mean, '%')
			# print('Portfolio std dev:   \t', formatted_stdev)
			print('Portfolio volatility:\t\t\t\t', formatted_volatility, '%')
			print('Information ratio:   \t\t\t\t', formatted_IR)

			print('\n*************************************************************************************')
		stockmarket.reset_removed_companies()

	# Instantiate an empty np-array of the same length as all the entries in the
	# index daily return lists, i.e. as long as there were total trade days.
	total_length_s_p = sum(len(s_p) for s_p in list_of_benchmark_index_arrays)
	total_benchmark_index = np.empty(shape=total_length_s_p)
	# Get the aggregate return of index by multiplying the cumulative return.
	from_idx = 0
	to_idx = 0
	multiplicator = 1
	for benchmark_index_array in list_of_benchmark_index_arrays:
		to_idx += benchmark_index_array.size
		total_benchmark_index[from_idx:to_idx] = benchmark_index_array
		total_benchmark_index[from_idx:to_idx] *= multiplicator
		multiplicator *= benchmark_index_array[-1]
		from_idx = to_idx

	# Instantiate an empty np-array of the same length as all the entries in the
	# index daily return lists, i.e. as long as there were total trade days. This
	# will be of the same length as the total_benchmark_index-array, but keep for clarity.
	total_length_summed_matrix = sum(len(s_m) for s_m in summed_matrices)
	total_summed_matrix = np.empty(shape=total_length_summed_matrix)
	# Get the aggregate return.
	from_idx = 0
	to_idx = 0
	multiplicator = 1
	for summed_matrix in summed_matrices:
		to_idx += summed_matrix.size
		total_summed_matrix[from_idx:to_idx] = summed_matrix
		total_summed_matrix[from_idx:to_idx] *= multiplicator
		multiplicator *= summed_matrix[-1]
		from_idx = to_idx

	list_of_years.append(end_year)
	first_year = int(list_of_years[0])
	last_year = int(list_of_years[-1])
	first_year_index = get_index_year(first_year)
	last_year_index = get_index_year(last_year)
	first_date, first_idx = stockmarket.get_first_date_and_its_index(first_year_index)
	last_date, last_idx = stockmarket.get_first_date_and_its_index(last_year_index)

	# TOTAL RETURN
	tpfy = total_summed_matrix[-1]
	# ANNUAL RATE OF RETURN
	# The baseline is annual_rate_of_return**exponent = tpfy.
	exponent = len(list_of_years) - 1
	exponent = float(exponent)
	# To get annual_rate_of_return, calculate the (exponent)nth square root of tpfy.
	# This can be done by raising tpfy to the power of 1/exponent.
	annual_rate_of_return = tpfy**(1/exponent)
	annual_rate_of_return = convert_float_to_yield(annual_rate_of_return)
	tpfy = convert_float_to_yield(tpfy)
	# TOTAL RETURN OF INDEX
	tspy = total_benchmark_index[-1]
	# ANNUAL RATE OF RETURN INDEX
	annual_rate_of_return_index = tspy**(1/exponent)
	annual_rate_of_return_index = convert_float_to_yield(annual_rate_of_return_index)
	tspy = convert_float_to_yield(tspy)
	# TOTAL EXCESS RETURN
	texr = tpfy - tspy

	# STANDARD DEVIATION, i.e. VOLATILITY
	# OPTION 2. Standard deviation (volatility) of the DAILY excess return.
	std_dev_daily_excess = np.std(excess_return_matrix, ddof=1)		# POPULATION
	# OPTION 3. Standard deviation (volatility) of the ANNUAL return.
	std_dev_annual = np.std(list_of_annual_return, ddof=1)	 		# POPULATION

	# INFORMATION RATIO
	# OPTION 2. Using daily excess returns and standard deviation of daily excess returns.
	IR_daily_excess = excess_return_matrix.mean() / std_dev_daily_excess

	# FORMATTING OF TOTAL RETURN
	formatted_tpfy = format_decimal(tpfy)
	# FORMATTING OF TOTAL EXCESS RETURN
	formatted_texr = format_decimal(texr)

	# FORMATTING OF STANDARD DEVIATION (VOLATILITY)
	formatted_std_dev_annual = format_decimal(std_dev_annual * 100)

	# FORMATTING OF INFORMATION RATIO
	formatted_IR_daily_excess = format_decimal(IR_daily_excess)

	if v:
		# DAILY EXCESS RETURN
		excess_return_matrix = total_summed_matrix - total_benchmark_index
		# ANNUAL RATE OF EXCESS RETURN
		annual_rate_of_excess_return =  (convert_yield_to_float(texr))**(1/exponent)
		annual_rate_of_excess_return = convert_float_to_yield(annual_rate_of_excess_return)


		# OPTION 1. Standard deviation (volatility) of the DAILY return.
		std_dev_daily = np.std(total_summed_matrix, ddof=1)				# POPULATION
		# std_dev_daily_sample = np.std(total_summed_matrix)			# SAMPLE

		# std_dev_daily_sample_excess = np.std(excess_return_matrix)	# SAMPLE

		# std_dev_annual = np.std(list_of_annual_return, ddof=0) 		# SAMPLE
		# OPTION 4. Standard deviation (volatility) of the ANNUAL excess return.
		list_of_excess_return = [((100 + r)/100) for r in list_of_excess_return]
		std_dev_annual_excess = np.std(list_of_excess_return, ddof=1)	# POPULATION
		# std_dev_annual_excess = np.std(list_of_annual_return, ddof=0) # SAMPLE
		# OPTION 5. Mean of each year's standard deviation.
		std_dev_mean = (np.array(list_of_std_dev)).mean()


		# OPTION 1. Using daily excess returns and standard deviation of daily returns.
		IR_daily = excess_return_matrix.mean() / std_dev_daily
		# OPTION 3. Using daily excess returns and standard deviation of annual returns.
		IR_annual1 = excess_return_matrix.mean() / std_dev_annual
		# OPTION 4. Using annual returns and standard deviation of annual returns.
		IR_annual2 = (np.array(list_of_annual_return).mean()) / std_dev_annual
		# OPTION 5. Using annual excess returns and standard deviation of annual returns.
		IR_annual3 = (np.array(list_of_excess_return).mean()) / std_dev_annual
		# OPTION 6. Using annual excess returns and standard deviation of annual excess returns.
		IR_annual4 = (np.array(list_of_excess_return).mean()) / std_dev_annual_excess
		# OPTION 7. Using the mean of each year's information ratio, i.e. average of 10.
		mean_of_IR = (np.array(list_of_IR)).mean()


		# FORMATTING OF AVERAGE ANNUAL RETURN (AAR)
		# formatted_aar = format_decimal(tpfy/(len(list_of_years)-1))
		formatted_aar_mean = format_decimal((np.array([convert_float_to_yield(r) for r in list_of_annual_return])).mean())
		# FORMATTING OF ANNUAL RATE OF RETURN
		formatted_ar = format_decimal(annual_rate_of_return)
		# FORMATTING OF RETURN OF INDEX (benchmark_index)
		formatted_tspy = format_decimal(tspy)
		# FORMATTING OF ANNUAL RATE OF RETURN INDEX
		formatted_ari = format_decimal(annual_rate_of_return_index)
		# FORMATTING OF ANNUAL RATE OF EXCESS RETURN
		formatted_are = format_decimal(annual_rate_of_excess_return)
		# formatted_mean = format_decimal(mean_as_yield)


		formatted_std_dev_daily = format_decimal(std_dev_daily)
		formatted_std_dev_daily_excess = format_decimal(std_dev_daily_excess)
		formatted_std_dev_annual_excess = format_decimal(std_dev_annual_excess)
		formatted_std_dev_mean = format_decimal(std_dev_mean)


		formatted_IR_daily = format_decimal(IR_daily)
		formatted_IR_annual1 = format_decimal(IR_annual1)
		formatted_IR_annual2 = format_decimal(IR_annual2)
		formatted_IR_annual3 = format_decimal(IR_annual3)
		formatted_IR_annual4 = format_decimal(IR_annual4)
		formatted_IR_mean = format_decimal(mean_of_IR)


		# AVERAGE ANNUAL RETURN INDEX
		formatted_aari = format_decimal((np.array(list_of_annual_return_index)).mean())
		aexr = (np.array(list_of_excess_return)).mean()
		aexr = convert_float_to_yield(aexr)
		formatted_aexr_mean = format_decimal(aexr)
		# formatted_aexr = format_decimal(texr/(len(list_of_years)-1))

		print()
		print('Total holding period:                              {} to {}\n'.format(first_date, last_date))
		print('Total return:                                     ', formatted_tpfy, '%')
		# print('AAR (total return/{}):                         \t  {} %'.format(len(list_of_years)-1, formatted_aar))
		print('AAR (mean of annual returns):                     ', formatted_aar_mean, '%')
		print('Annual rate of return:                            ', formatted_ar, '%\n')
		print('Total return of index:                            ', formatted_tspy, '%')
		print('AAR of index (mean of index annual returns):      ', formatted_aari, '%')
		print('Annual rate of return index:                      ', formatted_ari, '%\n')
		print('Total excess return:                              ', formatted_texr, '%')
		# print('Average excess return (total excess return/{}):\t  {} %: '.format((len(list_of_years))-1, formatted_aexr))
		print('Average excess return (mean of excess returns):   ', formatted_aexr_mean, '%')
		print('Annual rate of excess return:                     ', formatted_are, '%\n')
		# print('Mean excess return:    \t ', formatted_mean, '%')
		# print('Total std dev (sample):\t', std_dev_daily_sample)
		# print('Standard deviation (daily):              \t ', formatted_std_dev_daily)
		# print('Standard deviation (daily excess):       \t ', formatted_std_dev_daily_excess)
		print('Volatility (st. dev. of annual returns, {} years):'.format(len(list_of_years)-1), formatted_std_dev_annual, '%')
		# print('Standard deviation (annual excess):      \t ', formatted_std_dev_annual_excess)
		# print('Standard deviation (mean):               \t ', formatted_std_dev_mean, '\n')
		# print('Total IR (sample):     \t', IR_daily_sample)
		# print('Information ratio (d_e / d):             \t ', formatted_IR_daily)
		print('Information ratio:                                 ', formatted_IR_daily_excess)
		# print('Information ratio (d_e / a):             \t ', formatted_IR_annual1)
		# print('Information ratio (a / a):               \t ', formatted_IR_annual2)
		# print('Information ratio (a_e / a):             \t ', formatted_IR_annual3)
		# print('Information ratio (a_e / a_e):           \t ', formatted_IR_annual4)
		# print('Information ratio (mean):                \t ', formatted_IR_mean)

	if plot:
		dates = stockmarket.dates[last_idx:first_idx]
		dates.reverse()
		plot_returns(total_summed_matrix, total_benchmark_index, dates)

	return formatted_tpfy, formatted_texr, formatted_std_dev_annual, formatted_IR_daily_excess


def test_linearity(ratios_file, daily_prices_file, index_file, min_market_cap,
			 	   list_of_unwanted_industries, years, portfolio_size, remove,
			 	   dict_of_parameters_and_weights={'roe': 0.2, 'fcfy': 0.2, 'roic_wacc': 0.2, 'revenue_growth': 0.2, 'dividend_yield': 0.2},
			 	   v=True, plot=False, weighted=False):
	start, end = years.split('-')
	start, end = int(start), int(end)
	list_of_years = make_list_of_intermediate_values(start, end)

	dict_of_quintiles = {}

	dict_of_lists_of_summed_matrices = {0: [], 1: [], 2: [], 3: [], 4: []}
	dict_of_lists_of_annual_return = {0: [], 1: [], 2: [], 3: [], 4: []}
	dict_of_lists_of_excess_return = {0: [], 1: [], 2: [], 3: [], 4: []}
	dict_of_lists_of_excess_return_means = {0: [], 1: [], 2: [], 3: [], 4: []}

	dict_of_lists_of_std_dev = {0: [], 1: [], 2: [], 3: [], 4: []}
	dict_of_lists_of_IR = {0: [], 1: [], 2: [], 3: [], 4: []}

	list_of_benchmark_index_arrays = []
	list_of_annual_return_index = []

	for index, start_year in enumerate(list_of_years):
		stockmarket = filter_and_sort_stockmarket(ratios_file,
												  daily_prices_file,
												  index_file,
												  min_market_cap,
												  list_of_unwanted_industries,
												  start_year,
												  remove,
												  dict_of_parameters_and_weights)

		end_year = start_year + 1
		start_year_index = get_index_year(start_year)
		end_year_index = get_index_year(end_year)
		start_date, start_idx = stockmarket.get_first_date_and_its_index(start_year_index)
		end_date, end_idx = stockmarket.get_first_date_and_its_index(end_year_index)

		benchmark_index = stockmarket.get_benchmark_index_returns_array(start_idx, end_idx)
		list_of_benchmark_index_arrays.append(benchmark_index)

		spy = benchmark_index[-1]
		spy = convert_float_to_yield(spy)
		list_of_annual_return_index.append(spy)

		# pf = stockmarket.get_list_of_companies()[:100]
		pf = stockmarket.get_list_of_companies()
		for i in range(int(100/20)):
			quintile_pf = pf[i*20:(int((i+1)*20))]
			# quintile_pf = pf[:(int((i+1)*20))]
			# quintile_pf = pf[i*25:(int((i+1)*25))]
			dict_of_quintiles[i] = quintile_pf

			if weighted:
				stockmarket.assign_exponentially_lower_weights(quintile_pf)
			else:
				stockmarket.assign_equal_weights(quintile_pf)

			quintile_pf_daily_returns_matrix = stockmarket.get_daily_returns_matrix(quintile_pf, start_idx, end_idx)
			quintile_pf_std_dev = stockmarket.get_portfolio_std_dev(quintile_pf, quintile_pf_daily_returns_matrix)
			dict_of_lists_of_std_dev[i].append(quintile_pf_std_dev)

			# Sum all the arrays for each company's daily return to get the daily
			# return of the whole portfolio.
			summed_matrix = quintile_pf_daily_returns_matrix.sum(axis=0)
			# Save the summed_matrix for this year, so that we can concatenate the
			# summed matrices later, in order to get the portfolio daily return for
			# the whole time period.
			dict_of_lists_of_summed_matrices[i].append(summed_matrix)

			excess_return_matrix = summed_matrix - benchmark_index
			mean = excess_return_matrix.mean()
			# dict_of_lists_of_excess_return_means[i].append(mean)
			# Information ratio
			IR = mean / quintile_pf_std_dev
			dict_of_lists_of_IR[i].append(IR)
			quintile_pfy = summed_matrix[-1]
			dict_of_lists_of_annual_return[i].append(quintile_pfy)
			quintile_pfy = convert_float_to_yield(quintile_pfy)

			exr = quintile_pfy - spy
			dict_of_lists_of_excess_return[i].append(exr)

		formatted_spy = format_decimal(spy)
		list_of_formatted_pfy = []
		list_of_formatted_exr = []
		list_of_formatted_mean = []
		list_of_formatted_std_dev = []
		list_of_formatted_IR = []
		for i in range(int(100/20)):
			list_of_formatted_pfy.append(format_decimal(convert_float_to_yield(dict_of_lists_of_annual_return[i][index])))
			list_of_formatted_exr.append(format_decimal(dict_of_lists_of_excess_return[i][index]))
			# mean_as_yield = convert_float_to_yield(dict_of_lists_of_excess_return_means[i][index] + 1)
			# list_of_formatted_mean.append(format_decimal(mean_as_yield))
			list_of_formatted_std_dev.append(format_decimal(dict_of_lists_of_std_dev[i][index] * 100))
			list_of_formatted_IR.append(format_decimal(dict_of_lists_of_IR[i][index]))

			print()
			print('Quintile {}'.format(i+1))
			# print(dict_of_quintiles[i])
			if i == 0:
				stockmarket.print_these_companies(i*20, (i*20)+20)
				# stockmarket.print_these_companies(i*25, (i*25)+25)
			else:
				stockmarket.print_these_companies((i*20)+1, (i*20)+20)
				# stockmarket.print_these_companies((i*25)+1, (i*25)+25)
		# stockmarket.print_this_many_companies(100)
		print()
		print('Holding period:       \t\t\t\t     {} to {}'.format(start_date, end_date))
		print('Results for quintile: \t\t1\t   2\t      3\t         4\t    5')
		print('Holding period yields:\t{} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_pfy))
		print('Excess return:        \t{} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_exr))
		# print('Mean excess return:   \t{} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_mean))
		print('Portfolio std dev:    \t{} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_std_dev))
		print('Information ratio:    \t{} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_IR))
		print('Return of index:      \t\t\t\t\t\t    {} %'.format(formatted_spy))

		print('\n*************************************************************************************')

	list_of_years.append(end_year)
	first_year = int(list_of_years[0])
	last_year = int(list_of_years[-1])
	first_year_index = get_index_year(first_year)
	last_year_index = get_index_year(last_year)
	first_date, first_idx = stockmarket.get_first_date_and_its_index(first_year_index)
	last_date, last_idx = stockmarket.get_first_date_and_its_index(last_year_index)

	exponent = len(list_of_years) - 1
	exponent = float(exponent)

	# Instantiate an empty np-array of the same length as all the entries in the
	# index daily return lists, i.e. as long as there were total trade days.
	total_length_s_p = sum(len(s_p) for s_p in list_of_benchmark_index_arrays)
	total_benchmark_index = np.empty(shape=total_length_s_p)
	# Get the aggregate return of index by multiplying the cumulative return.
	from_idx = 0
	to_idx = 0
	multiplicator = 1
	for benchmark_index_array in list_of_benchmark_index_arrays:
		to_idx += benchmark_index_array.size
		total_benchmark_index[from_idx:to_idx] = benchmark_index_array
		total_benchmark_index[from_idx:to_idx] *= multiplicator
		multiplicator *= benchmark_index_array[-1]
		from_idx = to_idx

	# AVERAGE ANNUAL RETURN INDEX
	formatted_aari = format_decimal((np.array(list_of_annual_return_index)).mean())
	# TOTAL RETURN OF INDEX
	tspy = total_benchmark_index[-1]
	# ANNUAL RATE OF RETURN INDEX
	annual_rate_of_return_index = tspy**(1/exponent)
	annual_rate_of_return_index = convert_float_to_yield(annual_rate_of_return_index)
	tspy = convert_float_to_yield(tspy)

	# FORMATTING OF RETURN OF INDEX (benchmark_index)
	formatted_tspy = format_decimal(tspy)
	# FORMATTING OF ANNUAL RATE OF RETURN INDEX
	formatted_ari = format_decimal(annual_rate_of_return_index)

	# AVERAGE ANNUAL RETURN INDEX
	formatted_aari = format_decimal((np.array(list_of_annual_return_index)).mean())


	list_of_formatted_total_pfy = []
	list_of_total_summed_matrices = []
	list_of_formatted_annual_rate_of_return = []
	list_of_formatted_texr = []
	list_of_formatted_std_dev_annual = []
	list_of_formatted_IR_daily_excess = []
	list_of_formatted_aar_mean = []
	list_of_formatted_are = []
	list_of_formatted_aexr_mean = []
	for q in range(int(100/20)):
		# Instantiate an empty np-array of the same length as all the entries in the
		# index daily return lists, i.e. as long as there were total trade days. This
		# will be of the same length as the total_benchmark_index-array, but keep for clarity.
		total_length_summed_matrix = sum(len(s_m) for s_m in dict_of_lists_of_summed_matrices[q])
		total_summed_matrix = np.empty(shape=total_length_summed_matrix)
		# Get the aggregate return.
		from_idx = 0
		to_idx = 0
		multiplicator = 1
		for summed_matrix in dict_of_lists_of_summed_matrices[q]:
			to_idx += summed_matrix.size
			total_summed_matrix[from_idx:to_idx] = summed_matrix
			total_summed_matrix[from_idx:to_idx] *= multiplicator
			multiplicator *= summed_matrix[-1]
			from_idx = to_idx
		list_of_total_summed_matrices.append(total_summed_matrix)

		# TOTAL RETURN
		tpfy = total_summed_matrix[-1]

		# ANNUAL RATE OF RETURN
		# To get annual_rate_of_return, calculate the (exponent)nth square root of tpfy.
		# This can be done by raising tpfy to the power of 1/exponent.
		annual_rate_of_return = tpfy**(1/exponent)
		annual_rate_of_return = convert_float_to_yield(annual_rate_of_return)
		tpfy = convert_float_to_yield(tpfy)
		# TOTAL EXCESS RETURN
		texr = tpfy - tspy

		# STANDARD DEVIATION, i.e. VOLATILITY
		# OPTION 2. Standard deviation (volatility) of the DAILY excess return.
		std_dev_daily_excess = np.std(excess_return_matrix, ddof=1)		# POPULATION
		# OPTION 3. Standard deviation (volatility) of the ANNUAL return.
		std_dev_annual = np.std(dict_of_lists_of_annual_return[q], ddof=1)	 		# POPULATION

		# INFORMATION RATIO
		# OPTION 2. Using daily excess returns and standard deviation of daily excess returns.
		IR_daily_excess = excess_return_matrix.mean() / std_dev_daily_excess

		# FORMATTING OF TOTAL RETURN
		formatted_tpfy = format_decimal(tpfy)
		list_of_formatted_total_pfy.append(formatted_tpfy)

		# FORMATTING OF TOTAL EXCESS RETURN
		formatted_texr = format_decimal(texr)
		list_of_formatted_texr.append(formatted_texr)

		# FORMATTING OF STANDARD DEVIATION (VOLATILITY)
		formatted_std_dev_annual = format_decimal(std_dev_annual * 100)
		list_of_formatted_std_dev_annual.append(formatted_std_dev_annual)

		# FORMATTING OF INFORMATION RATIO
		formatted_IR_daily_excess = format_decimal(IR_daily_excess)
		list_of_formatted_IR_daily_excess.append(formatted_IR_daily_excess)

		# DAILY EXCESS RETURN
		excess_return_matrix = total_summed_matrix - total_benchmark_index
		# ANNUAL RATE OF EXCESS RETURN
		annual_rate_of_excess_return =  (convert_yield_to_float(texr))**(1/exponent)
		annual_rate_of_excess_return = convert_float_to_yield(annual_rate_of_excess_return)


		# OPTION 1. Standard deviation (volatility) of the DAILY return.
		# std_dev_daily = np.std(total_summed_matrix, ddof=1)				# POPULATION
		# std_dev_daily_sample = np.std(total_summed_matrix)			# SAMPLE

		# std_dev_daily_sample_excess = np.std(excess_return_matrix)	# SAMPLE

		# std_dev_annual = np.std(list_of_annual_return, ddof=0) 		# SAMPLE
		# OPTION 4. Standard deviation (volatility) of the ANNUAL excess return.
		list_of_excess_return = [((100 + r)/100) for r in dict_of_lists_of_excess_return[q]]
		# std_dev_annual_excess = np.std(list_of_excess_return, ddof=1)	# POPULATION
		# std_dev_annual_excess = np.std(list_of_annual_return, ddof=0) # SAMPLE
		# OPTION 5. Mean of each year's standard deviation.
		# std_dev_mean = (np.array(list_of_std_dev)).mean()


		# # OPTION 1. Using daily excess returns and standard deviation of daily returns.
		# IR_daily = excess_return_matrix.mean() / std_dev_daily
		# # OPTION 3. Using daily excess returns and standard deviation of annual returns.
		# IR_annual1 = excess_return_matrix.mean() / std_dev_annual
		# # OPTION 4. Using annual returns and standard deviation of annual returns.
		# IR_annual2 = (np.array(list_of_annual_return).mean()) / std_dev_annual
		# # OPTION 5. Using annual excess returns and standard deviation of annual returns.
		# IR_annual3 = (np.array(list_of_excess_return).mean()) / std_dev_annual
		# # OPTION 6. Using annual excess returns and standard deviation of annual excess returns.
		# IR_annual4 = (np.array(list_of_excess_return).mean()) / std_dev_annual_excess
		# # OPTION 7. Using the mean of each year's information ratio, i.e. average of 10.
		# mean_of_IR = (np.array(list_of_IR)).mean()


		# FORMATTING OF AVERAGE ANNUAL RETURN (AAR)
		# formatted_aar = format_decimal(tpfy/(len(list_of_years)-1))
		formatted_aar_mean = format_decimal((np.array([convert_float_to_yield(r) for r in dict_of_lists_of_annual_return[q]])).mean())
		list_of_formatted_aar_mean.append(formatted_aar_mean)
		# FORMATTING OF ANNUAL RATE OF RETURN
		formatted_ar = format_decimal(annual_rate_of_return)
		list_of_formatted_annual_rate_of_return.append(formatted_ar)
		# FORMATTING OF ANNUAL RATE OF EXCESS RETURN
		formatted_are = format_decimal(annual_rate_of_excess_return)
		list_of_formatted_are.append(formatted_are)
		# formatted_mean = format_decimal(mean_as_yield)


		# formatted_std_dev_daily = format_decimal(std_dev_daily)
		# formatted_std_dev_daily_excess = format_decimal(std_dev_daily_excess)
		# # formatted_std_dev_annual_excess = format_decimal(std_dev_annual_excess)
		# formatted_std_dev_mean = format_decimal(std_dev_mean)


		# formatted_IR_daily = format_decimal(IR_daily)
		# formatted_IR_annual1 = format_decimal(IR_annual1)
		# formatted_IR_annual2 = format_decimal(IR_annual2)
		# formatted_IR_annual3 = format_decimal(IR_annual3)
		# formatted_IR_annual4 = format_decimal(IR_annual4)
		# formatted_IR_mean = format_decimal(mean_of_IR)


		aexr = (np.array(list_of_excess_return)).mean()
		aexr = convert_float_to_yield(aexr)
		formatted_aexr_mean = format_decimal(aexr)
		list_of_formatted_aexr_mean.append(formatted_aexr_mean)

	print()
	print('Total holding period: \t\t\t\t\t\t\t      {} to {}\n'.format(first_date, last_date))
	print('Results for quintile: \t\t\t\t\t 1\t   2\t      3\t         4\t    5')
	print('Total holding period yields:\t\t\t {} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_total_pfy))
	print('AARs (mean of annual returns):\t\t\t {} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_aar_mean))
	print('Annual rates of return:\t\t\t\t {} %, {} %, {} %, {} %, {} %\n'.format(*list_of_formatted_annual_rate_of_return))
	print('Total excess returns:\t\t\t\t {} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_texr))
	print('Average excess returns (mean of excess returns): {} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_aexr_mean))
	print('Annual rates of excess return:\t\t\t {} %, {} %, {} %, {} %, {} %\n'.format(*list_of_formatted_are))
	print('Total return of index:                      \t', formatted_tspy, '%')
	print('AAR of index (mean of index annual returns):\t', formatted_aari, '%')
	print('Annual rate of return index:                \t', formatted_ari, '%\n')
	# print('Mean excess return:    \t ', formatted_mean, '%')
	# print('Total std dev (sample):\t', std_dev_daily_sample)
	# print('Standard deviation (daily):              \t ', formatted_std_dev_daily)
	# print('Standard deviation (daily excess):       \t ', formatted_std_dev_daily_excess)
	print('Volatilities (st. dev. of annual returns):\t {} %, {} %, {} %, {} %, {} %'.format(*list_of_formatted_std_dev_annual))
	# print('Standard deviation (annual excess):      \t ', formatted_std_dev_annual_excess)
	# print('Standard deviation (mean):               \t ', formatted_std_dev_mean, '\n')
	# print('Total IR (sample):     \t', IR_daily_sample)
	# print('Information ratio (d_e / d):             \t ', formatted_IR_daily)
	print('Information ratios:\t\t\t\t {}    {}    {}    {}    {} '.format(*list_of_formatted_IR_daily_excess))
	# print('Information ratio (d_e / a):             \t ', formatted_IR_annual1)
	# print('Information ratio (a / a):               \t ', formatted_IR_annual2)
	# print('Information ratio (a_e / a):             \t ', formatted_IR_annual3)
	# print('Information ratio (a_e / a_e):           \t ', formatted_IR_annual4)
	# print('Information ratio (mean):                \t ', formatted_IR_mean)

	# for i, m in enumerate(list_of_total_summed_matrices):
	# 	dates = stockmarket.dates[last_idx:first_idx]
	# 	dates.reverse()
	# 	plot_returns(m, total_benchmark_index, dates)

	dates = stockmarket.dates[last_idx:first_idx]
	dates.reverse()
	plot_linearity_returns(list_of_total_summed_matrices, total_benchmark_index, dates)

	return


# TODO: gör att frågorna i texten kommer i en annan färg.
def main():
	# Market cap in millions <local currency>.
	min_market_cap = 500
	min_market_cap = float(min_market_cap)

	# If remove is True, companies lacking too much data will be removed. If
	# remove is False, companies lacking too much data will instead be assigned
	# the worst score for that particular parameter.
	remove = False
	weighted = False
	market = 'Stockholm stock exchange (Stockholmsbörsen)'
	years = '2008-2018'
	portfolio_size = 20

	# list_of_unwanted_industries = ['Banks', 'Investment Companies', 'Real Estate', 'Private Equity']
	list_of_unwanted_industries = ['Banks', 'Investment Companies', 'Real Estate', 'Private Equity', 'Diversified Finan Serv']
	list_of_valid_years = ['2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018']
	list_of_parameter_names = ['roe', 'fcfy', 'roic_wacc', 'revenue_growth', 'dividend_yield']
	options = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

	regex_parameters_as_numbers = r'(^[1-5]{1,5}$)'
	regex_years = r'(^([0-9]{4})-([0-9]{4}$))'


	# TODO: 1. Tillval för att skriva ut varje enskilt bolags avkastning under
	#		   året när man skriver ut portföljens avkastning.
	#  		2. Titta på andra marknader. U.S. NASDAQ 100
	# 		3. Grafer. Portföljens avkastning + index avkastning.
	# 		4. ROIC/WACC blev omskrivet till ROIC, men vi ändrade tillbaka.
	#		5. Tillval till att investera mer i topprankade bolaget.
	# 		6. Kör Information Ratio istället för Sharpe Ratio.
	# 		7. Eventuellt ta bort Fingerprint.
	choice = True
	while choice:
		print('\nCurrent program rules')
		if market == 'Stockholm stock exchange (Stockholmsbörsen)':
			ratios_file = 'stockholm_ratios_2004-01-03_to_2018-01-03'
			daily_prices_file = 'stockholm_total_return_index_gross_dividends_2004-01-03_to_2018-01-03'
			index_file = 'sixprx_2004-01-03_to_2018-01-03'
			print('Remove if lacks data:\t{}\nWeighted investment: \t{}\nMinimum market cap: \tSEK {} million\nStock market: \t\t{}\nBacktesting period: \t{}\nPortfolio size: \t{}'.format(remove, weighted, int(min_market_cap), market, years, portfolio_size))
		elif market == 'U.S. NASDAQ':
			ratios_file = 'nasdaq_ratios_2004-04-30_to_2018-04-30'
			daily_prices_file = 'nasdaq_total_return_index_gross_dividends_2004-04-30_to_2018-04-30'
			index_file = 'nasdaq_100_stock_index_2004-04-30_to_2018-04-30'
			print('Remove if lacks data:\t{}\nWeighted investment: \t{}\nMinimum market cap: \tUSD {} million\nStock market: \t\t{}\nBacktesting period: \t{}\nPortfolio size: \t{}'.format(remove, weighted, int(min_market_cap), market, years, portfolio_size))

		choice = menu(options)

		if choice == '0':
			print('You chose to exit the program. Goodbye!\n')
			quit()


		# 1. Create portfolio today (i.e. January of 2018)
		elif choice == '1':
			year = '2018'
			stockmarket = filter_and_sort_stockmarket(ratios_file,
													  daily_prices_file,
													  index_file,
													  min_market_cap,
													  list_of_unwanted_industries,
													  year,
													  remove)
			print()
			stockmarket.print_this_many_companies(portfolio_size)
			print('\n*************************************************************************************')


		# 2. Create portfolio for a specific year and specify parameters yourself
		elif choice == '2':
			year = user_input_year(list_of_valid_years)
			parameters_as_numbers = user_input_parameters(regex_parameters_as_numbers)
			parameters_as_strings = get_list_of_parameter_names(parameters_as_numbers)
			string_of_parameters = format_parameter_string(parameters_as_strings)
			print('You chose {}.\n'.format(string_of_parameters))

			number_of_parameters = len(parameters_as_strings)
			s = str(number_of_parameters)
			set_weights = input('Would you like to set the weights for the parameters you chose? If yes, enter\n"yes". If not, enter anything other than "yes" (in this case they will be\nassigned equal weights, i.e. a weight of 1/{}). Your answer: '.format(s))
			set_weights = set_weights.strip()
			set_weights = set_weights.lower()

			if set_weights == 'q' or set_weights == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

			if set_weights == 'yes':
				dict_of_parameters_and_weights = user_input_weights(parameters_as_strings)
			else:
				print('\nYou chose not to change the weights. The parameters will all be weighted with\nan equal weight of 1/{}.'.format(s))
				dict_of_parameters_and_weights = {}
				for parameter in parameters_as_strings:
					dict_of_parameters_and_weights[parameter] = round(1/number_of_parameters, 2)

			stockmarket = filter_and_sort_stockmarket(ratios_file,
													  daily_prices_file,
													  index_file,
													  min_market_cap,
													  list_of_unwanted_industries,
													  year,
													  remove,
													  dict_of_parameters_and_weights)
			print()
			stockmarket.print_this_many_companies(portfolio_size)

			print('\n*************************************************************************************')


		# 3. Backtest H&A model from 2008 to 2018
		elif choice == '3':
			plot = False
			v = True
			print()
			backtest(ratios_file, daily_prices_file, index_file, min_market_cap,
					 list_of_unwanted_industries, years, portfolio_size, remove,
					 plot=plot, v=v, weighted=weighted)

			print('\n*************************************************************************************')


		elif choice == '4':
			plot = True
			v = True
			print()
			backtest(ratios_file, daily_prices_file, index_file, min_market_cap,
					 list_of_unwanted_industries, years, portfolio_size, remove,
					 plot=plot, v=v, weighted=weighted)

			print('\n*************************************************************************************')


		elif choice == '5':
			parameters_as_numbers = user_input_parameters(regex_parameters_as_numbers)
			parameters_as_strings = get_list_of_parameter_names(parameters_as_numbers)
			string_of_parameters = format_parameter_string(parameters_as_strings)
			print('You chose {}.\n'.format(string_of_parameters))

			number_of_parameters = len(parameters_as_strings)
			s = str(number_of_parameters)
			set_weights = input('Would you like to set the weights for the parameters you chose? If yes, enter\n"yes". If not, enter anything other than "yes" (in this case they will be\nassigned equal weights, i.e. a weight of 1/{}). Your answer: '.format(s))
			set_weights = set_weights.strip()
			set_weights = set_weights.lower()

			if set_weights == 'q' or set_weights == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

			if set_weights == 'yes':
				dict_of_parameters_and_weights = user_input_weights(parameters_as_strings)
			else:
				print('\nYou chose not to change the weights. The parameters will all be weighted with\nan equal weight of 1/{}.'.format(s))
				dict_of_parameters_and_weights = {}
				for parameter in parameters_as_strings:
					dict_of_parameters_and_weights[parameter] = round(1/number_of_parameters, 2)

			plot = False
			v = True

			print()
			backtest(ratios_file, daily_prices_file, index_file, min_market_cap,
					 list_of_unwanted_industries, years, portfolio_size, remove,
					 plot=plot, v=v, weighted=weighted,
					 dict_of_parameters_and_weights=dict_of_parameters_and_weights)

			print('\n*************************************************************************************')


		elif choice == '6':
			parameters_as_numbers = user_input_parameters(regex_parameters_as_numbers)
			parameters_as_strings = get_list_of_parameter_names(parameters_as_numbers)
			string_of_parameters = format_parameter_string(parameters_as_strings)
			print('You chose {}.\n'.format(string_of_parameters))

			number_of_parameters = len(parameters_as_strings)
			s = str(number_of_parameters)
			set_weights = input('Would you like to set the weights for the parameters you chose? If yes, enter\n"yes". If not, enter anything other than "yes" (in this case they will be\nassigned equal weights, i.e. a weight of 1/{}). Your answer: '.format(s))
			set_weights = set_weights.strip()
			set_weights = set_weights.lower()

			if set_weights == 'q' or set_weights == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

			if set_weights == 'yes':
				dict_of_parameters_and_weights = user_input_weights(parameters_as_strings)
			else:
				print('\nYou chose not to change the weights. The parameters will all be weighted with\nan equal weight of 1/{}.'.format(s))
				dict_of_parameters_and_weights = {}
				for parameter in parameters_as_strings:
					dict_of_parameters_and_weights[parameter] = round(1/number_of_parameters, 2)

			plot = True
			v = True

			print()
			backtest(ratios_file, daily_prices_file, index_file, min_market_cap,
					 list_of_unwanted_industries, years, portfolio_size, remove,
					 plot=plot, v=v, weighted=weighted,
					 dict_of_parameters_and_weights=dict_of_parameters_and_weights)

			print('\n*************************************************************************************')


		# En viktning måste vara över 0.08?
		# 5. Find optimal parameter-weight combinations, i.e. the combinations
		# 	 of parameters and weights which yield the highest returns. The
		#	 resulting best combinations will be written to a .csv-file.
		#	 WARNING: extremely long runtime!'
		elif choice == '7':
			input_file = 'weight_permutations_that_sum_up_to_1_with_0_and_interval_001.csv'
			input_file_path = os.getcwd() + '/inputfiles/' + input_file

			output_folder_path = os.getcwd() + '/outputfiles/'
			directory_contents = os.listdir(output_folder_path)
			directory_contents = [x for x in directory_contents if x.startswith('optimization_results_interval001')]
			if directory_contents:
				for content in directory_contents[:]:
					if remove:
						if 'removeNO' in content:
							directory_contents.remove(content)
					elif not remove:
						if 'removeYES' in content:
							directory_contents.remove(content)
					elif weighted:
						if 'weightedNO' in content:
							directory_contents.remove(content)
					else:
						if 'weightedYES' in content:
							directory_contents.remove(content)
				directory_contents.sort(reverse=True)
				if directory_contents:
					if os.path.isfile(output_folder_path + directory_contents[0]):
						yes_or_no = input('\nOne or several csv-files of optimal parameter-weight' +
						' combinations\nalready exist and can be found in your "outputfiles"' +
						' folder. If you\nwould like to open the most recent such file, enter "yes": ')
						yes_or_no = yes_or_no.strip()
						yes_or_no = yes_or_no.lower()

						if yes_or_no == 'q' or yes_or_no == 'quit':
							print('You chose to exit the program. Goodbye!\n')
							quit()

						if yes_or_no == 'yes':
							print('You chose to open the file.')
							# https://stackoverflow.com/questions/8220108/how-do-i-check-the-operating-system-in-python
							# https://stackoverflow.com/questions/434597/open-document-with-default-application-in-python
							from sys import platform
							if platform == 'darwin':
								os.system('open '+(output_folder_path + directory_contents[0]))
							if platform == 'win32':
								os.system('start '+(output_folder_path + directory_contents[0]))
							print('\n*************************************************************************************')
							break
						else:
							print('You chose not to open the file.')

			proceed = input('\nThis is the function for finding optimal parameter-weight ' +
			'combinations,\ni.e. the combinations of parameters and weights which ' +
			'yield the highest\nreturns. The results will be written to a csv-file.' +
			' WARNING: very long\nruntime! If you still want to proceed, enter ' +
			'"yes": ')
			proceed = proceed.strip()
			proceed = proceed.lower()

			if proceed == 'q' or proceed == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

			if not proceed == 'yes':
				print('You chose not to proceed.')
				print('\n*************************************************************************************')
				continue

			output_file = 'optimization_results_interval001'
			if remove:
				output_file += '_removeYES'
			else:
				output_file += '_removeNO'
			if weighted:
				output_file += '_weightedYES_'
			else:
				output_file += '_weightedNO_'
			date = str(datetime.datetime.now().date())
			output_file = output_file + date + '.csv'
			output_file_path = os.getcwd() + '/outputfiles/' + output_file

			years = '2008-2018'
			portfolio_size = 20

			if os.path.exists(output_file_path):
				append_or_write = 'a'
				with open(output_file_path, 'r') as output_file:
					output_csv_reader = csv.reader(output_file)
					row_count = sum(1 for row in output_csv_reader)
			else:
				append_or_write = 'w'
				row_count = 0

			with open(input_file_path, 'r') as input_file:
				# input_csv_reader = csv.reader(input_file)
				with open(output_file_path, append_or_write, newline='') as output_file:
					output_csv_writer = csv.writer(output_file, delimiter=';')
					if row_count == 0:
						column_titles = ['10 year total return', 'Excess return (over index)', 'Volatility (as st. dev. of annual returns)', 'Information ratio', 'Parameters and weights']
						output_csv_writer.writerow(column_titles)
					else:
						row_count -= 1

					for row in islice(csv.reader(input_file), row_count, None):
						d = {}
						l = list(row)
						for i, w in enumerate(l):
							if not float(l[i]) == 0:
								d[list_of_parameter_names[i]] = float(l[i])
						tpfy, texr, vola, IR = backtest(ratios_file,
															  daily_prices_file,
															  index_file,
															  min_market_cap,
															  list_of_unwanted_industries,
															  years,
															  portfolio_size,
															  remove,
															  d,
															  plot=False,
															  v=False,
														      weighted=weighted)

						output_list = [str(tpfy) + ' %', str(texr) + ' %',  str(vola) + ' %', str(IR), d]
						output_csv_writer.writerow(output_list)

			print('\nFinding optimal parameter-weight combinations succesful. The' +
			' results can\nbe found in the "outputfiles" folder in the csv-file ' +
			'called\n"{}"\n'.format(output_file_path.strip('/outputfiles/')))
			print('\n*************************************************************************************')


		elif choice == '8':
			remove = user_input_remove()
			weighted = user_input_weighted()
			market = user_input_market()
			min_market_cap = user_input_min_market_cap(market)
			years = user_input_years(list_of_valid_years, regex_years)
			portfolio_size = user_input_portfolio_size()

			print('\n*************************************************************************************')


		elif choice == '9':
			old_remove = remove
			remove = False

			print('\nDuring this test, remove_if_lacks_data will temporarily be set\n' +
				  'to False, since we need to make sure enough companies exist in\n' +
				  'order to divide the 100 best companies into quintiles.')

			parameters_as_numbers = user_input_parameters(regex_parameters_as_numbers)
			parameters_as_strings = get_list_of_parameter_names(parameters_as_numbers)
			string_of_parameters = format_parameter_string(parameters_as_strings)
			print('You chose {}.\n'.format(string_of_parameters))

			number_of_parameters = len(parameters_as_strings)
			s = str(number_of_parameters)
			set_weights = input('Would you like to set the weights for the parameters you chose? If yes, enter\n"yes". If not, enter anything other than "yes" (in this case they will be\nassigned equal weights, i.e. a weight of 1/{}). Your answer: '.format(s))
			set_weights = set_weights.strip()
			set_weights = set_weights.lower()

			if set_weights == 'q' or set_weights == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

			if set_weights == 'yes':
				dict_of_parameters_and_weights = user_input_weights(parameters_as_strings)
			else:
				print('\nYou chose not to change the weights. The parameters will all be weighted with\nan equal weight of 1/{}.'.format(s))
				dict_of_parameters_and_weights = {}
				for parameter in parameters_as_strings:
					dict_of_parameters_and_weights[parameter] = round(1/number_of_parameters, 2)

			# portfolio_size = user_input_portfolio_size()
			portfolio_size = 20
			plot = True
			v = True

			test_linearity(ratios_file, daily_prices_file, index_file, min_market_cap,
					 	   list_of_unwanted_industries, years, portfolio_size, remove,
					 	   plot=plot, v=v, weighted=weighted,
					 	   dict_of_parameters_and_weights=dict_of_parameters_and_weights)

			remove = old_remove

			print('\n*************************************************************************************')


if __name__ == '__main__':
		main()
