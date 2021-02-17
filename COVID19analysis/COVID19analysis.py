"""
The MIT License (MIT)

Copyright (c) 2020-2021 Prasanna Badami

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Description:
COVID-19 analysis on data from CSSEGISandData repository on GitHub.
This covers all the 150+ countries, provinces & counties.
This generates interactive HTML reports showing trends confirmed, active, recovery, death, incident rate & case fatality
ratio, top 10 comparison, top 10 & worldwide bar graphs.

Important Note: This library/source code requires internet connection to connect to CSSEGISandData repository on GitHub
to download input files. The fucntion daily_report() has an option to take the local file, but for latest or recent
report it is suggested to connect to CSSEGISandData repository on GitHub.

@author: Prasanna Badami
"""

__version__ = '1.0.1'

import pandas as pd
import collections
import numpy as np
from datetime import datetime, timedelta

from numpy import nan
import os
import errno
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FactorRange, Div, HoverTool, FuncTickFormatter, NumeralTickFormatter, \
    Select, CustomJS, DataTable, TableColumn
from bokeh.resources import INLINE
from bokeh.layouts import gridplot
from bokeh.transform import factor_cmap
import holoviews as hv
import panel as pn
# noinspection PyUnresolvedReferences
import hvplot.pandas
from tqdm import tqdm

hv.extension('bokeh')
pn.extension()

__all__ = ['trends', 'daily_report']


