# coding=utf-8

import re
from util import *


# Prints a menu asking the user for input. Returns user input.
def menu(options):
	print('' +
		  '\n0. Quit (you can also enter "q" or "quit" at any time to quit).' +
		  '\n1. Create portfolio today (last available date in the input file).' +
		  '\n2. Create portfolio for a specific year. Specify the parameters ' +
		  '\n   used and their respective weights yourself.' +
		  '\n3. Backtest H&A model.' +
		  '\n4. Same as 3, but also plot the results.' +
		  '\n5. Backtest a model. Specify the parameters used and their ' +
		  '\n   respective weights yourself.' +
		  '\n6. Same as 5, but also plot the results.' +
		  '\n7. Find optimal parameter-weight combinations.' +
		  '\n8. Set the program rules.' +
		  '\n9. Test for portfolio linearity.')
	choice = input('Select an option from the menu and press enter:\t')
	choice = choice.strip()
	choice = choice.lower()

	if choice == 'q' or choice == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	while choice not in options:
		choice = input('Invalid input. Please try again: ')
		choice = choice.strip()
		choice = choice.lower()

		if choice == 'q' or choice == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

	print('You chose option {}.'.format(choice))

	return choice


def user_input_year(list_of_valid_years):
	print()
	year = input('Enter the year for which you want to create a portfolio: ')
	year = year.strip()
	year = year.lower()

	if year == 'q' or year == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	while year not in list_of_valid_years:
		year = input('Invalid year. Please enter a year from 2008 up to 2018: ')
		year = year.strip()
		year = year.lower()

		if year == 'q' or year == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

	print('You chose {}.'.format(year))

	return year


def user_input_years(list_of_valid_years, regex):
	print()
	years = input('5. Enter the timespan for which you would like to backtest ' +
				  '(e.g. 2009-2014): ')
	years = years.strip()
	years = years.lower()

	if years == 'q' or years == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	valid_input = False
	while not valid_input:
		if re.match(regex, years):
			if are_valid_years(list_of_valid_years, years):
				valid_input = True
			else:
				years = input('Invalid input. Please try again: ')
				years = years.strip()
				years = years.lower()

				if years == 'q' or years == 'quit':
					print('You chose to exit the program. Goodbye!\n')
					quit()

		else:
			years = input('Invalid input. Please try again: ')
			years = years.strip()
			years = years.lower()

			if years == 'q' or years == 'quit':
				print('You chose to exit the program. Goodbye!\n')
				quit()

	print('You chose {}.'.format(years))

	return years


# Måste vara mellan 1 och oändligheten.
def user_input_portfolio_size():
	print()
	portfolio_size = 0
	while not int(portfolio_size) > 0:
		portfolio_size = input('6. Select how many stocks you want in your portfolio: ')
		portfolio_size = portfolio_size.strip()
		portfolio_size = portfolio_size.lower()

		if portfolio_size == 'q' or portfolio_size == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

		if not is_int(portfolio_size):
			portfolio_size = -1
		else:
			portfolio_size = int(portfolio_size)

	print('You chose a portfolio size of {}. If less than {} companies are'.format(portfolio_size, portfolio_size))
	print('displayed, too few companies satisfied our criteria.\n')

	return portfolio_size


def user_input_parameters(regex):
	print()
	parameters_as_numbers = input('' +
	'Which parameters do you want to include in your model?\n' +
	'You can choose between the following:\n' +
	'1. ROE/STDEV\n' +
	'2. Free Cash Flow Yield\n' +
	'3. ROIC/WACC\n' +
	'4. Revenue Growth\n' +
	'5. Dividend Yield\n' +
	'(E.g. 135 if you want ROE/STDEV, ROIC/WACC & Dividend Yield): ')
	parameters_as_numbers = parameters_as_numbers.strip()
	parameters_as_numbers = parameters_as_numbers.lower()

	if parameters_as_numbers == 'q' or parameters_as_numbers == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	parameters_as_numbers = parameters_as_numbers.replace(' ', '')
	while not re.match(regex, parameters_as_numbers) or (len(list(parameters_as_numbers)) != len(set(list(parameters_as_numbers)))):
		parameters_as_numbers = input('Invalid input. Please try again: ')
		parameters_as_numbers = parameters_as_numbers.strip()
		parameters_as_numbers = parameters_as_numbers.lower()

		if parameters_as_numbers == 'q' or parameters_as_numbers == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

		parameters_as_numbers = parameters_as_numbers.replace(' ', '')

	return parameters_as_numbers


