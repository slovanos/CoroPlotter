import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from mytools.myutils import updateFile, inputInteger

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

# Distinct color list

colorList = [(0, 0, 0), (230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200),\
             (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230),\
             (210, 245, 60), (0, 128, 128), (230, 190, 255), (170, 110, 40),\
             (255, 250, 200), (128, 0, 0), (170, 255, 195), (128, 128, 0),\
             (255, 215, 180), (0, 0, 128), (128, 128, 128), (255, 255, 255)]

colorsArrayNormalized = np.array(colorList)/255 

dataSource = 'Data Source: Johns Hopkins University\nGraph by @slovanos'

def plot(data, title, pdays=28, kind='line'):
    """Plots the passed dataframe.
    kind (str): 'line' or 'bar'
    """
    loc = MultipleLocator(1)
    if len(data.columns) <= 10:
    	ax = data.iloc[-pdays:].plot(kind=kind, style='.-', grid=True, title=title)
    else:
    	ax = data.iloc[-pdays:].plot(kind=kind, style='.-', grid=True, title=title, color=colorsArrayNormalized)
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, which='major')
    plt.annotate(dataSource, xy=(0.55,-0.07), xytext=(0.55,-0.07), xycoords='axes fraction',
                 textcoords='offset points', va='top', fontsize=8)
    plt.show()

    
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
    plt.show()


## Getting and processing Data

# ++++++++++++++++ Population Data +++++++++++++

file = './data/population_by_country_2020.csv'
dfPopulation = pd.read_csv(file)
dfPopulation.rename(columns={'Country (or dependency)' : 'country',
                             'Population (2020)' : 'population'}, inplace=True)
population = dfPopulation[['country','population']]
population.set_index('country', inplace = True)

# Adding World Total
population = population.append(pd.DataFrame(data = [population.sum()], index=['World']))

# +++++++++++++ COVID-19 Data +++++++++++++++++++

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

# ######## Renaming Index values for consistency ###############
population = population.rename(
        index={'United States':'Usa', 'South Korea':'Korea, South', 'Myanmar': 'Burma',
        'Czech Republic (Czechia)':'Czechia'})

dfC = dfC.rename(columns={'US':'Usa', 'Taiwan*':'Taiwan'})

dfD = dfD.rename(columns={'US':'Usa', 'Taiwan*':'Taiwan'})

# ##### Defining Arbitrary Zones of interest and parameters #######

ZOI = ['World', 'China', 'Italy', 'Usa','Germany', 'Switzerland',
         'United Kingdom', 'Spain', 'Iran', 'Argentina','Korea, South', 'Canada',
         'Austria', 'Norway','Russia']

ZOIRatios = ['World', 'China', 'Italy', 'Usa','Germany', 'Spain', 'Iran',
               'Argentina','Korea, South', 'Canada', 'Austria', 'Norway']

europe = ['Italy','Spain','France','Germany','Switzerland','Austria',
         'United Kingdom', 'Norway','Sweden', 'Finland','Belgium', 'Ireland', 'Portugal']

latam = ['Brazil', 'Argentina', 'Chile', 'Mexico', 'Ecuador', 'Uruguay', 'Peru', 'Bolivia']

world = ['World']


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

#dfCTrend = dfC[zones].iloc[-1,:]
trendIndex = pd.date_range(start=dfC.index[-1], periods=fDaysTrend, freq='D')
dfCTrend = pd.DataFrame(index=trendIndex, columns=trendZones)
dfCTrend.iloc[0] = dfC[trendZones].iloc[-1,:]

for i in range(1,fDaysTrend):
    dfCTrend.iloc[i] = dfCTrend.iloc[i-1] * growthFactorMean

# ################## Plotting Data ########################

# some plot Options
pdays = 70

# Data used. Description

## picking

titlePrefix = 'COVID-19 - '

# List of zones and list of dataframes to be combined

# Data Choices

dfs = [(dfC,'Cases'),
       (growthFactor, 'Cases growth Factor (Daily)'),
       (dailyNewCases, 'Daily New Cases'),
       (dfD,'Deaths'),
       (dailyNewDeath, 'Daily New Deaths'),
       (dfMortality, 'Mortality (Deaths per million)'),
       (dRatio, 'Deaths/Cases ratio'),
       ]

# Zone Choices
zoneChoices = [(topZonesCases, 'Countries with most cases'),
         (topZonesDeaths, 'Countries with most deaths'),
         (topMortality, 'Countries with largest mortality ratio (deaths/population)'),
         (world, 'World'),
         (ZOI, 'Arbitrary zone selection', '\n(' + ', '.join(ZOI) +')'),
         (europe, 'Europe Countries', '\n(' + ', '.join(europe) +')'),
         (latam, 'Some Latam Countries', '\n(' + ', '.join(latam) +')'),
         ]

# (dfCTrend,'COVID-19 Cases'), # Special case actually
# continue. See special cases!!

###########################

def listOptions(options, msg):
    print(msg)
    
    for idx, option in enumerate(options):
        optionDescription = option[1]
        optionList = option[2] if len(option) > 2 else ''
        print(f'{idx}: {optionDescription}{optionList}')

def inputIntegerOrList(choicesList, message='Enter an option (integer), name or list of names [q to quit]:'):

    while True:

        option = input(f'\n{message}')

        if option == 'q':
            sys.exit(0)

        elif option == '':
            print(f'No pick, using default value 0')
            return 0

        elif option.isdigit():

            try:
                n = int(option)
                return n

            except ValueError:
                    print('Not a valid input')
        else:
            
            option = option.title().replace(' ','')
            options = option.split(',')

            intersection = choicesList.intersection(options)

            if intersection:

                if len(intersection) < len(options):
                    print('One of the entered countries is not on the list')

                return list(intersection)

            else:
                
                print('Input no in the list of countries')

       
if __name__ == '__main__':

    #zones = [zone.lower() for zone in zones.tolist()] #  lowercased
    zones = set(zones.tolist()) # pandas index to list and list to set

    daysMsg = f'Enter the number of past days to draw the graphs. [Enter for default: {pdays}]:'
    pdays = inputInteger(pdays, daysMsg)

    dataMsg = f'\nChoose one of the following COVID-19 related Data:\n'
    listOptions(dfs, dataMsg)
    dataChoice = inputInteger(default=5)

    zoneMsg = f'\nChoose the zone of interest, or type the name of the country or list of countries separated by commas:\n'
    listOptions(zoneChoices, zoneMsg)
    zoneChoice = inputIntegerOrList(zones)

    while True:

        chosenData, dataDescription = dfs[dataChoice]
        if isinstance(zoneChoice, int):
            chosenZone, zoneDescription = zoneChoices[zoneChoice][:2]
        else:
            chosenZone = zoneChoice
            zoneDescription = 'User zone selection'

        title = titlePrefix + dataDescription + ' - ' + zoneDescription
        try:
            plot(chosenData[chosenZone], title, pdays)
        except Exception as e:
            print(e)
        
        dataChoice = inputInteger(default=5, message='Choose the data [or q to quit]:')
        zoneChoice = inputIntegerOrList(zones,message='Choose the zone of interest [or q to quit]:')
