import fitparse
import pandas as pd
from io import BytesIO




def process_fit_file(file_content):

    file_obj = BytesIO(file_content)

    # Load the FIT file
    fit_file = fitparse.FitFile(file_obj)

    power = []
    temperature = []
    hr = []
    elevation = []
    latitudes = []
    longitudes = []
    distance = 0
    ride_date = ''
    total_elapsed_time = ''
    max_speed = 0
    total_speed = 0
    count_speed = 0
    fit_file_id = None

    for record in fit_file.get_messages("record"):
        for data in record:
            if data.name == 'power':
                power.append(data.value)

            if data.name == 'temperature':
                temperature.append(data.value)

            if data.name == 'heart_rate':
                hr.append(data.value)


            if data.name == 'position_lat':
                latitude = semicircles_to_degrees(data.value)
                latitudes.append(latitude)

            if data.name == 'position_long':
                longitude = semicircles_to_degrees(data.value)
                longitudes.append(longitude)

            if data.name == 'distance':
                # The 'distance' field is found in the 'record' message
                distance = data.value


            if data.name == 'speed':
                speed = data.value * 2.23694  # Convert speed to miles per hour

                # Update max speed
                max_speed = max(max_speed, speed)

                # Update total speed for average calculation
                total_speed += speed
                count_speed += 1

            if data.name == "altitude":
                conversion_factor = 3.28084
                feet = float(data.value) * conversion_factor
                elevation.append(feet)

    for record in fit_file:
        if record.name == 'file_id':
            fit_file_id = record.get_value('time_created')

    for record in fit_file.get_messages('session'):
        for record_data in record:
            if record_data.name == 'start_time':
                ride_date = record_data.value

            if record_data.name == 'total_elapsed_time':
                total_elapsed_time = record_data.value


    avg_speed = total_speed / count_speed if count_speed > 0 else 0
    coordinates_list = [list(pair) for pair in zip(longitudes, latitudes)]

    return (power, temperature, hr, coordinates_list,
            distance, ride_date, total_elapsed_time,
            max_speed, avg_speed, elevation, fit_file_id)


def semicircles_to_degrees(semicircles):
    return semicircles / (2 ** 31) * 180

def get_coords(coordinates_list):
    coords = coordinates_list
    return coords

def cycling_norm_power(Power):
    # Remove None values from the list
    filtered_power = list(filter(None, Power))

    if not filtered_power:
        # Return default values if the filtered list is empty
        return None, None

    WindowSize = 30
    NumberSeries = pd.Series(filtered_power)
    Windows = NumberSeries.rolling(WindowSize)
    Power_30s = Windows.mean().dropna()
    PowerAvg = round(Power_30s.mean(), 0)
    NP = round((((Power_30s**4).mean())**0.25), 0)
    return NP, PowerAvg

def avg_temp(Temperature):
    filtered_temp = list(filter(None, Temperature))

    if not filtered_temp:
        # Return default values if the filtered list is empty
        return None, None

    fahrenheit = (1.8 * sum(Temperature) / len(Temperature)) + 32
    return round(fahrenheit, 0)


def get_heart_rate(HR):
    # Remove None values from the list
    filtered_hr = list(filter(None, HR))

    if not filtered_hr:
        # Return default values if the filtered list is empty
        return None, None, None

    hr_avg = round(sum(filtered_hr) / len(filtered_hr), 0)
    hr_max = max(filtered_hr)
    hr_min = min(filtered_hr)
    return hr_avg, hr_min, hr_max


def get_dist(Distance):
    meters_to_miles_conversion = 0.000621371
    distance_in_miles = Distance * meters_to_miles_conversion
    return distance_in_miles

def convert_total_elapsed_time(total_elapsed_time):
    # Convert the total_elapsed_time string to a float
    total_elapsed_time_float = float(total_elapsed_time)

    # Convert seconds to hours, minutes, and seconds
    hours, remainder = divmod(total_elapsed_time_float, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the result with two decimal places for seconds
    formatted_time = "{:02}:{:02}.{:02}".format(int(hours), int(minutes), int(seconds * 100))

    return formatted_time


def calculate_elevation_gain(elevation):
    if not elevation:
        return 0

    total_gain = 0
    current_elevation = float(elevation[0])

    for next_elevation in elevation[1:]:
        if next_elevation > current_elevation:
            total_gain += next_elevation - current_elevation
        current_elevation = next_elevation

    return total_gain