# keyword argument 'filename' is optional, optional mean default is already assigned in function definition
def daily_report(*, filename=''):
    """
    Important Note: This function requires internet connection to connect to CSSEGISandData repository on GitHub or local file,
    else it will raise error.

    Daily interactive HTML report for all countries, provinces & counties, confirmed, active, recovery, death,
    incident rate, case fatality ratio.

    Input:
    local downloaded mm-dd-yyyy.csv or no arguments(reads latest mm-dd-yyyy.csv directly from CSSEGISandData repository on GitHub)

    :return: Daily interactive HTML report for all countries, provinces & counties

    """
    date_on_file_today = datetime.today().strftime('%m-%d-%Y')
    date_on_file_yesterday = (datetime.today() - timedelta(days=1)).strftime('%m-%d-%Y')
    date_on_file_day_b4_yesterday = (datetime.today() - timedelta(days=2)).strftime('%m-%d-%Y')
    date_on_save_html = ' '
    # if filename is not empty, check for file integrity
    with tqdm(total=8, desc='Daily report status', bar_format='{l_bar}{bar}{r_bar}', colour='yellow') as progress_bar:
        progress_bar.update(1)
        if filename != '':
            if '.csv' in filename:
                if os.path.isfile(filename):
                    df_daily_report = pd.read_csv(filename)
                    date_on_save_html = filename.split('.')[0]
                    #     check for column names, if present in csv file else return error
                    if {'Admin2', 'Province_State', 'Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active',
                            'Incident_Rate', 'Case_Fatality_Ratio'}.issubset(df_daily_report.columns):
                        pass
                    else:
                        raise NameError('Admin2', 'Province_State', 'Country_Region', 'Confirmed', 'Deaths',
                                        'Recovered',
                                        'Active', 'Incident_Rate', 'Case_Fatality_Ratio',
                                        'one or any of these columns not '
                                        'found in the csv file')
                else:
                    # df_daily_report = pd.DataFrame()
                    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
            else:
                raise NameError('Filename extension missing, takes name of valid csv file with extension')
        else:
            # First try to get file with today's date, if not available,
            # try with yesterday's date, if not available,
            # try with day before yesterday's date, if not available
            # assign empty dataframe to df_daily_report, this dataframe is for checked contents in next cell.
            url_dr = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/'
            try:
                df_daily_report = pd.read_csv(url_dr + date_on_file_today + '.csv')
                date_on_save_html = date_on_file_today
                # print('Selected %s.csv' % date_on_file_today)
            except:
                try:
                    df_daily_report = pd.read_csv(url_dr + date_on_file_yesterday + '.csv')
                    date_on_save_html = date_on_file_yesterday
                    # print('Selected %s.csv' % date_on_file_yesterday)
                except:
                    try:
                        df_daily_report = pd.read_csv(url_dr + date_on_file_day_b4_yesterday + '.csv')
                        date_on_save_html = date_on_file_day_b4_yesterday
                        # print('Selected %s.csv' % date_on_file_day_b4_yesterday)
                    except:
                        # 'HTTPError: HTTP Error 404: File Not Found', assign empty dataframe
                        df_daily_report = pd.DataFrame()

        progress_bar.update(1)

        if df_daily_report.empty:
            raise FileNotFoundError('Input file not found on the server or internet connection unavailable')
        else:
            # x = 'Categories', y = 'Country_Province_State', source = master_source

            # df_drft: dataframe_DailyReportFilteredCopy, we are interested in columns filtered df_drfc is used to create
            # dictionary, which in turn is used to create ColumnDataSource for plots. Logic here is: to have a
            # categorical column 'categories' & columns for every country, country_province & country_province_admin2
            # corresponding to each category. default is added for displaying first plot to display when standalone HTML
            # output is opened.. here my home country & province are selected as default. color column is added to fill
            # bar color for each 'categories' in bar plot
            df_drfc = df_daily_report.filter(
                ['Admin2', 'Province_State', 'Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active',
                 'Incident_Rate', 'Case_Fatality_Ratio']).copy()

            ddict = dict(
                {'categories': ['Confirmed', 'Recovered', 'Deaths', 'Active', 'Incident_Rate', 'Case_Fatality_Ratio']})
            for i, j, k, l, m, n, o, p, q in zip(df_drfc.Country_Region.tolist(), df_drfc.Province_State.tolist(),
                                                 df_drfc.Admin2.tolist(),
                                                 df_drfc.Confirmed.tolist(), df_drfc.Recovered.tolist(),
                                                 df_drfc.Deaths.tolist(), df_drfc.Active.tolist(),
                                                 df_drfc.Incident_Rate.round().tolist(),
                                                 df_drfc.Case_Fatality_Ratio.round(2).tolist()
                                                 ):
                ddict.update({str(i) + '_' + str(j) + '_' + str(k): [l, m, n, o, p, q]})
                if str(i) + '_' + str(j) + '_' + str(k) == 'India_Karnataka_nan':
                    ddict.update({'default': [l, m, n, o, p, q]})
            ddict.update({'color': ['royalblue', 'lawngreen', 'red', 'orange', 'skyblue', 'blue']})

            dsource = ColumnDataSource(ddict)

            #     for select box provinces based on country
            provinces_df = df_daily_report.pivot(columns='Country_Region', values='Province_State')

            #     for select box admin2 based on province
            admin2_df = df_daily_report.pivot(columns='Province_State', values='Admin2')

            #     filter out all 'nan' in 'admin2 dataframe', because 'Province_State' do have 'nan' in 'Admin2'
            admin2_df.drop(columns=nan, inplace=True)

            #     for select box country
            countries_region_list = df_daily_report['Country_Region'].unique().tolist()

            #     last update is used in plot title & footer
            last_update = df_daily_report['Last_Update'][0]

            progress_bar.update(1)

            hover_tool2 = HoverTool(tooltips=[('Metric', '@categories'), ('Cases', '@default{0,}')])

            tp = figure(x_range=['Confirmed', 'Recovered', 'Deaths', 'Active'], width=930, height=600,
                        tools=[hover_tool2],
                        toolbar_location=None)

            tp.vbar(x='categories', top='default', width=0.4, line_width=5,
                    fill_color='color', line_color='white', source=dsource)

            #     tp.xaxis.major_label_orientation = 45

            tp.xaxis.major_label_text_font_style = 'bold'

            tp.y_range.start = 0
            tp.yaxis.formatter = NumeralTickFormatter(format='a')
            tp.yaxis.axis_label = 'COVID-19 Cases'
            tp.yaxis.axis_label_text_font_style = 'bold'
            tp.yaxis.major_label_text_font_style = 'bold'

            tp.title.text = 'Daily Report:' + ' | ' + 'India_Karnataka' + ' | ' + 'Incident Rate: ' + str(
                round(dsource.data['default'][4])) + ' | ' + 'Case Fatality Ratio: ' + str(
                round(dsource.data['default'][5], 2)) + ' | ' + 'Last update: ' + str(last_update)

            #     datatable used to display plot data based on each selection (Counrty, Province & Admin2) by user
            tablecolumns = [TableColumn(field='categories', title='Category'),
                            TableColumn(field='default', title='COVID-19 Cases')]

            datatable = DataTable(source=dsource, columns=tablecolumns, width=300, height=300)

            #     Select box for Country
            s_countries = Select(title='Country',
                                 options=countries_region_list, value='India',
                                 width=250,
                                 )
            #     Select box for Provinces
            s_provinces = Select(title='Province',
                                 options=provinces_df['India'].dropna().tolist(), value='Karnataka',
                                 width=250
                                 )
            #     Select box for Admin2
            s_admin2 = Select(title='Admin2',
                              options=[],
                              width=250
                              )
            #     footer for plot
            footer = Div(text="""Graphic: Prasanna Badami 
                                <div>Source: Center for Systems Science & Engineering, Johns Hopkins University</div> 
                                <div>Last update: {} </div> 
                                <div style = "font-size:12px"> Note:</div>
                                <div style = "font-size:12px"><i><t>Incident rate is calculated as confirmed cases per 100,000 population.</i></div>
                                <div style = "font-size:12px"><i> Case fatality ratio is the ratio of deaths to confirmed cases.</i></div>
                                """.format(last_update),
                         width=925,
                         background='white',
                         #                  style={'font-family': 'Helvetica',
                         #                         'font-style' : 'italic',
                         #                         'font-size' : '12px',
                         #                         'color': 'black',
                         #                         'font-weight': 'bold'
                         #                        },
                         )

            progress_bar.update(1)

            #     Custom JavaScript for select box country
            call_country = CustomJS(args={'s_states': s_provinces, 's_counties': s_admin2,
                                          'states': ColumnDataSource(provinces_df),
                                          'counties': ColumnDataSource(admin2_df),
                                          'source': dsource, 'dtable': datatable,
                                          'lastupdate': last_update,
                                          'pt': tp
                                          },
                                    code="""
    
                                           // Javascript code
    
                                           var category
                                           var tcategory = cb_obj.value
                                           var province = 'nan'
                                           var admin = 'nan'
    
                                              // cb_obj.value contains value of s_countries: name of a country
                                              // Filter out NaN values
                                            var foptions1 = states.data[cb_obj.value].filter(function(value, index, self){return value != 'NaN'})
                                            var poptions = foptions1.filter(function(value, index, self){return self.indexOf(value) == index})
                                            s_states.options = poptions
    
                                           if(s_states.options[0] == undefined){
                                                s_counties.options = poptions
                                                admin = 'nan'
                                                province = 'nan'
                                           }
                                           else{
                                                province = s_states.options[0]
                                                s_states.value = s_states.options[0] 
                                                var foptions2 = counties.data[s_states.options[0]].filter(function(value, index, self){return value != 'NaN'})
                                                var coptions = foptions2.filter(function(value, index, self){return self.indexOf(value) == index})
                                                s_counties.options = coptions
    
                                                if (s_counties.options[0] == undefined){
                                                    admin = 'nan'
                                                }
                                                else{
                                                    admin = s_counties.options[0]                     
                                                }
    
                                           }
                                            category = tcategory.concat('_', province, '_', admin)
    
                                              // if the province for country is null then counties will also be null, if not null assign counties in Selectbox admin2
                                              // if counties are null, assign that to Selectbox admin2, this will most probably be updated to disable Selectbox itself
    
                                             source.data['default'] = source.data[category]
                                             source.change.emit()
                                             dtable.columns[1].field = category
                                             dtable.change.emit()
                                             if(province != 'nan' && admin != 'nan'){
                                                 pt.title.text = 'Daily Report:' + ' | ' + category + ' | ' 
                                                                 + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                                 + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                                 + ' | ' + 'Last update: ' + lastupdate
    
                                             }
                                             else if(province == 'nan' && admin == 'nan'){
                                                 pt.title.text = 'Daily Report:' + ' | ' + tcategory + ' | ' 
                                                                 + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                                 + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                                 + ' | ' + 'Last update: ' + lastupdate
                                             }
                                             else if(province != 'nan'){
                                                 pt.title.text = 'Daily Report:' + ' | ' + tcategory + ' _ ' + province + ' | '
                                                                 + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                                 + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                                 + ' | ' + 'Last update: ' + lastupdate
                                             }
                                             else{
                                              // do nothing
                                             }
                                             pt.visible = true
    
                                           """
                                    )

            #     calls Custom JavaScript call_country whenever value is changed in select box country
            s_countries.js_on_change('value', call_country)

            progress_bar.update(1)

            #     Custom JavaScript for select box provinces
            call_provinces = CustomJS(args={'countries': s_countries, 's_states': s_provinces, 's_counties': s_admin2,
                                            'counties': ColumnDataSource(admin2_df),
                                            'source': dsource, 'dtable': datatable,
                                            'lastupdate': last_update,
                                            'pt': tp
                                            },
                                      code="""
                                             if (cb_obj.value != null){
                                              var category
                                              var admin
                                              var province = s_states.value
                                              var tcategory = countries.value
                                              var coptions = counties.data[cb_obj.value].filter(function(value, index, self){return value != 'NaN'})
                                              var ucoptions = coptions.filter(function(value, index, self){return self.indexOf(value) == index})
    
                                              s_counties.options = ucoptions
    
                                              if(s_counties.options[0] == undefined){
                                                    s_counties.value = null
                                                    admin = 'nan'
                                              }
                                              else{
                                                  s_counties.value = s_counties.options[0]
                                                  admin = s_counties.options[0]
                                              }
    
                                              category = tcategory.concat('_',province, '_', admin)
                                              // if the province for country is null then counties will also be null, if not null assign counties in Selectbox admin2
                                              // if counties are null, assign that to Selectbox admin2, this will most probably be updated to disable Selectbox itself
    
                                             source.data['default'] = source.data[category]
                                             source.change.emit()
                                             dtable.columns[1].field = category
                                             dtable.change.emit()
                                             if (admin == 'nan'){
                                                 pt.title.text = 'Daily Report:' + ' | ' + tcategory + '_' + province + ' | ' 
                                                                 + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                                 + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                                 + ' | ' + 'Last update: ' + lastupdate
                                             }
                                             else{
                                                 pt.title.text = 'Daily Report:' + ' | ' + category + ' | ' 
                                                                 + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                                 + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                                 + ' | ' + 'Last update: ' + lastupdate
                                             }
                                             pt.visible = true
                                             }
                                            """
                                      )
            #     calls Custom JavaScript call_provinces whenever value is changed in select box province
            s_provinces.js_on_change('value', call_provinces)

            progress_bar.update(1)

            #     Custom JavaScript for select box admin2
            call_admin2 = CustomJS(args={'countries': s_countries, 's_states': s_provinces, 's_counties': s_admin2,
                                         'source': dsource, 'dtable': datatable,
                                         'lastupdate': last_update,
                                         'pt': tp
                                         },
                                   code="""
                                         if (cb_obj.value != null){
                                             var category
                                             var admin = cb_obj.value
                                             var province = s_states.value
                                             var tcategory = countries.value
    
                                             category = tcategory.concat('_', province, '_', admin)
                                          // alert(category) 
                                          // if the province for country is null then counties will also be null, if not null assign counties in Selectbox admin2
                                          // if counties are null, assign that to Selectbox admin2, this will most probably be updated to disable Selectbox itself
    
                                             source.data['default'] = source.data[category]
                                             source.change.emit()
                                             dtable.columns[1].field = category
                                             dtable.change.emit()
                                             pt.title.text = 'Daily Report:' + ' | ' + category + ' | ' 
                                                             + 'Incident Rate: ' + Math.round(source.data[category][4]) + ' | '
                                                             + 'Case Fatality Ratio: ' + parseFloat(source.data[category][5]).toFixed(2)
                                                             + ' | ' + 'Last update: ' + lastupdate
                                             pt.xaxis.axis_label = 'category'
                                             pt.visible = true
                                             }
    
                                          """
                                   )
            #     calls Custom JavaScript call_admin2 whenever value is changed in select box admin2
            s_admin2.js_on_change('value', call_admin2)

            #     Arrange JavaScript in order for display
            pn_dashboard = pn.Column(pn.Row(s_countries, s_provinces, s_admin2), pn.Column(pn.Row(tp, datatable)),
                                     footer,
                                     background='aliceblue')
        progress_bar.update(1)

        # To standalone interactive HTML,
        pn_dashboard.save('COVID-19_Daily_Report_JS_' + str(date_on_save_html) + '.html',
                          resources=INLINE,
                          embed=True,
                          title='Daily Report'
                          )
        print('Interactive ' + 'COVID-19_Daily_Report_JS_' + str(
            date_on_save_html) + '.html saved in the local directory')
        # For server deployment
        # pn_dashboard.servable(title='COVID-19_Daily_Report_All_Regions_' + str(date_on_save_html))
        progress_bar.update(1)


