import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from mytools.myutils import update_file, input_integer

# ######################### Plot Functions #####################################

# Distinct color list

colorList = [(0, 0, 0), (230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200),\
             (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230),\
             (210, 245, 60), (0, 128, 128), (230, 190, 255), (170, 110, 40),\
             (255, 250, 200), (128, 0, 0), (170, 255, 195), (128, 128, 0),\
             (255, 215, 180), (0, 0, 128), (128, 128, 128), (255, 255, 255)]

colorsArrayNormalized = np.array(colorList)/255 


def plot(data, title, dataSource='', pdays=28, kind='line'):
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

    
def plottrend(data, dataTrend, title, dataSource='', pdays=28):
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


# ################## Getting and processing Data ###############################

# ++++++++++++++++ Population Data +++++++++++++

def processPopulationData(file = './data/population_by_country_2020.csv'):

    dfPopulation = pd.read_csv(file)
    dfPopulation.rename(columns={'Country (or dependency)' : 'country',
                                 'Population (2020)' : 'population'}, inplace=True)
    population = dfPopulation[['country','population']]
    population.set_index('country', inplace = True)

    # Adding World Total
    population = population.append(pd.DataFrame(data = [population.sum()], index=['World']))

    # for compatibility with COVID Datafreames
    population = population.rename(
        index={'United States':'Usa', 'South Korea':'Korea, South', 'Myanmar': 'Burma',
        'Czech Republic (Czechia)':'Czechia'})

    return population


# +++++++++++++ COVID-19 Data +++++++++++++++++++

def processDf(df):
    """Preprocess the raw dataframe (that results from the .csv import)"""
    
    df.drop(columns=['Province/State','Lat', 'Long'], inplace=True)
    df.rename(columns={'Country/Region' : 'region'}, inplace=True)
    df = df.groupby(['region']).sum() # Group Sum population of the same country/reguon (divided in states unit now)
    df = df.T # Columnx are countries, rows dates.
    # Renaming Index values for consistency with Population Data
    df = df.rename(columns={'US':'Usa', 'Taiwan*':'Taiwan'})
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")
    df['World'] = df.sum(axis=1)
    df['WorldExceptChina'] = df['World'] - df['China']

    return df


