# Pandas ("Panel Data")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from mytools.myutils import updateFile

def plotlines(data, title, pdays = 21):
    loc = MultipleLocator(1)
    ax = data.iloc[-pdays:].plot(kind='line', style = '.-', grid =True, title = title)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate('Data Source: Johns Hopkins University\nGraph by @slovanos', (0.55,-0.07), xycoords='axes fraction', textcoords='offset points', va='top', fontsize=8)
    plt.show(block=False)
    
def plotbars(data, title, pdays = 21):
    data.index = data.index.date
    loc = MultipleLocator(1)
    ax = data.iloc[-pdays:].plot(kind='bar', style = '.-', grid =True, title = title)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate('Data Source: Johns Hopkins University\nGraph by @slovanos', (0.55,-0.07), xycoords='axes fraction', textcoords='offset points', va='top', fontsize=8)
    plt.show(block=False)

def plottrend(data, dataTrend, title, pdays = 28):
    loc = MultipleLocator(1)
    ax = data.iloc[-pdays:].plot(kind='line', style = '.-',  grid =True, title = title)
    colors = [line.get_color() for line in ax.get_lines()]
    dataTrend.plot(ax=ax, style = '--', color = colors, legend = False)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate('Data Source: Johns Hopkins University\nGraph by @slovanos', (0.55,-0.07), xycoords='axes fraction', textcoords='offset points', va='top', fontsize=8)
    plt.show(block=False)

## Getting and processing Data

# Population Data
file = '~/Python/CoroPlotter/population_by_country_2020.csv'
dfPopulation = pd.read_csv(file)
dfPopulation.rename(columns={'Country (or dependency)' : 'country', 'Population (2020)' : 'population'}, inplace = True)
population = dfPopulation[['country','population']]
population.set_index('country', inplace = True)
# Adding World Total
#population.loc['World'] = population.sum()
population.append(pd.DataFrame(data = [population.sum()], index=['World']))

# Renaming Index values to John Hopkins COVID Data
population = population.rename(index={'United States':'US', 'South Korea':'Korea, South', 'Myanmar': 'Burma',\
                                      'Czech Republic (Czechia)':'Czechia', 'Taiwan':'Taiwan*'})

# COVID-19 Data
urlConfirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
urlDeaths = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
urlRecovered = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'

# ########## Confirmed #################
updateFile(urlConfirmed, 'confirmed.csv', mtime = 0.25)
dfConfirmed = pd.read_csv('confirmed.csv') 
# passing url directly to pd.read_csv is also possible. But trying to keep an up
# dated local file and avoid unecessary downloads
dfConfirmed.drop(columns=['Province/State','Lat', 'Long'], inplace = True)
dfConfirmed.rename(columns={'Country/Region' : 'region'}, inplace = True)
dfC = dfConfirmed.groupby(['region']).sum()
dfC = dfC.T
dfC.index = pd.to_datetime(dfC.index, format="%m/%d/%y")
dfC['World'] = dfC.sum(axis=1)
dfC['WorldExceptChina'] = dfC['World'] - dfC['China'] 


# ########## Deaths #################
updateFile(urlDeaths, 'deaths.csv', mtime = 0.25)
dfDeaths = pd.read_csv('deaths.csv')
dfDeaths.drop(columns=['Province/State','Lat', 'Long'], inplace = True)
dfDeaths.rename(columns={'Country/Region' : 'region'}, inplace = True)
dfD = dfDeaths.groupby(['region']).sum()
dfD = dfD.T
dfD.index = pd.to_datetime(dfD.index, format="%m/%d/%y")
dfD['World'] = dfD.sum(axis=1)
dfD['WorldExceptChina'] = dfD['World'] - dfD['China'] 

# ########## Recovered #################
##dfRecovered = pd.read_csv(urlRecovered)
##dfRecovered.drop(columns=['Province/State','Lat', 'Long'], inplace = True)
##dfRecovered.rename(columns={'Country/Region' : 'region'}, inplace = True)
##dfR = dfRecovered.groupby(['region']).sum()
##dfR = dfR.T
##dfR.index = pd.to_datetime(dfR.index, format="%m/%d/%y")
##dfR['World'] = dfR.sum(axis=1)
##dfR['WorldExceptChina'] = dfR['World'] - dfR['China']


## Subgroups and calculations
zones = dfC.columns

dfDict = {}
dRate = pd.DataFrame(index=dfC.index, columns=zones)
growthFactor = pd.DataFrame(index=dfC.index, columns=zones)
dailyNew = pd.DataFrame(index=dfC.index, columns=zones)
dailyNewDeath = pd.DataFrame(index=dfD.index, columns=zones)

