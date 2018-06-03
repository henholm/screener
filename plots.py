def plot_returns(returns, returns_index, xaxislabels):
	import matplotlib
	import matplotlib.pyplot as plt

	plt.title('Total portfolio return over time')
	plt.xlabel('Time')
	plt.ylabel('Return')

	fig = plt.gcf()
	ax = fig.axes[0]

	sm = plt.plot(range(returns.size), returns, label='Portfolio return')
	sp = plt.plot(range(returns_index.size), returns_index, label='Index return')

	# https://stackoverflow.com/questions/32073616/matplotlib-change-color-of-individual-grid-lines
	# https://stackoverflow.com/questions/32245434/matplotlib-hiding-specific-tick-lines
	# Set the dates as tick labels on the x-axis.
	plt.xticks(range(returns.size), xaxislabels, visible=False, rotation=45)
	# Set ticklines and gridlines to be invisible by default on x-axis.
	plt.setp(ax.xaxis.get_ticklines(), visible=False)
	plt.setp(ax.get_xgridlines(), visible=False)
	xlabels = ax.xaxis.get_ticklabels()
	xticklines = ax.xaxis.get_ticklines()
	xgridlines = ax.get_xgridlines()
	# Set the label, grid line and tick line to be visible for the first date.
	xlabels[0].set_visible(True)
	xgridlines[0].set_visible(True)
	xticklines[0].set_visible(True)
	# Every time the for-loop reaches a new year, set as visible.
	previous = xlabels[0].get_text()[3]
	for i, label in enumerate(xlabels):
		if label.get_text()[3] != previous:
			label.set_visible(True)
			xgridlines[i].set_visible(True)
			xticklines[i].set_visible(True)
		previous = label.get_text()[3]

	# Format the labels on the y-axis.
	y_vals = ax.get_yticks()
	ax.set_yticklabels(['{:3.2f}%'.format((x-1)*100) for x in y_vals])

	plt.legend(handles=[sm[0],sp[0]])
	plt.grid(True)
	plt.tight_layout()
	plt.show()

	return


def plot_linearity_returns(list_of_returns_lists, returns_index, xaxislabels):
	import matplotlib
	import matplotlib.pyplot as plt

	plt.title('Total portfolio return over time')
	plt.xlabel('Time')
	plt.ylabel('Return')

	fig = plt.gcf()
	ax = fig.axes[0]

	sm_list = []
	for i, returns_list in enumerate(list_of_returns_lists):
		label = 'Quintile {}'.format(i+1)
		sm = plt.plot(range(returns_list.size), returns_list, label=label)
		sm_list.append(sm)

	sp = plt.plot(range(returns_index.size), returns_index, label='Index return')

	# https://stackoverflow.com/questions/32073616/matplotlib-change-color-of-individual-grid-lines
	# https://stackoverflow.com/questions/32245434/matplotlib-hiding-specific-tick-lines
	# Set the dates as tick labels on the x-axis.
	plt.xticks(range(returns_index.size), xaxislabels, visible=False, rotation=45)
	# Set ticklines and gridlines to be invisible by default on x-axis.
	plt.setp(ax.xaxis.get_ticklines(), visible=False)
	plt.setp(ax.get_xgridlines(), visible=False)
	xlabels = ax.xaxis.get_ticklabels()
	xticklines = ax.xaxis.get_ticklines()
	xgridlines = ax.get_xgridlines()
	# Set the label, grid line and tick line to be visible for the first date.
	xlabels[0].set_visible(True)
	xgridlines[0].set_visible(True)
	xticklines[0].set_visible(True)
	# Every time the for-loop reaches a new year, set as visible.
	previous = xlabels[0].get_text()[3]
	for i, label in enumerate(xlabels):
		if label.get_text()[3] != previous:
			label.set_visible(True)
			xgridlines[i].set_visible(True)
			xticklines[i].set_visible(True)
		previous = label.get_text()[3]

	# Format the labels on the y-axis.
	y_vals = ax.get_yticks()
	ax.set_yticklabels(['{:3.2f}%'.format((x-1)*100) for x in y_vals])

	plt.legend(handles=[sm_list[0][0], sm_list[1][0], sm_list[2][0], sm_list[3][0], sm_list[4][0],sp[0]])
	plt.grid(True)
	plt.tight_layout()
	plt.show()

	return
