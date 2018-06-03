# coding=utf-8

def convert_yield_to_float(input_yield):
	return ((input_yield / 100) + 1)


def convert_float_to_yield(input_float):
	return ((input_float - 1) * 100)


def make_list_of_intermediate_values(smallest, largest):
	l = []
	for v in range(smallest, largest):
		l.append(v)

	return l


def is_float(input):
	try:
		float(input)
	except ValueError:
		return False

	return True


def is_int(input):
	try:
		int(input)
	except ValueError:
		return False

	return True


# Input:    - a list of values,
#           - the index to start the search from,
#           - a boolean specifying whether you want to search by going
#             forward or backward in the list.
# Returns:  - the next valid value.
def fetch_closest_valid_float(input_list, start_from_this_index, forward=True):
	try:
		valid_value = 'invalid_dummy_value'
		i = start_from_this_index
		while not is_float(valid_value):
			valid_value = input_list[i]
			# print(valid_value, i)
			if forward:
				i -= 1
			else:
				i += 1
		valid_value = float(valid_value)
	except Exception as e:
		print(e)
		return

	return valid_value


# This function takes the input years from the user and returns the index for
# each year.
def get_index_years(years_input_string):
	# now = datetime.datetime.now()
	# current_year = now.year
	current_year = 2018
	start_year, end_year = years_input_string.split('-')
	# index_start_year = current_year - int(start_year) + 1
	index_start_year = current_year - int(start_year)
	index_end_year = current_year - int(end_year)

	return index_start_year, index_end_year


# This function takes the input years from the user and returns the index for
# each year.
def get_index_year(year_input_string):
	current_year = 2018
	year = int(year_input_string)
	index_year = current_year - year

	return index_year


def convert_number_into_parameter_name(parameter_as_number):
	if parameter_as_number == '1':
		return 'roe'
	elif parameter_as_number == '2':
		return 'fcfy'
	elif parameter_as_number == '3':
		return 'roic_wacc'
	elif parameter_as_number == '4':
		return 'revenue_growth'
	elif parameter_as_number == '5':
		return 'dividend_yield'


def get_list_of_parameter_names(parameters_as_numbers):
	list_of_parameter_names = list()
	for number in parameters_as_numbers:
		parameter_name = convert_number_into_parameter_name(number)
		list_of_parameter_names.append(parameter_name)

	return list_of_parameter_names


def get_readable_name(parameter_code_name):
	if parameter_code_name == 'roe':
		return 'ROE/STDEV'
	if parameter_code_name == 'fcfy':
		return 'Free Cash Flow Yield'
	if parameter_code_name == 'roic_wacc':
		return 'ROIC/WACC'
	if parameter_code_name == 'revenue_growth':
		return 'Revenue Growth'
	if parameter_code_name == 'dividend_yield':
		return 'Dividend Yield'


def format_parameter_string(list_of_parameter_names):
	s = ''
	for p in list_of_parameter_names:
		s += get_readable_name(p) + ', '
	s = s.strip(', ')
	s = s[::-1]
	s = s.replace(' ,', ' dna ', 1)
	s = s[::-1]

	return s


def format_decimal(dec):
	s = '{:0.3f}'.format(dec)
	while len(s) < 7:
		s = ' ' + s

	return s


def are_valid_years(list_of_valid_years, years):
	start_year, end_year = years.split('-')
	if int(start_year) > int(end_year) or int(start_year) == int(end_year):
		return False
	elif not start_year in list_of_valid_years or not end_year in list_of_valid_years:
		return False
	else:
		return True
