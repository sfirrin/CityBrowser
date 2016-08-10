from bs4 import BeautifulSoup
import codecs
import os
import requests
import time
import re
import us_regions
import template_filler
import json
import urllib
import numpy as np

from math import radians, cos, sin, asin, sqrt

def get_cities(stations):
    page = open('wikipage.html')
    soup = BeautifulSoup(page, 'html.parser')

    table = soup.find_all('table')[3]

    rows = table.find_all('tr')[1:]

    index = 1

    cities = []

    for row in rows:
        data = row.find_all('td')
        city = {}

        latlong = data[8].find('span', class_='geo').text
        latlong = latlong.split('; ')

        city['latitude'] = float(latlong[0])
        city['longitude'] = float(latlong[1])
        # city['station'] = \
        #     get_nearest_station((city['latitude'], city['longitude']), stations)

        city['wiki'] = data[1].a.get('href')
        city['name'] = data[1].a.text
        print(city['name'])
        city['state'] = data[2].a.text
        if city['state'] == "Hawai'i":
            city['state'] = 'Hawaii'
        city['region'] = us_regions.STATES_TO_REGIONS[city['state']]
        city['population'] = int(data[3].text.replace(',', ''))
        city['id'] = str(index).rjust(3, '0')
        try:
            growth_rate = data[5].font.text
            positive = '+' in growth_rate
            for ch in growth_rate:
                if ch in ['+', u'\u2212', '%']:
                    growth_rate = growth_rate.replace(ch, '')
            growth_rate = float(growth_rate)
            if not positive:
                growth_rate *= -1
        except AttributeError:
            growth_rate = 0.0
        city['growth_rate'] = growth_rate
        nearby_stations = get_nearest_station((city['latitude'], city['longitude']), stations)
        for station in nearby_stations:
            try:
                # print(station)
                city['climate'] = get_station_weather(station)
                city['station'] = station
                print(station['ghcn_id'], station['distance'])
                break
            except ValueError as ve:
                pass
                # print(ve.args)
        cities.append(city)
        index += 1
    return cities


def save_city_wikis(cities):
    if not os.path.exists('city_pages/'):
        os.makedirs('city_pages/')
    for city in cities:
        print(city.name)
        file = codecs.open('city_pages/' + city.id + '.html', 'wb','utf-8')
        file.write(requests.get(city.wiki).text)
        time.sleep(2)


