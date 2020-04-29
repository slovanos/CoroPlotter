import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from mytools.myutils import updateFile

def processDf(df):
    """Preprocess the raw dataframe (that results from the .csv import)"""
    
    df.drop(columns=['Province/State','Lat', 'Long'], inplace=True)
    df.rename(columns={'Country/Region' : 'region'}, inplace=True)
    df = df.groupby(['region']).sum()
    df = df.T
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")
    df['World'] = df.sum(axis=1)
    df['WorldExceptChina'] = df['World'] - df['China']
    return df

# Plot Functions

dataSource = 'Data Source: Johns Hopkins University\nGraph by @slovanos'

def plot(data, title, pdays=28, kind='line'):
    """Plots the passed dataframe.
    kind (str): 'line' or 'bar'
    """
    loc = MultipleLocator(1)
    ax = data.iloc[-pdays:].plot(kind=kind, style='.-', grid=True, title=title)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate(dataSource, xy=(0.55,-0.07), xytext=(0.55,-0.07), xycoords='axes fraction',
                 textcoords='offset points', va='top', fontsize=8)
    plt.show(block=False)

    
def plottrend(data, dataTrend, title, pdays=28):
    """Plots a given datafram and its pre-calculated given trend"""
    
    loc = MultipleLocator(1)
    ax = data.iloc[-pdays:].plot(kind='line', style='.-',  grid=True, title=title)
    colors = [line.get_color() for line in ax.get_lines()]
    dataTrend.plot(ax=ax, style = '--', color=colors, legend=False)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate(dataSource, xy=(0.55,-0.07), xytext=(0.55,-0.07), xycoords='axes fraction',
                 textcoords='offset points', va='top', fontsize=8)
    plt.show(block=False)


## Getting and processing Data

# Population Data
file = './data/population_by_country_2020.csv'
dfPopulation = pd.read_csv(file)
dfPopulation.rename(columns={'Country (or dependency)' : 'country',
                             'Population (2020)' : 'population'}, inplace=True)
population = dfPopulation[['country','population']]
population.set_index('country', inplace = True)
# Adding World Total
population.append(pd.DataFrame(data = [population.sum()], index=['World']))

# Renaming Index values to John Hopkins COVID Data
population = population.rename(
        index={'United States':'US', 'South Korea':'Korea, South', 'Myanmar': 'Burma',
        'Czech Republic (Czechia)':'Czechia', 'Taiwan':'Taiwan*'})

# COVID-19 Data
rootUrl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master'\
          '/csse_covid_19_data/csse_covid_19_time_series/'

urlConfirmed = rootUrl+'time_series_covid19_confirmed_global.csv'
urlDeaths = rootUrl+'time_series_covid19_deaths_global.csv'
urlRecovered = rootUrl+'time_series_covid19_recovered_global.csv'

# ########## Confirmed #################
updateFile(urlConfirmed, './data/confirmed.csv', mtime = 0.25)

# Passing url directly to pd.read_csv() is also possible and valid, 
# but keeping an updated local file and avoid unecessary downloads instead
dfConfirmed = pd.read_csv('./data/confirmed.csv') 
dfC = processDf(dfConfirmed)

# ########## Deaths #################
updateFile(urlDeaths, './data/deaths.csv', mtime = 0.25)
dfDeaths = pd.read_csv('./data/deaths.csv')
dfD = processDf(dfDeaths)

# ########## Recovered #################
# Data currently Not available

# Defining Arbitrary Zones of interest and parameters

ZOI = ['World', 'WorldExceptChina', 'China', 'Italy', 'US','Germany', 'Switzerland',
         'United Kingdom', 'Spain', 'Iran', 'Argentina','Korea, South', 'Canada',
         'Austria', 'Norway','Russia']

ZOIRatios = ['World', 'China', 'Italy', 'US','Germany', 'Spain', 'Iran',
               'Argentina','Korea, South', 'Canada', 'Austria', 'Norway']

latam = ['Brazil', 'Argentina', 'Chile', 'Mexico', 'Ecuador', 'Uruguay', 'Peru']


## Subgroups and calculations
zones = dfC.columns

