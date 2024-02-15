# Capstone

## Distinctiveness and Complexity

This Django application is designed to track cycling activities by consuming .fit
files generated from most popular gps-enabled cycling computers (Garmin, Wahoo,
CATEYE, etc.) and display data from the activity in an easy-to-consume dashboard.
The app utilized the Mapbox JavaScript library to display latitude and longitude
data on an interactive map. Bootstrap alerts (via the built-in Django 
Messages helper) have been added to improve user experience. Multiple additional 
packages have been utilized to improve the user interface, such as the Plotly 
python library for displaying charts, and the FitParse library to aid in saving 
activity data to the SQLite database. The other Python libraries, geocode and 
Pandas are utilized for geocoding latitude and longitude, and simple statistics, 
respectively.

There is no “social” component to the application, however a login is required to
save data to the specific user. Since this app is cycling-centric, several
statistics relevant to cycling are calculated based on the user’s Functional
Threshold Power (ftp).

It is worth noting that this application is optimized for reading .fit files from
Wahoo cycling computers, since that is what was available for testing. Activities
recorded with the popular mobile app, Strava can still be loaded but some of the 
metrics do not get converted correctly, such as speed, distance and 
temperature if imperial units are selected in Strava. The GPS track loads as 
expected, however. An enhancement could be made to convert this data correctly, 
but is seen as outside the scope of this project.

Activities such as skiing, running and hiking recorded with a device that
generates a .fit file can also be loaded. Metrics such as power and heart rate (
if not detected) will be left as 0 so the file can be parsed and a GPS track
generated.

While bugs may exist, attention has been given to handling duplicate files,
deleting activities and comments, and handling files with incomplete or
unexpected data.

Below are details related to individual components of this application.

## Files

### activity_details Template

The activity_details page provides summary information such as elapsed time,
distance, max speed, various heart rate and power metrics (normalized power, max,
etc.), and more. This page also displays the GPS route on a 3D JavaScript map
powered by the popular mapping library, Mapbox.

The activity_detail page also provides a breakdown of time spent in each power
zone, which is calculated by referencing the ftp the user provides 
while creating an account. There are many approaches to
defining power zones, but this app relies on the method developed by Dr. Andrew
Coggan and seven zones are utilized. The time spent in each zone is displayed in
a Plotly pie chart. The elevation data is used to show an elevation profile with
the Plotly library, as well.

Finally, activity_detail contains a simple comments section to provide notes
about the activity. This could be used to describe level of effort or other
notable things about the activity. The comments are written to the Comment model
and are related to the activity via foreign key. Comments can be added and
deleted.

### activity_list Template

The activity_list template provides a calendar view to easily upload .fit files
and navigate to an activity based on the date it was completed. An activity in
the calendar can be clicked on to be taken to the details for that event.

### Index Template

The My Activity Overview page provides summary information based on number of
activities, total distance, total elevation gain and max power. These metrics are
summaries of the activities within the timeframe specified by the user (all time,
week, month, year). When the selector is changed, the lower table is filtered 
and updated to reflect the activities for the given timeframe. Users can also 
follow the hyperlink in the Ride Date column to see activity details.


### Fit_file_utils.py Python File

In order to read .fit files, and save the output to the SQLite database, the
Python library FitParse is utilized in the fit_file_utils.py file. Activity data
parsed from this file is saved to the Activity model and is related
via primary key to the logged-in user. This utility file does much of the heavy
lifting of extracting rows from the .fit file (one row is added every second) 
and converting latitude and longitude to a list which can be used to visualize 
the GPS route in the activity_details template, as well as calculating 
normalized power (a popular metric for assessing activity intensity).


### map.js
This JavaScript file is responsible for rendering the Mapbox map, and 
translates the activity coordinates into a LineString. A Mapbox token is 
required to access the library. 

### styles.css
Stores css styling for different elements of this application

# Models

### Activity 
This model stores all the related data from the .fit file. The 
latitude and longitude (coordinates field) are stored as a string and parsed 
in the map.js file as needed. The best practice would be to utilize a PostgreSQL 
database with the PostGIS extension and store the GPS track as a shape, but 
the TextField datatype is sufficient for this application. 

### User 
Simple model used to store user information.

### UserAttributes 
Additional user info such as functional threshold power, birthdate, and weight 
are stored in this model.

### Comment 
Simple model to store comments, and relates to an activity via foreign key.

# How to run

Once the requirements are installed this app should function as expected.
