from bs4 import BeautifulSoup
import codecs
import os
import requests
import time
import re
import us_regions
import template_filler
import json

from math import radians, cos, sin, asin, sqrt

def get_cities(stations):
    page = open('wikipage.html')
    soup = BeautifulSoup(page, 'html.parser')

    table = soup.find_all('table')[3]

    rows = table.find_all('tr')[1:]

    index = 1

    cities = []

    for row in rows[:4]:
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
        # print(city['name'])
        city['state'] = data[2].a.text
        if city['state'] == "Hawai'i":
            city['state'] = 'Hawaii'
        city['region'] = us_regions.STATES_TO_REGIONS[city['state']]
        city['population'] = int(data[3].text.replace(',', ''))
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
                city['climate'] = get_weather((city['latitude'], city['longitude']))
                break
            except ValueError:
                pass
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
        stations[latlong] = {'ghcn_id': id, 'name': name.title()}
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
    return sorted_stations[:10]

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


def get_station_weather(station_id):
    # Retrieves the monthly normal data (30 year average) from the NOAA dataset
    # The normal files are downloaded in this repo but they can be obtained from
    # http://www1.ncdc.noaa.gov/pub/data/normals/1981-2010/products/

    weather = {}

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

    return weather


def get_weather(latlong):
    # Takes a lat and long as input and finds the nearest station
    # Looks up info about that station from NOAA files and returns a dict
    # Containing weather info as well as the station
    allstations = get_stations_dict()
    station = get_nearest_station(latlong, allstations)[0]
    weather = get_station_weather(station['ghcn_id'])
    weather.update({'station': station})
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
    month_mean_extreme['year'] = yearly_mean_of_extremes

    if max_not_min:
        month_record_extreme['year'] = round(max(month_record_extreme.values()), 2)
    else:
        month_record_extreme['year'] = round(min(month_record_extreme.values()), 2)

    return month_mean_extreme, month_record_extreme

def get_min_max_mean_record(station_id):
    # Takes a station ID as input and returns a dictionary with mean
    # and record maxes and mins for each month of the year in a dictionary

    # I have downloaded these .dly files locally but they can be requested from
    # ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/all/
    lines = open('../../ghcnd_all/' + station_id + '.dly').readlines()
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
    template_filler.get_weatherbox(cities[0])
    # #
    # json.dump(cities, open('cities.json', 'wb'))


    # from pprint import pprint
    # pprint(get_monthly_normals(line))
    # i = 0
    # for month in line.split():
    #     print(i)
    #     print(month)
    #     print('')
    #     i += 1

main()