# Vi skulle kunna lägga till en check som tittar att de summeras till 1.
def user_input_weights(list_of_parameters):
	dict_of_parameters_and_weights = {}
	weight_sum = 0
	print()
	print('Each weight must be between 0 and 1. Decimals should be written in the\nfollowing format: "0.3", i.e. not using the comma sign: "0,3".')
	for parameter in list_of_parameters:
		weight = 'dummy_value'
		while not is_float(weight) or not (0 <= float(weight) <= 1):
			if weight == 'dummy_value':
				weight = input('Enter the weight for {}: '.format(get_readable_name(parameter)))
				weight = weight.strip()
				weight = weight.lower()

				if weight == 'q' or weight == 'quit':
					print('You chose to exit the program. Goodbye!\n')
					quit()
			else:
				weight = input('Invalid value. Try again: ')
				weight = weight.strip()
				weight = weight.lower()

				if weight == 'q' or weight == 'quit':
					print('You chose to exit the program. Goodbye!\n')
					quit()

		weight = float(weight)
		dict_of_parameters_and_weights[parameter] = weight
		weight_sum += weight

	for parameter, weight in dict_of_parameters_and_weights.items():
		print('The weight for {} has been set to {}.'.format(get_readable_name(parameter), str(weight)))

	if weight_sum != 1:
		proceed = input('Your weights do not add up to 1. Do you want to proceed anyway? ')
		proceed = proceed.strip()
		proceed = proceed.lower()

		if proceed == 'q' or proceed == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

		if not proceed == 'yes':
			print('Okay. Then try again.')
			dict_of_parameters_and_weights = user_input_weights(list_of_parameters)

	return dict_of_parameters_and_weights


def user_input_remove():
	remove = input('\n1. Would you like companies lacking too much data to be removed, ' +
	 			   'or would you\nrather assign them the worst rank (for ' +
				   'the parameter where they lack data)?\nIf you want them to be ' +
				   'removed, enter "yes": ')
	remove = remove.strip()
	remove = remove.lower()
	if remove == 'q' or remove == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	# If remove is True, companies lacking too much data will be removed. If
	# remove is False, companies lacking too much data will instead be assigned
	# the worst score for that particular parameter.
	if remove == 'yes':
		remove = True
		print('Companies lacking too much data will be removed.')
	else:
		remove = False
		print('Companies lacking too much data will be assigned the worst rank.')

	return remove


def user_input_weighted():
	weighted = input('\n2. Would you like to invest proportionally more in the top-ranked ' +
					 'stocks in your\nportfolio? If you do, enter "yes": ')
	weighted = weighted.strip()
	weighted = weighted.lower()

	if weighted == 'q' or weighted == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	if weighted == 'yes':
		weighted = True
		print('You will invest proportionally more in stocks with a higher rank.')
	else:
		weighted = False
		print('You will invest equally much in each stock in your portfolio.')

	return weighted


def user_input_market():
	market = input('\n3. Would you like to analyze the Stockholm stock exchange or the ' +
					 'U.S. NASDAQ\nstock exchange? Enter "yes" for the Stockholm stock exhange. ' +
					 'Enter anything other\nthan "yes" for the US market: ')
	market = market.strip()
	market = market.lower()

	if market == 'q' or market == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	if market == 'yes':
		market = 'Stockholm stock exchange (Stockholmsbörsen)'
		print('You chose the Stockholm stock exchange.')
	else:
		market = 'U.S. NASDAQ'
		print('You chose the U.S. NASDAQ stock exchange.')

	return market


def user_input_min_market_cap(market):
	if market == 'Stockholm stock exchange (Stockholmsbörsen)':
		min_market_cap = input('\n4. Enter your desired minimum market cap (in millions SEK, e.g. "500"): ')
	elif market == 'U.S. NASDAQ':
		min_market_cap = input('\n4. Enter your desired minimum market cap (in millions USD, e.g. "500"): ')
	min_market_cap = min_market_cap.strip()
	min_market_cap = min_market_cap.lower()

	if min_market_cap == 'q' or min_market_cap == 'quit':
		print('You chose to exit the program. Goodbye!\n')
		quit()

	while not is_int(min_market_cap) or int(min_market_cap) < 0:
		min_market_cap = input('Invalid value. Try again.')
		min_market_cap = min_market_cap.strip()
		min_market_cap = min_market_cap.lower()

		if min_market_cap == 'q' or min_market_cap == 'quit':
			print('You chose to exit the program. Goodbye!\n')
			quit()

	min_market_cap = int(min_market_cap)
	print('You chose a minimum market cap of SEK {} million.'.format(min_market_cap))

	return min_market_cap