def getCovIdData(rootUrl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master'\
          '/csse_covid_19_data/csse_covid_19_time_series/'):

    urlConfirmed = rootUrl+'time_series_covid19_confirmed_global.csv'
    urlDeaths = rootUrl+'time_series_covid19_deaths_global.csv'
    urlRecovered = rootUrl+'time_series_covid19_recovered_global.csv'

    # ########## Confirmed #################
    update_file(urlConfirmed, './data/confirmed.csv', mtime = 0.25)

    # Passing url directly to pd.read_csv() is also possible and valid, 
    # but keeping an updated local file and avoid unecessary downloads instead
    dfConfirmed = pd.read_csv('./data/confirmed.csv') 
    dfC = processDf(dfConfirmed)

    # ########## Deaths #################
    update_file(urlDeaths, './data/deaths.csv', mtime = 0.25)
    dfDeaths = pd.read_csv('./data/deaths.csv')
    dfD = processDf(dfDeaths)

    # ########## Recovered #################
    # Data currently Not available

    return dfC, dfD


def calculateData(dfC, dfD, population, populationUnit=1000000):

    # Selecting only countries in both data frames and dropping nAs
    commonLabelsIndex = population.index.intersection(dfC.columns.values)
    pop = population.loc[commonLabelsIndex].dropna()

    print(f'Total Countries: {pop.shape[0]}')

    ## Subgroups and calculations
    zones = dfC.columns

    dfDict = {}
    growthFactor = pd.DataFrame(index=dfC.index, columns=zones)
    dRatio = pd.DataFrame(index=dfC.index, columns=zones)
    dailyCases = pd.DataFrame(index=dfC.index, columns=zones)
    dailyDeaths = pd.DataFrame(index=dfD.index, columns=zones)

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

        dailyCases[zone] = dfC[zone]-tempC.values

        tempD = pd.Series(dfD[zone][0])
        tempD = tempD.append(dfD[zone][0:-1], ignore_index = True)

        dailyDeaths[zone] = dfD[zone]-tempD.values

    # New Cases/Deaths moving average
    dailyCasesMA = dailyCases.rolling(window=7).mean()
    dailyDeathsMA = dailyDeaths.rolling(window=7).mean()

    # New Cases/Deaths per million
    dailyCasesOverPopulationMA = (dailyCasesMA[pop.index].div(pop.T.values.squeeze()))*populationUnit
    dailyDeathsOverPopulationMA = (dailyDeathsMA[pop.index].div(pop.T.values.squeeze()))*populationUnit

    # Mortality (deaths/Population) per Million
    dfMortality = (dfD[pop.index].div(pop.T.values.squeeze()))*populationUnit


    # #### TOP N Countries ####

    topN = 10

    # Most affected Countries (by case count)
    sorted_dfC = dfC.sort_values(dfC.last_valid_index(), axis=1, ascending = False)

    topCases = sorted_dfC.drop(columns=['World','WorldExceptChina']).columns[:topN]

    # Countries with most daily Cases (Moving Average)
    sorted_dailyCasesMA = dailyCasesMA.sort_values(
        dailyCasesMA.last_valid_index(), axis=1, ascending = False)

    topDailyCases = sorted_dailyCasesMA.drop(columns=['World','WorldExceptChina']).columns[:topN]

    # Countries with most daily Cases (Per unit population, Moving Average)
    sorted_dailyCasesOverPopulationMA = dailyCasesOverPopulationMA.sort_values(
        dailyCasesOverPopulationMA.last_valid_index(), axis=1, ascending = False)

    topDailyCasesOverPopulation = sorted_dailyCasesOverPopulationMA.columns[:topN]

    # Countries with most deaths
    sorted_dfD = dfD.sort_values(dfD.last_valid_index(), axis=1, ascending = False)

    topDeaths = sorted_dfD.drop(columns=['World','WorldExceptChina']).columns[:topN]

    # Countries with most daily deaths (Moving Average)
    sorted_dailyDeathsMA = dailyDeathsMA.sort_values(
        dailyDeathsMA.last_valid_index(), axis=1, ascending = False)

    topDailyDeaths = sorted_dailyDeathsMA.drop(columns=['World','WorldExceptChina']).columns[:topN]

    # Countries with most daily deaths (Per unit population, Moving Average)
    sorted_dailyDeathsOverPopulationMA = dailyDeathsOverPopulationMA.sort_values(
        dailyDeathsOverPopulationMA.last_valid_index(), axis=1, ascending = False)

    topDailyDeathsOverPopulation = sorted_dailyDeathsOverPopulationMA.columns[:topN]

    # Top Mortaliy
    sorted_dfMortality = dfMortality.sort_values(dfMortality.last_valid_index(),
                                                 axis=1, ascending = False)

    topMortality = sorted_dfMortality.columns[:topN]


    ## ########  Trend #############

    ##pDaysTrend = 5 # Days used for averiging the Growth Rate
    ##fDaysTrend = 4 # Days in the future for the trend
    ##
    ##trendZones = topCases
    ##
    ##growthFactorMean = growthFactor.iloc[-pDaysTrend:,:].mean(axis=0)
    ##
    ###dfCTrend = dfC[zones].iloc[-1,:]
    ##trendIndex = pd.date_range(start=dfC.index[-1], periods=fDaysTrend, freq='D')
    ##dfCTrend = pd.DataFrame(index=trendIndex, columns=trendZones)
    ##dfCTrend.iloc[0] = dfC[trendZones].iloc[-1,:]
    ##
    ##for i in range(1,fDaysTrend):
    ##    dfCTrend.iloc[i] = dfCTrend.iloc[i-1] * growthFactorMean

    ## Data used. Description. Picking.

    # Lists of dataframes and zones to be combined

    # Data Choices

    dfs = [(dfC,'Cases (accumulated)'),
           (growthFactor, 'Cases growth Factor (Daily)'),
           (dailyCases, 'Daily Cases'),
           (dailyCasesMA, 'Daily Cases (7 days MA)'),
           (dailyCasesOverPopulationMA, 'Daily Cases per Million (7 days MA)'),
           (dfD,'Deaths (accumulated)'),
           (dailyDeaths, 'Daily Deaths'),
           (dailyDeathsMA, 'Daily Deaths (7 days MA)'),
           (dailyDeathsOverPopulationMA, 'Daily Deaths per Million (7 days MA)'),
           (dfMortality, 'Mortality (Deaths per million)'),
           (dRatio, 'Deaths/Cases ratio'),
           ]

    # Zone Choices

    # ##### Defining Arbitrary Zones of interest and parameters #######

    ZOI = ['World', 'China', 'Italy', 'Usa','Germany', 'Switzerland',
             'United Kingdom', 'Spain', 'Iran', 'Argentina','Korea, South', 'Canada',
             'Austria', 'Norway','Russia']

    europe = ['Italy','Spain','France','Germany','Switzerland','Austria',
             'United Kingdom', 'Norway','Sweden', 'Finland','Belgium', 'Ireland', 'Portugal']

    latam = ['Brazil', 'Argentina', 'Chile', 'Mexico', 'Ecuador', 'Uruguay', 'Peru', 'Bolivia']

    world = ['World']


    zoneChoices = [(topCases, 'Countries with most cases'),
             (topDailyCases, 'Countries with most daily cases (7 days MA)'),
             (topDailyCasesOverPopulation, 'Countries with most daily cases per population unit (7 days MA)'),
             (topDeaths, 'Countries with most deaths'),
             (topDailyDeaths, 'Countries with most daily deaths (MA)'),
             (topDailyDeathsOverPopulation, 'Countries with most daily deaths per population unit (7 days MA)'),
             (topMortality, 'Countries with largest mortality ratio (deaths/population)'),
             (world, 'World'),
             (ZOI, 'Arbitrary zone selection', '\n(' + ', '.join(ZOI) +')'),
             (europe, 'Europe Countries', '\n(' + ', '.join(europe) +')'),
             (latam, 'Some Latam Countries', '\n(' + ', '.join(latam) +')'),
             ]

    # (dfCTrend,'COVID-19 Cases'), # Special case actually
    # continue. See special cases!!

    #zones = [zone.lower() for zone in zones.tolist()] #  lowercased
    zones = set(zones.tolist()) # pandas index to list and list to set

    return zones, dfs, zoneChoices

# ################ Listing and Selection tools #############################

def listOptions(options, msg):
    print(msg)
    
    for idx, option in enumerate(options):
        optionDescription = option[1]
        optionList = option[2] if len(option) > 2 else ''
        print(f'{idx}: {optionDescription}{optionList}')

def inputIntegerOrList(choicesList, message='Enter an option (integer), name or list of names [q to quit]:', defaultChoice=0):

    while True:

        option = input(f'\n{message}')

        if option == 'q':
            sys.exit(0)

        elif option == '':
            print(f'No pick, using default value {defaultChoice}')
            return defaultChoice

        elif option.isdigit():

            try:
                n = int(option)
                return n

            except ValueError:
                    print('Not a valid input')
        else:
            
            option = option.title()
            options = option.split(',')
            options = [item.strip() for item in options]

            intersection = choicesList.intersection(set(options))

            if intersection:

                if len(intersection) < len(options):
                    print('At least one of the entered countries is not on the list')

                return list(intersection)

            else:
                
                print('Input not in the list of countries')

       
if __name__ == '__main__':

    defaultDF = 8
    defaultZone = 8

    # some plot Options
    pdays = 180
    titlePrefix = 'COVID-19 - '
    dataSource = 'Data Source: Johns Hopkins University\nGraph by @slovanos'

    # Getting data:
    # COVID Data from Johns Hopkins University
    dfC, dfD = getCovIdData(rootUrl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master'\
          '/csse_covid_19_data/csse_covid_19_time_series/')

    # Population Data. Local
    population = processPopulationData(file = './data/population_by_country_2020.csv')
   
    # Calculating Data:
    zones, dfs, zoneChoices = calculateData(dfC, dfD, population)

    # Choosing Data:
    daysMsg = f'Enter the number of past days to draw the graphs (max: {dfC.shape[0]}). [Enter for default: {pdays}]:'
    pdays = input_integer(pdays, daysMsg)

    dataMsg = f'\nChoose one of the following COVID-19 related Data:\n'
    listOptions(dfs, dataMsg)
    dataChoice = input_integer(default=defaultDF)

    zoneMsg = f'\nChoose the zone of interest, or type the name of the country or list of countries separated by commas:\n'
    listOptions(zoneChoices, zoneMsg)
    zoneChoice = inputIntegerOrList(zones,defaultChoice=defaultZone)

    while True:

        chosenData, dataDescription = dfs[dataChoice]
        if isinstance(zoneChoice, int):
            chosenZone, zoneDescription = zoneChoices[zoneChoice][:2]
        else:
            chosenZone = zoneChoice
            zoneDescription = 'User zone selection'

        title = titlePrefix + dataDescription + ' on ' + zoneDescription + '. ' + str(pdays) + ' days.'
        try:
            plot(chosenData[chosenZone], title, dataSource, pdays)
        except Exception as e:
            print(e)
        
        dataChoice = input_integer(default=defaultDF, message='Choose the data [or q to quit]:')
        zoneChoice = inputIntegerOrList(zones,message='Choose the zone of interest [or q to quit]:',defaultChoice=defaultZone)
