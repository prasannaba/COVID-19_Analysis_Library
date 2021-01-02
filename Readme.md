# COVID-19 Analysis Library
COVID-19 analysis on data from **CSSEGISandData** covering all the 150+ countries in the data. <br>
## The library contains two functions:
1. **trends()** <br>
Trends by country, top 10 trends comparison, top 10 and worldwide bar graph. Standalone interactive HTML.
	
2. **daily_report(\*, filename='')**<br>
Daily report bar graph for all countries: Confirmed, Recovered, Deaths, & Active. Incident Rate & Case Fatality Ratio in a table. Standalone interactive HTML

*Important Note:* This library requires internet connection to connect to CSSEGISandData repository on GitHub to download input files. The daily_report() has an option to take the local file, but for latest or recent report it is suggested to connect to CSSEGISandData repository on GitHub.

### 1. trends()

The output from this source code contains following tabs with graphs:  
1. Trends by country
	- Cases:
		- Cumulative
		- Daily
		- Seven day moving average
		- Recovered
		- Death
		- Active
	- Rate & Ratio:
		- Incident Rate
		- Case Fatality Ratio
2. Trends comparison
	- Top 10 countries trends with options for log plot & highlight countries by clicking on countries label
3. Top 10 bar graph and table of data corresponding to graph
4. Worldwide bar graph and table of data corresponding to graph

The source code uses bokeh, panel, holoviews & hvplot modules along with pandas.

The source code reads the following files from CSSEGISandData repository on Github:
	'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
	'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
	'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'

This when executed generates standalone interactive HTML file

### 2. daily_report(*, filename='')

The output from this source code contains: 

1. Daily graphs of Confirmed, Recovered, Deaths, & Active cases.
2. Daily Incident Rate & Case Fatality Ratio in a table.

The source code reads the recent file with the name 'mm-dd-yyyy.csv' from CSSEGISandData repository on Github or from the local file 'mm-dd-yyyy.csv' given by user.<br>
'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/'

This when executed generates standalone interactive HTML file