def haversine(latlong1, latlong2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Function slightly modified from http://stackoverflow.com/a/4913653
    """
    lat1, lon1 = latlong1
    lat2, lon2 = latlong2
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    earth_radius = 3956 # In miles
    return c * earth_radius

def get_stations_dict():
    # Returns a dict with coordinates of all stations as keys
    # and a value of a nested dict with id and name
    allstations = open('noaa/allstations.txt', 'rb')
    station_name_pattern = \
        r"\w+\s+-?\d+\.\d+\s+-?\d+\.\d+\s+-?[\d\.]+\s+\w\w\s+(\w+[ ?\w'-\.]{0,20} ?\w+)"
    stations = {}
    for line in allstations:
        # print(line)
        split = line.split()
        id = split[0]
        latlong = (float(split[1]), float(split[2]))
        # print(latlong)
        name_match = re.match(station_name_pattern, line)
        if name_match:
            name = name_match.group(1)
        else:
            print(line)
            name = 'not found'
        # print(name)
        stations[latlong] = {'ghcn_id': id, 'name': name}
    return stations

def get_nearest_station(latlong, stations):
    # Iterates through all station coordinates and returns the station with the minimum
    # great-circle distance
    min_distance = float('inf')
    nearest_station = None
    all_stations = []
    for coords in stations:
        distance = haversine(latlong, coords)
        current_station = stations[coords]
        current_station['distance'] = round(distance, 2)
        all_stations.append(current_station)
    sorted_stations = sorted(all_stations, key=lambda k: k['distance'])
    return sorted_stations

def get_line_with_id(id, path):
    # With a given station ID and file path (to the monthly normal), returns all
    # of the text of the first line that ID appears on

    file = '\n' + open(path, 'rb').read()
    pattern = r'\n(.*' + id + '.*)\n'
    match = re.search(pattern, file)
    if not match:
        raise ValueError('ID ' + id + ' not found in ' + path)
    else:
        return match.group(1)


def get_monthly_normals(line, temp_not_precip=True):
    # Parses the NOAA monthly normal data, input as a line
    # Info on the format of the monthly normal data can be found at
    # http://www1.ncdc.noaa.gov/pub/data/normals/1981-2010/readme.txt

    month_normals = {}
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
              'oct', 'nov', 'dec']

    # The first item in the line is the station id
    index = 0
    for month_normal in line.split()[1:]:
        # The last char of the temp is a flag related to the NOAA data collection
        # The format of the temp is 10ths of degrees F
        # The format of precip is 100ths of inches
        factor = 10.0 if temp_not_precip else 100.0
        month_normal = float(month_normal[:-1]) / factor
        month_normals[months[index]] = month_normal
        index += 1
    return month_normals


def get_station_weather(station):
    # Retrieves the monthly normal data (30 year average) from the NOAA dataset
    # The normal files are downloaded in this repo but they can be obtained from
    # http://www1.ncdc.noaa.gov/pub/data/normals/1981-2010/products/

    weather = {}

    station_id = station['ghcn_id']

    mean_high_line = get_line_with_id(station_id, 'noaa/mly-tmax-normal.txt')
    weather['mean_high'] = get_monthly_normals(mean_high_line)
    weather['mean_high']['year'] = sum(weather['mean_high'].values()) / 12.0

    mean_low_line = get_line_with_id(station_id, 'noaa/mly-tmin-normal.txt')
    weather['mean_low'] = get_monthly_normals(mean_low_line)
    weather['mean_low']['year'] = sum(weather['mean_low'].values()) / 12.0

    mean_precip_line = get_line_with_id(station_id, 'noaa/mly-prcp-normal.txt')
    weather['mean_precip'] = \
        get_monthly_normals(mean_precip_line, temp_not_precip=False)
    weather['mean_precip']['year'] = sum(weather['mean_precip'].values())

    weather.update(get_min_max_mean_record(station_id))

    weather['station'] = station

    return weather


def get_weather(latlong):
    # Takes a lat and long as input and finds the nearest station
    # Looks up info about that station from NOAA files and returns a dict
    # Containing weather info as well as the station
    allstations = get_stations_dict()
    nearest_stations = get_nearest_station(latlong, allstations)
    for station in nearest_stations:
        try:
            weather = get_station_weather(station)
            break
        except ValueError:
            pass
    return weather


def c_to_f(celcius):
    # Converts from Celcius to Fahrenheit
    return celcius * 9.0/5 + 32


def get_extremes_from_lines(lines, max_not_min=True):
    # Gets the maxes and mins from lines in the format of the ghcd .dly files
    # Like the ones found at ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/
    # The value of max_not_min determines whether it returns the min extremes
    # Or the max extremes

    # month_extremes is a dict of list of extremes for every month of every year
    # The keys are ints 1-12 for each month
    month_extremes = {}

    for line in lines:
        line_values = []
        # The window is just based on the way NOAA formats these files
        value_window = [22, 27]
        month = line[15:17]
        while value_window[0] <= 262:
            month_value = \
                float(line[value_window[0]:value_window[1]].strip(' \t\n\r')) / 10.0
            value_window = [bound + 8 for bound in value_window]
            # To account for the NOAA formatting for missing values
            if month_value > 80:
                continue
            line_values.append(month_value)

        if max_not_min:
            month_extremes.setdefault(int(month), []).append(max(line_values))
        else:
            month_extremes.setdefault(int(month), []).append(min(line_values))

    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
              'oct', 'nov', 'dec']

    month_mean_extreme = {}
    month_record_extreme = {}
    from pprint import pprint

    for i in range(12):
        extremes = month_extremes[i + 1]
        mean_of_extremes = float(sum(extremes)) / len(extremes)
        if max_not_min:
            record_extreme = max(extremes)
        else:
            record_extreme = min(extremes)
        month_mean_extreme[months[i]] = round(c_to_f(mean_of_extremes), 2)
        month_record_extreme[months[i]] = round(c_to_f(record_extreme), 2)

    yearly_mean_of_extremes = round(sum(month_mean_extreme.values()) / float(len(month_mean_extreme.values())), 2)
    month_mean_extreme['year'] = get_mean_yearly_extreme(month_extremes, max_not_min)

    if max_not_min:
        month_record_extreme['year'] = round(max(month_record_extreme.values()), 2)
    else:
        month_record_extreme['year'] = round(min(month_record_extreme.values()), 2)

    return month_mean_extreme, month_record_extreme


def get_mean_yearly_extreme(month_extremes, max_not_min=True):
    # Takes as input the month_extremes dictionary made in get_extremes_from_lines
    # Converts the dictionary to a numpy array with years as columns and months
    # As rows
    # Returns the average yearly max/min temp (the mean max or min temp for all years)
    month_extremes_np = np.array(month_extremes.values())
    if max_not_min:
        whole_year_extremes = month_extremes_np.max(axis=0)
    else:
        whole_year_extremes = month_extremes_np.min(axis=0)
    # print(whole_year_extremes)
    average_year_extreme = round(c_to_f(np.average(whole_year_extremes)), 2)
    # print(average_year_extreme)
    return average_year_extreme


def get_min_max_mean_record(station_id):
    # Takes a station ID as input and returns a dictionary with mean
    # and record maxes and mins for each month of the year in a dictionary

    # I have downloaded these .dly files locally but they can be requested from
    # ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/all/
    lines = open('../../ghcnd_us/' + station_id + '.dly').readlines()
    # Lines with temp max data
    tmax_lines = [line for line in lines if 'TMAX' in line]
    # Lines with temp min data
    tmin_lines = [line for line in lines if 'TMIN' in line]

    mean_max_high, record_high = get_extremes_from_lines(tmax_lines, max_not_min=True)
    mean_min_low, record_low = get_extremes_from_lines(tmin_lines, max_not_min=False)
    mins_and_maxes = {'mean_max_high': mean_max_high, 'record_high': record_high,
                      'mean_min_low': mean_min_low, 'record_low': record_low}

    # from pprint import pprint
    # pprint(mins_and_maxes)

    return mins_and_maxes

def convert_climate_to_seasons(city):
    """
    For when you want the city's weather to be by season rather than by month
    What I'm using it for is the web app since going by month would be too much
    :param city: The city dictionary produced by get_cities
    :return: A new city dictionary with a weather item that uses seasons rather
             than months
    """
    climate = city.pop('climate')
    months_to_seasons = {'dec': 'winter', 'jan': 'winter', 'feb': 'winter',
                   'mar': 'spring', 'apr': 'spring', 'may': 'spring',
                   'jun': 'summer', 'jul': 'summer', 'aug': 'summer',
                   'sep': 'fall', 'oct': 'fall', 'nov': 'fall'}
    seasons_to_months = {'winter': ['dec', 'jan', 'feb'], 'spring': ['mar', 'apr', 'may'],
                         'summer': ['jun', 'jul', 'aug'], 'fall': ['sep', 'oct', 'nov'], 'year': ['year']}
    # pprint(seasons_to_months)
    seasons_climate = {'record_high': {}, 'record_low': {}, 'mean_max_high': {}, 'mean_min_low': {}}

    for stat in ['mean_high', 'mean_low', 'mean_precip']:
        seasons_stat = {}
        for month in climate[stat]:
            if month == 'year':
                seasons_stat['year'] = round(climate[stat]['year'], 2)
                continue
            season = months_to_seasons[month]
            if stat == 'mean_precip':
                seasons_stat[season] = round(seasons_stat.get(season, 0) + climate[stat][month], 2)
            else:
                # Creating an average of the three months by adding 1/3 of each to zero, one at a time
                seasons_stat[season] = round(seasons_stat.get(season, 0) + (1.0/3)*climate[stat][month], 2)
        seasons_climate[stat] = seasons_stat

    record_highs = climate['record_high']
    record_lows = climate['record_low']
    mean_max_highs = climate['mean_max_high']
    mean_min_lows = climate['mean_min_low']

    for season in seasons_to_months:
        season_months = seasons_to_months[season]
        season_record_highs = []
        season_record_lows = []
        season_mean_max_highs = []
        season_mean_min_lows = []
        for month in season_months:
            season_record_highs.append(record_highs[month])
            season_record_lows.append(record_lows[month])
            season_mean_max_highs.append(mean_max_highs[month])
            season_mean_min_lows.append(mean_min_lows[month])
        seasons_climate['record_high'][season] = max(season_record_highs)
        seasons_climate['record_low'][season] = min(season_record_lows)
        seasons_climate['mean_max_high'][season] = max(season_mean_max_highs)
        seasons_climate['mean_min_low'][season] = min(season_mean_min_lows)
    seasons_climate['station'] = climate['station']
    # pprint(seasons_climate)
    city['climate'] = seasons_climate

def remove_noncentral_months(city):
    """
    I had the idea to show the middle months of each season, rather than the season statistics
    The idea being that the individual months will tell a more concrete story than the seasons
    :param city: The city dictionary produced by get_cities
    :return: The same city dicitonary, with the extra months removed
    """

    original_climate = city.pop('climate')
    trimmed_climate = {}

    trimmed_climate['station'] = original_climate['station']

    for stat in original_climate:
        if stat == 'station':
            continue
        trimmed_climate.setdefault(stat, {})
        for month in original_climate[stat]:
            if month in ['jan', 'apr', 'jul', 'oct', 'year']:
                trimmed_climate[stat][month] = original_climate[stat][month]
    city['climate'] = trimmed_climate

def add_city_photos_intros(cities, download=False):
    """
    Given a list of city dictionaries, mutates each city to include a properties for
    photo, the page's intro paragraph, and the wikimedia photo details page url
    Can also download the thumbnails to disk
    :param cities: City dictionary as found in get_cities
    :param download: Determines whether the thumbnails will be downloaded or not
    :return: Nothing, only mutates the cities
    """

    image_name_pattern = re.compile(r'\d+px-(.*)')
    for city in cities:
        remove_noncentral_months(city)
        id = city['id']
        city_file = open('city_pages/' + id + '.html')
        city_wiki = BeautifulSoup(city_file, 'html.parser')
        intro = city_wiki.find(id='mw-content-text').find('p', recursive=False).text
        # Removing citations
        intro = re.sub(r'\[\w+\]', '', intro)
        intro = re.sub(r' \(.+?\)', '', intro)
        intro = re.sub(r'/*/', '', intro)
        thumb_url = city_wiki.find(class_='infobox').find('img')['src'][2:]
        image_name_match = re.search(image_name_pattern, thumb_url)
        if image_name_match is None:
            image_name = thumb_url.split('/')[-1]
        else:
            image_name = image_name_match.group(1)
        if download:
            urllib.urlretrieve('http://' + thumb_url, 'city_images/' + id + '.jpg')
            time.sleep(0.5)
        city['photo_details_url'] = 'https://commons.wikimedia.org/wiki/File:' + image_name
        # print(city['photo_details_url'])
        city['photo_url'] = thumb_url
        city['wiki_intro'] = intro


def main():
    raleigh = (35.7796, -78.6382)
    cary = (35.7915, -78.7811)
    asheville = (35.5951, -82.5515)
    nc_state = (35.7847, -78.6821)


    # station, weather = get_weather(asheville)
    # print(station['name'])
    # from pprint import pprint
    # pprint(weather)

    # station_id = 'USC00305796'
    # get_min_max_mean_record(station_id)



    stations = get_stations_dict()
    # from pprint import pprint
    # pprint(get_weather(asheville))
    # pprint(get_nearest_station(raleigh, stations))
    cities = get_cities(stations)

    add_city_photos_intros(cities)
    # for city in cities:
    #     print(city['climate']['station']['ghcn_id'])
    # template_filler.get_weatherbox(cities[0])
    # #

        # print(photo_url)


    json.dump(cities, open('cities.json', 'wb'))


    # from pprint import pprint
    # pprint(get_monthly_normals(line))
    # i = 0
    # for month in line.split():
    #     print(i)
    #     print(month)
    #     print('')
    #     i += 1

main()