for zone in zones:
    #dfDict[zone] = pd.concat([dfC[zone].rename('confirmed'), dfD[zone].rename('death'), dfR[zone].rename('recovered')], axis=1)
    dfDict[zone] = pd.concat([dfC[zone].rename('confirmed'), dfD[zone].rename('death')], axis=1)
    dfDict[zone].index = pd.to_datetime(dfDict[zone].index, format="%m/%d/%y")
    #dfDict[zone]['dRate%'] = dfDict[zone]['death']/dfDict[zone]['confirmed']*100
    dRate[zone] = dfDict[zone]['death']/dfDict[zone]['confirmed']*100

    #Growth Rate
    tempC = pd.Series(dfC[zone][0])
    tempC = tempC.append(dfC[zone][0:-1], ignore_index = True)
    tempC = tempC.replace(0,1)
    growthFactor[zone] = dfC[zone]/tempC.values
    dailyNew[zone] = dfC[zone]-tempC.values

    tempD = pd.Series(dfD[zone][0])
    tempD = tempD.append(dfD[zone][0:-1], ignore_index = True)

    dailyNewDeath[zone] = dfD[zone]-tempD.values

# #### Most ####

topN = 10

# Most affected Countries (by case count)
dfCsubset = dfC.drop(columns=['World','WorldExceptChina'])
sorted_dfC = dfCsubset.sort_values(dfCsubset.last_valid_index(), axis=1, ascending = False)

topZonesCases = sorted_dfC.columns[:topN]

# Countries with most deaths
dfDsubset = dfD.drop(columns=['World','WorldExceptChina'])
sorted_dfD = dfDsubset.sort_values(dfDsubset.last_valid_index(), axis=1, ascending = False)
topZonesDeaths = sorted_dfD.columns[:topN]

# Mortality (deaths/Population)
# Selecting only countries in both data frames and dropping nAs
commonLabelsIndex = population.index.intersection(dfC.columns.values) 
pop = population.loc[commonLabelsIndex].dropna()
# # Mortality per Million
dfMortality = (dfD[pop.index].div(pop.T.values.squeeze()))*1000000

sorted_dfMortality = dfMortality.sort_values(dfMortality.last_valid_index(), axis=1, ascending = False)
topMortality = sorted_dfMortality.columns[:topN]

## ################## Plotting Data ########################

# Defining Zones and parameters

zones = ['World', 'WorldExceptChina', 'China', 'Italy', 'US','Germany', 'Switzerland', 'United Kingdom',\
         'Spain', 'Iran', 'Argentina','Korea, South', 'Canada', 'Austria', 'Norway','Russia']

zonesRatios = ['World', 'China', 'Italy', 'US','Germany',\
         'Spain', 'Iran', 'Argentina','Korea, South', 'Canada', 'Austria', 'Norway']

latam = ['Brazil', 'Argentina', 'Chile', 'Mexico', 'Ecuador', 'Uruguay', 'Peru']

pdays = 28

## ####### Cases #######

# Most affected
plotlines(dfC[topZonesCases], 'COVID-19 Cases in Most Affected Countries')

# Cases acumulated in given zone
plotlines(dfC[zones], 'COVID-19 Cases')

# Daily New Cases
plotbars(dailyNew[topZonesCases], 'COVID-19 Daily New Cases')

## ####### Deaths #######

# Death - Top Countries
plotlines(dfD[topZonesDeaths], 'COVID-19 - Countries with most deaths', pdays)

# Daily New Death
plotbars(dailyNewDeath[latam], 'COVID-19 Daily New Deaths')

## ####### Ratios #######

# Deaths/Cases Ratio
plotlines(dRate[topZonesCases], 'COVID-19 - Death Ratio %', pdays)

# Growth Factor
plotlines(growthFactor[topZonesCases], 'Growth Factor - Daily', 14)


## ####### Mortality (deaths/population) #######

# Mortality - Top Countries
plotlines(dfMortality[topMortality], 'COVID-19 - Mortality (deaths per Million Population) Top Countries', pdays)

# Mortality #topZonesDeaths
plotlines(dfMortality[latam], 'COVID-19 - Mortality (deaths per Million Population) Latam', pdays)

## ########  Trend #############

pDaysTrend = 5 # Days used for averiging the Growth Rate
fDaysTrend = 4 # Days in the future for the trend

zones = topZonesCases

growthFactorMean = growthFactor.iloc[-pDaysTrend:,:].mean(axis=0)

#dfTrend = dfC[zones].iloc[-1,:]
trendIndex = pd.date_range(start = dfC.index[-1], periods = fDaysTrend, freq = 'D')
dfTrend = pd.DataFrame(index = trendIndex, columns = zones)
dfTrend.iloc[0] = dfC[zones].iloc[-1,:]

for i in range(1,fDaysTrend):
    dfTrend.iloc[i] = dfTrend.iloc[i-1] * growthFactorMean

# Plot Trend
plottrend(dfC[zones], dfTrend, 'COVID-19 Cases and Trend')