dfDict = {}
growthFactor = pd.DataFrame(index=dfC.index, columns=zones)
dRatio = pd.DataFrame(index=dfC.index, columns=zones)
dailyNewCases = pd.DataFrame(index=dfC.index, columns=zones)
dailyNewDeath = pd.DataFrame(index=dfD.index, columns=zones)

for zone in zones:
    #dfDict[zone] = pd.concat([dfC[zone].rename('confirmed'), dfD[zone].rename('death'), dfR[zone].rename('recovered')], axis=1)
    dfDict[zone] = pd.concat([dfC[zone].rename('confirmed'), dfD[zone].rename('death')], axis=1)   
    dfDict[zone].index = pd.to_datetime(dfDict[zone].index, format="%m/%d/%y")

    # Death Ratio
    dRatio[zone] = dfDict[zone]['death']/dfDict[zone]['confirmed']*100

    # Growth Rate
    tempC = pd.Series(dfC[zone][0])
    tempC = tempC.append(dfC[zone][0:-1], ignore_index = True)
    tempC = tempC.replace(0,1)
    growthFactor[zone] = dfC[zone]/tempC.values

    dailyNewCases[zone] = dfC[zone]-tempC.values

    tempD = pd.Series(dfD[zone][0])
    tempD = tempD.append(dfD[zone][0:-1], ignore_index = True)

    dailyNewDeath[zone] = dfD[zone]-tempD.values


# #### TOP N Countries ####

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

# Mortality per Million
dfMortality = (dfD[pop.index].div(pop.T.values.squeeze()))*1000000

sorted_dfMortality = dfMortality.sort_values(dfMortality.last_valid_index(),
                                             axis=1, ascending = False)

topMortality = sorted_dfMortality.columns[:topN]


## ########  Trend #############

pDaysTrend = 5 # Days used for averiging the Growth Rate
fDaysTrend = 4 # Days in the future for the trend

trendZones = topZonesCases

growthFactorMean = growthFactor.iloc[-pDaysTrend:,:].mean(axis=0)

#dfTrend = dfC[zones].iloc[-1,:]
trendIndex = pd.date_range(start=dfC.index[-1], periods=fDaysTrend, freq='D')
dfTrend = pd.DataFrame(index=trendIndex, columns=trendZones)
dfTrend.iloc[0] = dfC[trendZones].iloc[-1,:]

for i in range(1,fDaysTrend):
    dfTrend.iloc[i] = dfTrend.iloc[i-1] * growthFactorMean

# ################## Plotting Data ########################
pdays = 48

## ####### Cases #######

# Cases in Most affected Countries
plot(dfC[topZonesCases], 'COVID-19 Cases in Most Affected Countries', pdays)

# Cases in a given zone
plot(dfC[ZOI], 'COVID-19 Cases', pdays)

# Daily New Cases
#plot(dailyNewCases[topZonesCases], 'COVID-19 Daily New Cases', kind='bar')

## ####### Deaths #######

# Countries with most deaths
plot(dfD[topZonesDeaths], 'COVID-19 - Countries with most deaths', pdays)

# Daily New Death on a given zone
#plot(dailyNewDeath[latam], 'COVID-19 Daily New Deaths', kind='bar')

## ####### Ratios #######

# Deaths/Cases Ratio
plot(dRatio[topZonesCases], 'COVID-19 - Death Ratio %', pdays)

# Growth Factor on given zone
plot(growthFactor[latam], 'Growth Factor - Daily', pdays)


## ####### Mortality (deaths/population) #######

# Mortality - Top Countries
plot(dfMortality[topMortality], 'COVID-19 - Mortality (deaths per Million Population) Top Countries', pdays)

# Mortality
plot(dfMortality[topZonesCases], 'COVID-19 - Mortality (deaths per Million Population)', pdays)

# Mortality #topZonesDeaths
plot(dfMortality[latam], 'COVID-19 - Mortality (deaths per Million Population) Latam', pdays)

## Trend

# Plot Trend
plottrend(dfC[trendZones], dfTrend, 'COVID-19 Cases and Trend', pdays)