def trends():
    """
    Important Note: This function requires internet connection to connect to CSSEGISandData repository on GitHub, else
    it will raise URLError.

    Input:

    The following files from CSSEGISandData repository on Github are used as inputs:

    - time_series_covid19_confirmed_global.csv
    - time_series_covid19_recovered_global.csv
    - time_series_covid19_deaths_global.csv

    Return:
    Standalone HTML interactive file in local directory.

    Trends by country

    - Cumulative
    - Daily
    - Seven day moving average
    - Recovered
    - Death
    - Active
    - Incident Rate
    - Case Fatality Ratio

    Trends comparison

    Top 10 countries trends with options for log plot & highlight countries by clicking on countries label

    Top 10 bar graph and table of data corresponding to graph

    Worldwide bar graph and table of data corresponding to graph
    """

    def set_external_graph_prop(p):
        p.yaxis.formatter = NumeralTickFormatter(format='0.0a')
        p.y_range.start = 0
        p.toolbar_location = None
        p.margin = 5
        p.background_fill_color = 'white'
        p.border_fill_color = 'white'
        p.width = 300
        p.height = 300

        p.xaxis.axis_label = 'Date'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.xaxis.major_label_text_font_style = 'bold'
        p.xaxis.major_label_orientation = 45

        p.yaxis.axis_label = 'COVID19_Case'
        p.yaxis.axis_label_text_font_style = 'bold'
        p.yaxis.major_label_text_font_style = 'bold'

    def set_external_graph_prop2(p):
        """

        :rtype: object
        """
        p.yaxis.formatter = FuncTickFormatter(code=""" return (Math.floor(tick)) + "%" """)
        p.y_range.start = 0
        p.toolbar_location = None
        p.margin = 5
        p.background_fill_color = 'white'
        p.border_fill_color = 'white'
        p.width = 300
        p.height = 300

        p.xaxis.axis_label = 'Date'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.xaxis.major_label_text_font_style = 'bold'
        p.xaxis.major_label_orientation = 45

        p.yaxis.axis_label = 'Case Fatality Ratio'
        p.yaxis.axis_label_text_font_style = 'bold'
        p.yaxis.major_label_text_font_style = 'bold'

    def set_external_graph_prop3(p):
        p.yaxis.formatter = NumeralTickFormatter(format='0.0a')
        p.y_range.start = 0
        p.toolbar_location = None
        p.margin = 5
        p.background_fill_color = 'white'
        p.border_fill_color = 'white'
        p.width = 300
        p.height = 300

        p.xaxis.axis_label = 'Date'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.xaxis.major_label_orientation = 45
        p.xaxis.major_label_text_font_style = 'bold'

        p.yaxis.axis_label = 'Incident Rate'
        p.yaxis.axis_label_text_font_style = 'bold'
        p.yaxis.major_label_text_font_style = 'bold'

    def set_internal_graph_prop(p_glyph_renderer):
        p_glyph_renderer.glyph.line_width = 2
        p_glyph_renderer.glyph.line_color = 'dodgerblue'

    def create_df(df):
        """

        :rtype: object
        """
        df_prelude = df.drop(['Province/State', 'Lat', 'Long'], axis=1).copy()
        df_prelude.columns = pd.to_datetime(df_prelude.columns)
        df_pivot = df_prelude.pivot_table(columns=df_prelude.index, aggfunc='sum')
        #  df_pivot.reset_index(inplace = True)
        #  df_pivot.rename(columns = {'index': 'Date'}, inplace = True)
        return df_pivot

    # todays_date = datetime.today().strftime('%a, %b %d, %Y')

    # todays_date.replace('/', '-')

    with tqdm(total=15, desc='Trends status', bar_format='{l_bar}{bar}{r_bar}', colour='yellow') as progress_bar:

        # Function to create DataFrame out of .csv file

        url_c = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
        url_r = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
        url_d = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'

        # print('Connecting, downloading & processing covid-19 global confirmed, recovered & deaths CSV files from CSSEGISandData repository on GitHub..')
        progress_bar.update(1)

        # Read & create a copy confirmed confirmed global cases
        df_confirmed = create_df(
            pd.read_csv(url_c, index_col=['Country/Region'], parse_dates=True, infer_datetime_format=True))

        date_on_plot = df_confirmed.index[df_confirmed.index.size - 1].strftime('%A, %b %d, %Y')

        # Read & create a copy recovered global cases
        df_recovered = create_df(
            pd.read_csv(url_r, index_col=['Country/Region'], parse_dates=True, infer_datetime_format=True))

        # Read & create a copy deaths global cases
        df_deaths = create_df(
            pd.read_csv(url_d, index_col=['Country/Region'], parse_dates=True, infer_datetime_format=True))

        # print('Processed covid-19 global confirmed, recovered & deaths global cases & created dataframes for analysis')
        progress_bar.update(1)

        # DataFrames with worldwide column, these DataFrames are used in plots
        df_confirmed_ww = df_confirmed.copy()
        df_confirmed_ww['Worldwide'] = df_confirmed.sum(axis=1)
        df_recovered_ww = df_recovered.copy()
        df_recovered_ww['Worldwide'] = df_recovered.sum(axis=1)
        df_deaths_ww = df_deaths.copy()
        df_deaths_ww['Worldwide'] = df_deaths.sum(axis=1)

        # DataFrame for top 10 countries, this DataFrame is used in bar plot
        # Top 10 recovery, deaths & active are with reference to confirmed cases
        # Index of pd.Series df_confirmed.max().sort_values(ascending == False)[0:10] contains list of top 10 countries with max cases.
        df_top10_crda = pd.DataFrame(dict(Confirmed=df_confirmed.max().sort_values(ascending=False)[0:10],
                                          Recovered=df_recovered.max().sort_values(ascending=False)
                                          [df_confirmed.max().sort_values(ascending=False)[0:10].index],
                                          Deaths=df_deaths.max().sort_values(ascending=False)
                                          [df_confirmed.max().sort_values(ascending=False)[0:10].index]))
        df_top10_crda['Active'] = df_top10_crda['Confirmed'] - df_top10_crda['Recovered'] - df_top10_crda['Deaths']

        # print('Created top 10 confirmed, recovered, deaths & active dataframe for analysis')
        progress_bar.update(1)

        # Country wise population is hardcoded in the source code here because there is less chance of it changing
        # 'population_record' is the variable that stores countries & corresponding populations
        # df_pop_inc_worldwide is generated using one of the two methods:
        # 1. Using .csv file from repository,
        # 2. Using hardcoded 'population_record'
        # df_pop_inc_worldwide is used in calculation of incident_rate.

        # Method 1: Using .csv file from repository only if True:
        # noinspection PyUnusedLocal
        population_record = list()  # Empty, undefined, this will remain empty if False:
        if True:
            url_population = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
            df_population = pd.read_csv(url_population)

            #     df_population contain provinces/states for some countries, my interest is in country wise population.
            #     So first filter 'Province_State' column for null/nan then filter corresponding 'Country_Region' & 'Population',
            #     no need to use sum or pivot, 'Country_Region' column with country name has null/nan in 'Province_State' column and
            #     corresponding 'Population' column field has sum of population of all provinces, if applicable. Please see the .csv file.
            df_pop = df_population[df_population['Province_State'].isna()].filter(['Country_Region', 'Population'])

            #     Create dataframe with single row for worldwide population
            df_pop_ww = pd.DataFrame(
                {df_pop.columns[0]: 'Worldwide', df_pop.columns[1]: df_pop.sum(axis=0)['Population']},
                index=[0])

            #     Final population dataframe that include worldwide population
            df_pop_inc_worldwide = pd.concat([df_pop_ww, df_pop], ignore_index=True)
            #     Just to make population_record non-empty this is assigned here, you can assign any value
            #     population_record is not used in calculation of incident_rate, df_pop_inc_worldwide is used.
            population_record = df_pop_inc_worldwide.to_dict(orient='records')

        # Method 2: Using hardcoded 'population_record' only if False:
        if not population_record:
            population_record = [{'Country_Region': 'Worldwide', 'Population': 7711863221.0},
                                 {'Country_Region': 'Afghanistan', 'Population': 38928341.0},
                                 {'Country_Region': 'Albania', 'Population': 2877800.0},
                                 {'Country_Region': 'Algeria', 'Population': 43851043.0},
                                 {'Country_Region': 'Andorra', 'Population': 77265.0},
                                 {'Country_Region': 'Angola', 'Population': 32866268.0},
                                 {'Country_Region': 'Antigua and Barbuda', 'Population': 97928.0},
                                 {'Country_Region': 'Argentina', 'Population': 45195777.0},
                                 {'Country_Region': 'Armenia', 'Population': 2963234.0},
                                 {'Country_Region': 'Austria', 'Population': 9006400.0},
                                 {'Country_Region': 'Azerbaijan', 'Population': 10139175.0},
                                 {'Country_Region': 'Bahamas', 'Population': 393248.0},
                                 {'Country_Region': 'Bahrain', 'Population': 1701583.0},
                                 {'Country_Region': 'Bangladesh', 'Population': 164689383.0},
                                 {'Country_Region': 'Barbados', 'Population': 287371.0},
                                 {'Country_Region': 'Belarus', 'Population': 9449321.0},
                                 {'Country_Region': 'Belgium', 'Population': 11589616.0},
                                 {'Country_Region': 'Belize', 'Population': 397621.0},
                                 {'Country_Region': 'Benin', 'Population': 12123198.0},
                                 {'Country_Region': 'Bhutan', 'Population': 771612.0},
                                 {'Country_Region': 'Bolivia', 'Population': 11673029.0},
                                 {'Country_Region': 'Bosnia and Herzegovina', 'Population': 3280815.0},
                                 {'Country_Region': 'Botswana', 'Population': 2351625.0},
                                 {'Country_Region': 'Brazil', 'Population': 212559409.0},
                                 {'Country_Region': 'Brunei', 'Population': 437483.0},
                                 {'Country_Region': 'Bulgaria', 'Population': 6948445.0},
                                 {'Country_Region': 'Burkina Faso', 'Population': 20903278.0},
                                 {'Country_Region': 'Burma', 'Population': 54409794.0},
                                 {'Country_Region': 'Burundi', 'Population': 11890781.0},
                                 {'Country_Region': 'Cabo Verde', 'Population': 555988.0},
                                 {'Country_Region': 'Cambodia', 'Population': 16718971.0},
                                 {'Country_Region': 'Cameroon', 'Population': 26545864.0},
                                 {'Country_Region': 'Central African Republic', 'Population': 4829764.0},
                                 {'Country_Region': 'Chad', 'Population': 16425859.0},
                                 {'Country_Region': 'Chile', 'Population': 19116209.0},
                                 {'Country_Region': 'Colombia', 'Population': 50882884.0},
                                 {'Country_Region': 'Congo (Brazzaville)', 'Population': 5518092.0},
                                 {'Country_Region': 'Congo (Kinshasa)', 'Population': 89561404.0},
                                 {'Country_Region': 'Comoros', 'Population': 869595.0},
                                 {'Country_Region': 'Costa Rica', 'Population': 5094114.0},
                                 {'Country_Region': "Cote d'Ivoire", 'Population': 26378275.0},
                                 {'Country_Region': 'Croatia', 'Population': 4105268.0},
                                 {'Country_Region': 'Cuba', 'Population': 11326616.0},
                                 {'Country_Region': 'Cyprus', 'Population': 1207361.0},
                                 {'Country_Region': 'Czechia', 'Population': 10708982.0},
                                 {'Country_Region': 'Denmark', 'Population': 5792203.0},
                                 {'Country_Region': 'Diamond Princess', 'Population': np.nan},
                                 {'Country_Region': 'Djibouti', 'Population': 988002.0},
                                 {'Country_Region': 'Dominica', 'Population': 71991.0},
                                 {'Country_Region': 'Dominican Republic', 'Population': 10847904.0},
                                 {'Country_Region': 'Ecuador', 'Population': 17643060.0},
                                 {'Country_Region': 'Egypt', 'Population': 102334403.0},
                                 {'Country_Region': 'El Salvador', 'Population': 6486201.0},
                                 {'Country_Region': 'Equatorial Guinea', 'Population': 1402985.0},
                                 {'Country_Region': 'Eritrea', 'Population': 3546427.0},
                                 {'Country_Region': 'Estonia', 'Population': 1326539.0},
                                 {'Country_Region': 'Eswatini', 'Population': 1160164.0},
                                 {'Country_Region': 'Ethiopia', 'Population': 114963583.0},
                                 {'Country_Region': 'Fiji', 'Population': 896444.0},
                                 {'Country_Region': 'Finland', 'Population': 5540718.0},
                                 {'Country_Region': 'France', 'Population': 65273512.0},
                                 {'Country_Region': 'Gabon', 'Population': 2225728.0},
                                 {'Country_Region': 'Gambia', 'Population': 2416664.0},
                                 {'Country_Region': 'Georgia', 'Population': 3989175.0},
                                 {'Country_Region': 'Germany', 'Population': 83783945.0},
                                 {'Country_Region': 'Ghana', 'Population': 31072945.0},
                                 {'Country_Region': 'Greece', 'Population': 10423056.0},
                                 {'Country_Region': 'Grenada', 'Population': 112519.0},
                                 {'Country_Region': 'Guatemala', 'Population': 17915567.0},
                                 {'Country_Region': 'Guinea', 'Population': 13132792.0},
                                 {'Country_Region': 'Guinea-Bissau', 'Population': 1967998.0},
                                 {'Country_Region': 'Guyana', 'Population': 786559.0},
                                 {'Country_Region': 'Haiti', 'Population': 11402533.0},
                                 {'Country_Region': 'Holy See', 'Population': 809.0},
                                 {'Country_Region': 'Honduras', 'Population': 9904608.0},
                                 {'Country_Region': 'Hungary', 'Population': 9660350.0},
                                 {'Country_Region': 'Iceland', 'Population': 341250.0},
                                 {'Country_Region': 'India', 'Population': 1380004385.0},
                                 {'Country_Region': 'Indonesia', 'Population': 273523621.0},
                                 {'Country_Region': 'Iran', 'Population': 83992953.0},
                                 {'Country_Region': 'Iraq', 'Population': 40222503.0},
                                 {'Country_Region': 'Ireland', 'Population': 4937796.0},
                                 {'Country_Region': 'Israel', 'Population': 8655541.0},
                                 {'Country_Region': 'Italy', 'Population': 60461828.0},
                                 {'Country_Region': 'Jamaica', 'Population': 2961161.0},
                                 {'Country_Region': 'Japan', 'Population': 126476458.0},
                                 {'Country_Region': 'Jordan', 'Population': 10203140.0},
                                 {'Country_Region': 'Kazakhstan', 'Population': 18776707.0},
                                 {'Country_Region': 'Kenya', 'Population': 53771300.0},
                                 {'Country_Region': 'Korea, South', 'Population': 51269183.0},
                                 {'Country_Region': 'Kosovo', 'Population': 1810366.0},
                                 {'Country_Region': 'Kuwait', 'Population': 4270563.0},
                                 {'Country_Region': 'Kyrgyzstan', 'Population': 6524191.0},
                                 {'Country_Region': 'Laos', 'Population': 7275556.0},
                                 {'Country_Region': 'Latvia', 'Population': 1886202.0},
                                 {'Country_Region': 'Lebanon', 'Population': 6825442.0},
                                 {'Country_Region': 'Lesotho', 'Population': 2142252.0},
                                 {'Country_Region': 'Liberia', 'Population': 5057677.0},
                                 {'Country_Region': 'Libya', 'Population': 6871287.0},
                                 {'Country_Region': 'Liechtenstein', 'Population': 38137.0},
                                 {'Country_Region': 'Lithuania', 'Population': 2722291.0},
                                 {'Country_Region': 'Luxembourg', 'Population': 625976.0},
                                 {'Country_Region': 'Madagascar', 'Population': 27691019.0},
                                 {'Country_Region': 'Malawi', 'Population': 19129955.0},
                                 {'Country_Region': 'Malaysia', 'Population': 32365998.0},
                                 {'Country_Region': 'Maldives', 'Population': 540542.0},
                                 {'Country_Region': 'Mali', 'Population': 20250834.0},
                                 {'Country_Region': 'Malta', 'Population': 441539.0},
                                 {'Country_Region': 'Marshall Islands', 'Population': 58413.0},
                                 {'Country_Region': 'Mauritania', 'Population': 4649660.0},
                                 {'Country_Region': 'Mauritius', 'Population': 1271767.0},
                                 {'Country_Region': 'Mexico', 'Population': 127792286.0},
                                 {'Country_Region': 'Moldova', 'Population': 4033963.0},
                                 {'Country_Region': 'Monaco', 'Population': 39244.0},
                                 {'Country_Region': 'Mongolia', 'Population': 3278292.0},
                                 {'Country_Region': 'Montenegro', 'Population': 628062.0},
                                 {'Country_Region': 'Morocco', 'Population': 36910558.0},
                                 {'Country_Region': 'Mozambique', 'Population': 31255435.0},
                                 {'Country_Region': 'MS Zaandam', 'Population': np.nan},
                                 {'Country_Region': 'Namibia', 'Population': 2540916.0},
                                 {'Country_Region': 'Nepal', 'Population': 29136808.0},
                                 {'Country_Region': 'Netherlands', 'Population': 17134873.0},
                                 {'Country_Region': 'New Zealand', 'Population': 4822233.0},
                                 {'Country_Region': 'Nicaragua', 'Population': 6624554.0},
                                 {'Country_Region': 'Niger', 'Population': 24206636.0},
                                 {'Country_Region': 'Nigeria', 'Population': 206139587.0},
                                 {'Country_Region': 'North Macedonia', 'Population': 2083380.0},
                                 {'Country_Region': 'Norway', 'Population': 5421242.0},
                                 {'Country_Region': 'Oman', 'Population': 5106622.0},
                                 {'Country_Region': 'Pakistan', 'Population': 220892331.0},
                                 {'Country_Region': 'Panama', 'Population': 4314768.0},
                                 {'Country_Region': 'Papua New Guinea', 'Population': 8947027.0},
                                 {'Country_Region': 'Paraguay', 'Population': 7132530.0},
                                 {'Country_Region': 'Peru', 'Population': 32971846.0},
                                 {'Country_Region': 'Philippines', 'Population': 109581085.0},
                                 {'Country_Region': 'Poland', 'Population': 37846605.0},
                                 {'Country_Region': 'Portugal', 'Population': 10196707.0},
                                 {'Country_Region': 'Qatar', 'Population': 2881060.0},
                                 {'Country_Region': 'Romania', 'Population': 19237682.0},
                                 {'Country_Region': 'Russia', 'Population': 145934460.0},
                                 {'Country_Region': 'Rwanda', 'Population': 12952209.0},
                                 {'Country_Region': 'Saint Kitts and Nevis', 'Population': 53192.0},
                                 {'Country_Region': 'Saint Lucia', 'Population': 183629.0},
                                 {'Country_Region': 'Saint Vincent and the Grenadines',
                                  'Population': 110947.0},
                                 {'Country_Region': 'Samoa', 'Population': 196130.0},
                                 {'Country_Region': 'San Marino', 'Population': 33938.0},
                                 {'Country_Region': 'Sao Tome and Principe', 'Population': 219161.0},
                                 {'Country_Region': 'Saudi Arabia', 'Population': 34813867.0},
                                 {'Country_Region': 'Senegal', 'Population': 16743930.0},
                                 {'Country_Region': 'Serbia', 'Population': 8737370.0},
                                 {'Country_Region': 'Seychelles', 'Population': 98340.0},
                                 {'Country_Region': 'Sierra Leone', 'Population': 7976985.0},
                                 {'Country_Region': 'Singapore', 'Population': 5850343.0},
                                 {'Country_Region': 'Slovakia', 'Population': 5459643.0},
                                 {'Country_Region': 'Slovenia', 'Population': 2078932.0},
                                 {'Country_Region': 'Solomon Islands', 'Population': 652858.0},
                                 {'Country_Region': 'Somalia', 'Population': 15893219.0},
                                 {'Country_Region': 'South Africa', 'Population': 59308690.0},
                                 {'Country_Region': 'South Sudan', 'Population': 11193729.0},
                                 {'Country_Region': 'Spain', 'Population': 46754783.0},
                                 {'Country_Region': 'Sri Lanka', 'Population': 21413250.0},
                                 {'Country_Region': 'Sudan', 'Population': 43849269.0},
                                 {'Country_Region': 'Suriname', 'Population': 586634.0},
                                 {'Country_Region': 'Sweden', 'Population': 10099270.0},
                                 {'Country_Region': 'Switzerland', 'Population': 8654618.0},
                                 {'Country_Region': 'Syria', 'Population': 17500657.0},
                                 {'Country_Region': 'Taiwan*', 'Population': 23816775.0},
                                 {'Country_Region': 'Tajikistan', 'Population': 9537642.0},
                                 {'Country_Region': 'Tanzania', 'Population': 59734213.0},
                                 {'Country_Region': 'Thailand', 'Population': 69799978.0},
                                 {'Country_Region': 'Timor-Leste', 'Population': 1318442.0},
                                 {'Country_Region': 'Togo', 'Population': 8278737.0},
                                 {'Country_Region': 'Trinidad and Tobago', 'Population': 1399491.0},
                                 {'Country_Region': 'Tunisia', 'Population': 11818618.0},
                                 {'Country_Region': 'Turkey', 'Population': 84339067.0},
                                 {'Country_Region': 'Uganda', 'Population': 45741000.0},
                                 {'Country_Region': 'Ukraine', 'Population': 43733759.0},
                                 {'Country_Region': 'United Arab Emirates', 'Population': 9890400.0},
                                 {'Country_Region': 'United Kingdom', 'Population': 67886004.0},
                                 {'Country_Region': 'Uruguay', 'Population': 3473727.0},
                                 {'Country_Region': 'Uzbekistan', 'Population': 33469199.0},
                                 {'Country_Region': 'Vanuatu', 'Population': 292680.0},
                                 {'Country_Region': 'Venezuela', 'Population': 28435943.0},
                                 {'Country_Region': 'Vietnam', 'Population': 97338583.0},
                                 {'Country_Region': 'West Bank and Gaza', 'Population': 5101416.0},
                                 {'Country_Region': 'Western Sahara', 'Population': 597330.0},
                                 {'Country_Region': 'Yemen', 'Population': 29825968.0},
                                 {'Country_Region': 'Zambia', 'Population': 18383956.0},
                                 {'Country_Region': 'Zimbabwe', 'Population': 14862927.0},
                                 {'Country_Region': 'Australia', 'Population': 25459700.0},
                                 {'Country_Region': 'Canada', 'Population': 37855702.0},
                                 {'Country_Region': 'China', 'Population': 1404676330.0},
                                 {'Country_Region': 'US', 'Population': 329466283.0}]
            #     create DataFrame df_pop_inc_worldwide from hardcoded 'population_record'
            df_pop_inc_worldwide = pd.DataFrame(population_record)
            # print('Using hardcoded population record..')
            progress_bar.update(1)
        else:
            # print("Using population record UID_ISO_FIPS_LookUp_Table.csv from CSSEGISandData repository")
            progress_bar.update(1)

        # As long as set of countries in confirmed main is subset of set of countries in population, it is fine.
        # To verify this, convert pd.Series of countries to set, & use set functions issubset & symmetric_difference
        # If setx.issubset(sety) returns True & setx.symmetric_difference(sety) returns the non-empty set,
        # that non-empty set members are not present in setx

        df_incident_rate = pd.DataFrame()
        for i in df_confirmed_ww.columns.tolist():
            df_incident_rate = pd.concat([df_incident_rate,
                                          df_confirmed_ww[i] * 100000 /
                                          df_pop_inc_worldwide[df_pop_inc_worldwide['Country_Region'].isin([i])][
                                              'Population'].values[0]
                                          ],
                                         axis=1,
                                         )
        df_incident_rate = df_incident_rate.round()

        # print('Created incident rate dataframe for analysis')
        progress_bar.update(1)

        # ### Core cells to create DataFrames for analysis COMPLETE.

        # Dropdown list options for GUI
        countries_list = list(
            ['Worldwide', 'India', 'US', 'Germany', 'France', 'Italy', 'Canada', 'Japan', 'Israel', 'United Kingdom',
             'Russia',
             'Brazil', 'Mexico', 'Korea, South', 'Iran', 'Saudi Arabia', 'United Arab Emirates', 'Australia',
             'New Zealand',
             'Sweden', 'Switzerland', 'Belgium'])
        # countries_list.extend(df_r1.columns.drop_duplicates().tolist()[3:])

        countries_list.extend(df_confirmed.columns.drop_duplicates().drop(['India', 'US', 'Germany',
                                                                           'France', 'Italy', 'Canada', 'Japan',
                                                                           'Israel',
                                                                           'United Kingdom',
                                                                           'Russia', 'Brazil', 'Mexico', 'Korea, South',
                                                                           'Iran',
                                                                           'Saudi Arabia', 'United Arab Emirates',
                                                                           'Australia',
                                                                           'New Zealand', 'Sweden', 'Switzerland',
                                                                           'Belgium']).tolist())
        countries_list.remove('China')

        top10_countries = df_top10_crda.index.tolist()

        trends_list_linear = ['Confirmed', 'Daily Cases', 'Seven Day Moving Average', 'Recovered', 'Deaths', 'Active']
        trends_list_log = ['Confirmed_log', 'Daily Cases_log', 'Seven Day Moving Average_log', 'Recovered_log',
                           'Deaths_log',
                           'Active_log']

        # hover for linear & log
        hv_hover = HoverTool(tooltips=[('Country', '@Variable'), ('Date', '@index{%F}'), ('Cases', '@value{0,}')],
                             formatters={'@index': 'datetime'}
                             )

        # Creates list of graphs confirmed, daily... Important code, the two list of plots for linear & log can be used in javascript call back..
        df_list = [df_confirmed[70:][top10_countries],
                   df_confirmed[70:][top10_countries].diff(1)[df_confirmed[70:][top10_countries].diff(1) > 0],
                   df_confirmed_ww[70:][top10_countries].diff(1).rolling(7).agg('mean').dropna().astype(int),
                   df_recovered[70:][top10_countries], df_deaths[70:][top10_countries],
                   df_confirmed_ww[70:][top10_countries] - df_recovered_ww[70:][top10_countries] - df_deaths_ww[70:][
                       top10_countries]
                   ]

        # print('Starting linear & logarithmic comparison plots for top 10 countries..')
        progress_bar.update(1)

        # bokeh plots stored in list linear
        hv_list_linear = [hv.render(i.hvplot.line(tools=[hv_hover],
                                                  logy=False, width=1200, height=600,
                                                  grid=True, line_width=5,
                                                  yformatter=NumeralTickFormatter(format='0.0a')
                                                  ).opts(legend_position='right')
                                    ) for i in df_list
                          ]

        # bokeh plots stored in list log
        hv_list_log = [hv.render(i.hvplot.line(tools=[hv_hover],
                                               logy=True, width=1200, height=600,
                                               grid=True, line_width=5, ylim=(1, i.max()[0]),
                                               yformatter=NumeralTickFormatter(format='0.0a')
                                               ).opts(legend_position='right')
                                 ) for i in df_list
                       ]

        for i, j in zip(trends_list_linear, hv_list_linear):
            j.toolbar.active_drag = None
            j.y_range.start = 0
            j.title.text = i + ' trends for top 10 countries'
            j.legend.title = 'Countries'
            j.ygrid.minor_grid_line_color = 'black'
            j.ygrid.minor_grid_line_alpha = 0.1
            j.toolbar_location = None

            j.xaxis.axis_label = 'Date'
            j.xaxis.axis_label_text_font_style = 'bold'
            j.xaxis.major_label_text_font_style = 'bold'

            j.yaxis.axis_label = 'COVID19_Case'
            j.yaxis.axis_label_text_font_style = 'bold'
            j.yaxis.major_label_text_font_style = 'bold'

            j.legend.click_policy = 'hide'

        for i, j in zip(trends_list_log, hv_list_log):
            j.toolbar.active_drag = None
            j.y_range.start = 1
            j.title.text = i + ' trends for top 10 countries'
            j.legend.title = 'Countries'
            j.ygrid.minor_grid_line_color = 'black'
            j.ygrid.minor_grid_line_alpha = 0.1
            j.toolbar_location = None

            j.xaxis.axis_label = 'Date'
            j.xaxis.axis_label_text_font_style = 'bold'
            j.xaxis.major_label_text_font_style = 'bold'

            j.yaxis.axis_label = 'COVID19_Case'
            j.yaxis.axis_label_text_font_style = 'bold'
            j.yaxis.major_label_text_font_style = 'bold'

            j.legend.click_policy = 'hide'

        bkh_dict_linear = collections.UserDict(zip(trends_list_linear, hv_list_linear))
        bkh_dict_log = collections.UserDict(zip(trends_list_log, hv_list_log))

        # print('Stored linear & logarithmic comparison plots for top 10 countries')
        progress_bar.update(1)

        df_worldwide_bar = pd.DataFrame(dict(Confirmed=df_confirmed.max().sum(axis=0),
                                             Recovered=df_recovered.max().sum(axis=0),
                                             Deaths=df_deaths.max().sum(axis=0),
                                             Active=df_confirmed.max().sum(axis=0) - df_recovered.max().sum(
                                                 axis=0) - df_deaths.max().sum(axis=0)
                                             ), index=['Worldwide']
                                        )
        # print('Created dataframe for worldwide bar graph...')
        progress_bar.update(1)

        ###################### Trends by country ######################################
        # Widgets, selectionbox, checkbox. Flag is kept for R&D purpose.
        s200 = pn.widgets.Select(name='Trends by Country',
                                 options=countries_list,
                                 width=250
                                 )
        t198 = Div(text='<b>Worlwide Trends</b>')

        # footer for trends by country
        footer_trends_by_country = Div(text="""Graphic: Prasanna Badami 
                                            <div>Source: Center for Systems Science & Engineering, Johns Hopkins University</div> 
                                            <div>Date: {} </div> 
                                            <div style = "font-size:12px"> Note:</div>
                                            <div style = "font-size:12px"><i><t>Incident rate is calculated as confirmed cases per 100,000 population.</i></div>
                                            <div style = "font-size:12px"><i> Case fatality ratio is the ratio of deaths to confirmed cases.</i></div>
                                            <div style = "font-size:12px"><i>United Kingdom has outliers in Recovered Cases data, graphs for certain dates may be not valid for UK.</i></div>""".format(
            date_on_plot),
            width=1230,
            background='white',
            #                                style={'font-family': 'Helvetica',
            #                                       'font-style' : 'italic',
            #                                       'font-size' : '12px',
            #                                       'color': 'black',
            #                                       'font-weight': 'bold'},
        )

        # footer for trends comparison(Top 10 countries), footer width 5 less than plot width
        footer_trends_comparison = Div(text="""Graphic: Prasanna Badami <div>Source: Center for Systems Science & Engineering, Johns Hopkins University</div> 
                                        <div>Date: {} </div>
                                        <div>Note: Click on interactive legends to select, enable or disable trends comparison </div>""".format(date_on_plot),
                                       width=1195,
                                       background='white',
                                       #                                style={'font-family': 'Helvetica',
                                       #                                       'font-style' : 'italic',
                                       #                                       'font-size' : '12px',
                                       #                                       'color': 'black',
                                       #                                       'font-weight': 'bold'},
                                       )

        # footer for top 10 bar graph & Worldwide bar graph, footer width 5 less than plot width
        footer_top10_ww_bar = Div(text="""Graphic: Prasanna Badami <div>Source: Center for Systems Science & Engineering, Johns Hopkins University</div> 
                                        <div>Date: {} </div>""".format(date_on_plot),
                                  width=925,
                                  background='white',
                                  #                           style={'font-family': 'Helvetica',
                                  #                                  'font-style' : 'italic',
                                  #                                  'font-size' : '12px',
                                  #                                  'color': 'black',
                                  #                                  'font-weight': 'bold'},
                                  )

        # HoverTool for trends by country
        hover_tool_all = HoverTool(tooltips=[('Date', '@index{%F}'), ('Cases', '@Default{0,}')],
                                   formatters={'@index': 'datetime'}
                                   )

        hover_tool_rate = HoverTool(
            tooltips=[('Date', '@index{%F}'), ('Cases', '@Default' + ' per 100,000 population')],
            formatters={'@index': 'datetime'}
            )

        hover_tool_ratio = HoverTool(tooltips=[('Date', '@index{%F}'), ('Cases', '@Default' + '%')],
                                     formatters={'@index': 'datetime'}
                                     )
        # print('Generating graphs, total 6 graphs for 6 trends for trends by country tab..')
        progress_bar.update(1)

        # Figure for graphs, basic things done here..
        # Confirmed cases
        p_confirmed_cases = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Daily cases
        p_daily_cases = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Seven day moving average cases
        p_7day_moving_avg = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Recovered cases
        p_recovered_cases = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Deaths
        p_deaths = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Active cases
        p_active = figure(tools=[hover_tool_all], x_axis_type='datetime')
        # Incident rate
        p_incident_rate = figure(tools=[hover_tool_rate], x_axis_type='datetime')
        # Case fatality ratio
        p_case_fatality_ratio = figure(tools=[hover_tool_ratio], x_axis_type='datetime')

        # Creating column data source files from dataframes for 6 trends:
        # 1. Confirmed, 2. Daily, 3. Seven days moving average, 4. Recovered, 5. Deaths & 6. Active
        source_c = ColumnDataSource(df_confirmed_ww[70:])
        source_c.data['Default'] = source_c.data['Worldwide']
        source_daily = ColumnDataSource(df_confirmed_ww[70:].diff(1))
        source_daily.data['Default'] = source_daily.data['Worldwide']
        source_sda = ColumnDataSource(df_confirmed_ww[70:].diff(1).rolling(7).agg('mean').dropna().astype(int))
        source_sda.data['Default'] = source_sda.data['Worldwide']
        source_rec = ColumnDataSource(df_recovered_ww[70:])
        source_rec.data['Default'] = source_rec.data['Worldwide']
        source_dth = ColumnDataSource(df_deaths_ww[70:])
        source_dth.data['Default'] = source_dth.data['Worldwide']
        source_act = ColumnDataSource(df_confirmed_ww[70:] - df_recovered_ww[70:] - df_deaths_ww[70:])
        source_act.data['Default'] = source_act.data['Worldwide']

        ######################################################
        # Incident rate
        source_incident_rate = ColumnDataSource(df_incident_rate)
        source_incident_rate.data['Default'] = source_incident_rate.data['Worldwide']

        # Case fatality ratio
        source_case_fatality_ratio = ColumnDataSource(df_deaths_ww[70:] * 100 / (df_confirmed_ww[70:]))
        source_case_fatality_ratio.data['Default'] = source_case_fatality_ratio.data['Worldwide']

        ######################################################

        # Generating graphs, total 6 graphs for 6 trends. Javascript code controls/changes the 'y' parameter based on user selection.
        p_confirmed_cases_glyph_renderer = p_confirmed_cases.line(source=source_c,
                                                                  x='index',
                                                                  y='Default'
                                                                  )
        p_confirmed_cases.title.text = 'Confirmed Cases'
        set_external_graph_prop(p_confirmed_cases)
        set_internal_graph_prop(p_confirmed_cases_glyph_renderer)

        p_daily_cases_glyph_renderer = p_daily_cases.line(source=source_daily,
                                                          x='index',
                                                          y='Default'
                                                          )
        p_daily_cases.title.text = 'Daily Cases'
        set_external_graph_prop(p_daily_cases)
        set_internal_graph_prop(p_daily_cases_glyph_renderer)

        p_7day_moving_avg_glyph_renderer = p_7day_moving_avg.line(source=source_sda,
                                                                  x='index',
                                                                  y='Default'
                                                                  )
        p_7day_moving_avg.title.text = 'Seven Day Moving Average'
        set_external_graph_prop(p_7day_moving_avg)
        set_internal_graph_prop(p_7day_moving_avg_glyph_renderer)

        p_recovered_cases_glyph_renderer = p_recovered_cases.line(source=source_rec,
                                                                  x='index',
                                                                  y='Default'
                                                                  )
        p_recovered_cases.title.text = 'Recovered Cases'
        set_external_graph_prop(p_recovered_cases)
        set_internal_graph_prop(p_recovered_cases_glyph_renderer)

        p_deaths_glyph_renderer = p_deaths.line(source=source_dth,
                                                x='index',
                                                y='Default'
                                                )
        p_deaths.title.text = 'Deaths'
        set_external_graph_prop(p_deaths)
        set_internal_graph_prop(p_deaths_glyph_renderer)

        p_active_glyph_renderer = p_active.line(source=source_act,
                                                x='index',
                                                y='Default'
                                                )
        p_active.title.text = 'Active Cases'
        set_external_graph_prop(p_active)
        set_internal_graph_prop(p_active_glyph_renderer)

        ##############################################################
        p_incident_rate.title.text = 'Incident Rate'
        prec_r_glyph_renderer = p_incident_rate.line(source=source_incident_rate,
                                                     x='index',
                                                     y='Default'
                                                     )
        set_external_graph_prop3(p_incident_rate)
        set_internal_graph_prop(prec_r_glyph_renderer)

        p_case_fatality_ratio_glyph_renderer = p_case_fatality_ratio.line(source=source_case_fatality_ratio,
                                                                          x='index',
                                                                          y='Default'
                                                                          )
        p_case_fatality_ratio.title.text = 'Case Fatality Ratio'
        set_external_graph_prop2(p_case_fatality_ratio)
        set_internal_graph_prop(p_case_fatality_ratio_glyph_renderer)
        ##############################################################

        # Arraging 6 graphs in a grid, set merge_tools =False to reflect changes done to toolbar_location
        pgrid = gridplot(children=[[p_confirmed_cases, p_daily_cases, p_7day_moving_avg, p_recovered_cases],
                                   [p_deaths, p_active, p_incident_rate, p_case_fatality_ratio]
                                   ],
                         merge_tools=False
                         )
        # default making grid visible, Javascript code controls/changes visibility based on user interactions with checkbox
        pgrid.visible = True
        pgrid.background = 'white'
        pgrid.name = 'Prasanna Badami'

        # JavaScript for select & trends for all countries
        callcode = """
            /* alert(c.value) */
            sc.data['Default'] = sc.data[c.value]
            sd.data['Default'] = sd.data[c.value]
            sda.data['Default'] = sda.data[c.value]
            sr.data['Default'] = sr.data[c.value]
            sdt.data['Default'] = sdt.data[c.value]
            sact.data['Default'] = sact.data[c.value]
    
            srec_r.data['Default'] = srec_r.data[c.value]
            sdth_r.data['Default'] = sdth_r.data[c.value]
    
            sc.change.emit()
            sd.change.emit()
            sda.change.emit()
            sr.change.emit()
            sdt.change.emit()
            sact.change.emit()
    
            srec_r.change.emit()
            sdth_r.change.emit()
            pg.visible = true
            tt.text = '<b>' + c.value + ' Trends' + '</b>'
    
        """

        # JavaScript 'callcode' is triggered when selection box 'value' changes
        # noinspection PyTypeChecker
        s200.jscallback(value=callcode, args={'sc': source_c,
                                              'sd': source_daily,
                                              'sda': source_sda,
                                              'sr': source_rec,
                                              'sdt': source_dth,
                                              'sact': source_act,
                                              'srec_r': source_incident_rate,
                                              'sdth_r': source_case_fatality_ratio,
                                              'c': s200,
                                              'pg': pgrid,
                                              'tt': t198
                                              }
                        )
        ###############################################################################
        # print('Generating graphs, for top 10 comparison...')
        progress_bar.update(1)
        ###################### Trends comparison(Top 10 countries) ####################
        # Widgets
        s199 = pn.widgets.Select(name='Top 10 Countries Observations',
                                 options=['Confirmed', 'Daily Cases', 'Seven Day Moving Average', 'Recovered', 'Deaths',
                                          'Active'],
                                 width=250
                                 )
        c199 = pn.widgets.Checkbox(name='Log Scale', value=False, disabled=False, align='end')

        @pn.depends(s199, c199)
        def get_trendscompare(s_199, c_199):
            if c_199:
                bkh_dict_r = bkh_dict_log[s_199 + '_log']
            else:
                bkh_dict_r = bkh_dict_linear[s_199]
            return bkh_dict_r

        ###############################################################################

        # print('Generating top 10 bar graph...')
        progress_bar.update(1)

        ############################# Top 10 bar graph ################################
        # t200 = Div(text='<br><br>Top 10 Countries Trends')
        # HoverTool for bar graph
        hover_tool_bar = HoverTool(tooltips=[('Country', '@x'), ('Cases', '@Cases{0,}')])

        # For Bar graph top 10
        dft = df_top10_crda.reset_index()
        # [('US', 'Confirmed'), ('US', 'Recovered')......]
        x = [(i, j) for i in dft['Country/Region'] for j in dft.columns[1:]]
        # print(x)

        # [cases....] mapped to 'x'
        # sum() is used here for concatenation of tuples, resulting in a single tuple
        # zip object contains tuples, so 'sum' function second argument is ()
        counts = sum(zip(dft.Confirmed, dft.Recovered, dft.Deaths, dft.Active), ())
        cases = list(counts)

        source_ww_bar = ColumnDataSource(data=dict(x=x, Cases=cases))

        #  display top 10 data along with plot
        table_top10 = hv.Table(dft, kdims='Country/Region').opts(width=600)

        # FactorRange is important, else plot will be empty.. setting x_range is very important in Bokeh
        pbar = figure(width=930,
                      height=600,
                      x_range=FactorRange(*x),
                      tooltips=hover_tool_bar.tooltips,
                      active_drag=None
                      )

        pbar.vbar(source=source_ww_bar, x='x', top='Cases',
                  width=1, bottom=0,
                  fill_color=factor_cmap('x', palette=['royalblue', 'lawngreen', 'red', 'orange'],
                                         factors=['Confirmed', 'Recovered', 'Deaths', 'Active'],
                                         start=1, end=4
                                         ),
                  line_color='white'
                  )
        pbar.xaxis.major_label_orientation = 'vertical'
        pbar.yaxis.formatter = NumeralTickFormatter(format='0.0a')
        pbar.y_range.start = 0
        pbar.background_fill_color = 'white'
        pbar.border_fill_color = 'white'
        pbar.ygrid.visible = True
        pbar.xgrid.visible = True
        pbar.toolbar_location = None

        pbar.xaxis.axis_label = 'Country'
        pbar.xaxis.axis_label_text_font_style = 'bold'
        # pbar.xaxis.major_label_text_font_style = 'bold'

        pbar.yaxis.axis_label = 'COVID19_Case'
        pbar.yaxis.axis_label_text_font_style = 'bold'
        pbar.yaxis.major_label_text_font_style = 'bold'
        ###############################################################################

        # print('Generating worldwide bar graph...')
        progress_bar.update(1)

        ###################### Worldwide bar graph ####################################
        # t201 = Div(text='<br><br>Worldwide Trends')
        hover_tool_wwbar = HoverTool(tooltips=[('Metric', '@Variable'), ('Cases', '@value{0,}')])
        bkh_ww_bar = hv.render(df_worldwide_bar.hvplot.bar(y=['Active', 'Deaths', 'Recovered', 'Confirmed'],
                                                           tools=[hover_tool_wwbar],
                                                           color=['orange', 'red', 'lawngreen', 'royalblue'],
                                                           bar_width=0.5, width=930, height=600,
                                                           ).opts(ylabel='COVID-19 Case'
                                                                  )
                               )
        bkh_ww_bar.yaxis.formatter = NumeralTickFormatter(format='0.0a')
        bkh_ww_bar.toolbar_location = None

        bkh_ww_bar.xaxis.axis_label_text_font_style = 'bold'
        bkh_ww_bar.xaxis.major_label_text_font_style = 'bold'

        bkh_ww_bar.yaxis.axis_label_text_font_style = 'bold'
        bkh_ww_bar.yaxis.major_label_text_font_style = 'bold'

        # display worldwide data along with plot
        table_ww = hv.Table(df_worldwide_bar)
        ###############################################################################

        # print('Arranging everything for dashboard')
        progress_bar.update(1)

        # Finally arrange everything in order for dashboard..
        pn_output = pn.Column(pn.Tabs(pn.WidgetBox(s200, t198,
                                                   # Javascript is used to control the graphs in bokeh gridplot
                                                   # Javascript gets activated whenever s200 changes(initiated by user)
                                                   pgrid,
                                                   footer_trends_by_country,
                                                   name='Trends by country'
                                                   ),
                                      # widget values as arguments to get_trendscompare
                                      pn.WidgetBox(pn.Row(s199, c199),
                                                   # Function takes s199/c199 as arguments & is called whenever s199/c199 changes.
                                                   # Function definition should have @pn.depends(s199, c199) immediately preceding it.
                                                   # It returns graph (bokeh object)
                                                   get_trendscompare,
                                                   footer_trends_comparison,
                                                   name='Trends comparison(Top 10 countries)'
                                                   ),
                                      pn.WidgetBox(pn.Row(pbar, table_top10), footer_top10_ww_bar,
                                                   name='Top 10 bar graph'),
                                      pn.WidgetBox(pn.Row(bkh_ww_bar, table_ww), footer_top10_ww_bar,
                                                   name='Worldwide bar graph')
                                      )
                              )
        # print('Saving interactive HTML dashboard...')
        progress_bar.update(1)
        #     To standalone interactive HTML
        pn_output.save('COVID-19_dashboard_' + date_on_plot + '.html',
                       resources=INLINE,
                       embed=True,
                       title='COVID19 dashboard | ' + date_on_plot
                       )

        print('Interactive ' + 'COVID-19_dashboard_' + str(date_on_plot) + '.html saved in the local directory')
        progress_bar.update(1)
