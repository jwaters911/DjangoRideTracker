from django.contrib.auth import authenticate, login, logout
import json
import plotly.express as px
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Activity, User, Comment, UserAttributes
from .forms import UploadFileForm, CommentForm
from .fit_file_utils import process_fit_file, cycling_norm_power, get_coords, avg_temp, get_heart_rate, get_dist, convert_total_elapsed_time, calculate_elevation_gain
from django.db.models import Sum, Max
from django.utils import timezone
from datetime import date, datetime
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.html import format_html

def home(request):
    if request.user.is_authenticated:
        # Redirect to the main activity list page or another authenticated page
        return redirect('activity_list')
    else:
        # Redirect to the login page
        return redirect('login')
@login_required(login_url='/activity/login')
def index(request):
    activities = Activity.objects.filter(user=request.user).order_by('-ride_date')
    user_attributes = UserAttributes.objects.get(user=request.user)
    birthdate = user_attributes.birthdate
    user_age = calculate_age(birthdate)

    now = timezone.now()
    week_activities = activities.filter(ride_date__gte=timezone.now() - timezone.timedelta(days=7))
    month_activities = activities.filter(ride_date__month=timezone.now().month, ride_date__year=timezone.now().year)
    year_activities = activities.filter(ride_date__year=timezone.now().year)

    summary = {
        'week': {
            'count': week_activities.count(),
            'total_miles': week_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
            'total_elevation': week_activities.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0,
            'max_power': week_activities.aggregate(Max('max_power'))['max_power__max'] or 0,
        },
        'month': {
            'count': month_activities.count(),
            'total_miles': month_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
            'max_power': month_activities.aggregate(Max('max_power'))['max_power__max'] or 0,
        },
        'year': {
            'count': year_activities.count(),
            'total_miles': year_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
            'max_power': year_activities.aggregate(Max('max_power'))['max_power__max'] or 0,
        },
        'all_time': {
            'count': activities.count(),
            'total_miles': activities.aggregate(Sum('distance'))['distance__sum'] or 0,
            'total_elevation': activities.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0,
            'max_power': activities.aggregate(Max('max_power'))['max_power__max'] or 0,
        },
    }

    return render(request, 'activity/index.html', {'activities': activities, "summary": summary, "user_age": user_age,})


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "activity/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "activity/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        ftp = float(request.POST["ftp"])  # Parse to float
        weight = float(request.POST["weight"])  # Parse to float
        birthdate_str = request.POST["birthdate"]
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()  # Parse to date
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "activity/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            print(f"User: {user.username}")
            user_attributes = UserAttributes(user=user, ftp=ftp, weight=weight, birthdate=birthdate)
            print(f"User Attrs: {user_attributes.birthdate}")
            user_attributes.save()
        except IntegrityError:
            return render(request, "activity/register.html", {
                "message": "Username already taken."
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "activity/register.html")


@login_required(login_url='/activity/login/')
def activity_list(request):
    print(f"Logged-in user: {request.user.username}")

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            # Handle the uploaded file
            fit_file = request.FILES['fit_file']

            # Process the Fit file data
            file_content = fit_file.read()
            power, temperature, hr, coordinates_list, distance, ride_date, total_elapsed_time, max_speed, avg_speed, elevation, fit_file_id = process_fit_file(
                file_content)
            # Check if an activity with the same fit_file_id already exists
            existing_activity = Activity.objects.filter(fit_file_id=fit_file_id).first()


            if existing_activity:
                # Handle the case where a duplicate activity is found
                #return HttpResponseBadRequest("Duplicate file. This activity already exists.")
                messages.error(request, 'Duplicate file. This activity already exists.')
                return redirect('activity_list')

            user_instance = request.user

            activity = Activity.objects.create(
                fit_file_id=fit_file_id,
                user=user_instance,
                coordinates=get_coords(coordinates_list),
                power=power if power else None,
                avg_power=cycling_norm_power(power)[1] if power else 0,
                np_power=cycling_norm_power(power)[0] if power else 0,
                max_power=max(power, default=None) if power else None,
                avg_temp=avg_temp(temperature) if power else None,
                distance=get_dist(distance) if distance is not None else 0,
                ride_date=ride_date,
                total_elapsed_time=convert_total_elapsed_time(total_elapsed_time),
                hr_avg=get_heart_rate(hr)[0] if hr else 0,
                hr_max=get_heart_rate(hr)[2] if hr else None,
                hr_min=get_heart_rate(hr)[1] if hr else None,
                max_speed=max_speed,
                avg_speed=avg_speed,
                elevation=elevation if elevation else None,
                elevation_gain=calculate_elevation_gain(elevation) if calculate_elevation_gain else None,
            )

            # Handle None values before performing operations
            activity.avg_power = activity.avg_power or 0
            activity.np_power = activity.np_power or 0
            activity.hr_avg = activity.hr_avg or 0
            activity.hr_max = activity.hr_max or 0
            activity.hr_min = activity.hr_min or 0

            activity.save()

            activity_url = reverse('activity_details', args=[activity.id])

            success_message = f'Activity uploaded successfully: <a href="{activity_url}">View Activity</a>'

            # Use format_html to mark the string as safe HTML
            messages.success(request, format_html(success_message))

            return redirect('activity_list')
    else:
        form = UploadFileForm()

    activities = Activity.objects.filter(user=request.user).order_by('-ride_date')
    week_activities = activities.filter(ride_date__gte=timezone.now() - timezone.timedelta(days=7))

    month_activities = activities.filter(ride_date__month=timezone.now().month, ride_date__year=timezone.now().year)
    year_activities = activities.filter(ride_date__year=timezone.now().year)

    summary = {
        'week': {
            'count': week_activities.count(),
            'total_miles': week_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
        },
        'month': {
            'count': month_activities.count(),
            'total_miles': month_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
        },
        'year': {
            'count': year_activities.count(),
            'total_miles': year_activities.aggregate(Sum('distance'))['distance__sum'] or 0,
        },
        'all_time': {
            'count': activities.count(),
            'total_miles': activities.aggregate(Sum('distance'))['distance__sum'] or 0,
        },
    }

    return render(request, 'activity/activity_list.html', {'activities': activities, 'form': form, 'summary': summary})


def activity_details(request, activity_id):
    zones = {
        "Active Recovery (zone 1)": (0, 57),
        "Aerobic Endurance (zone 2)": (58, 76),
        "Tempo (zone 3)": (77, 91),
        "Lactate Threshold (zone 4)": (92, 106),
        "VO2 Max (zone 5)": (107, 121),
        "Anaerobic Capacity (zone 6)": (122, 200),
        "Neuromuscular power (zone 7)": (201, float('inf'))
    }

    # Convert percentages to decimal values for comparison
    percentage_to_decimal = 0.01
    ftp_percentages = {zone: (lower * percentage_to_decimal, upper * percentage_to_decimal) for zone, (lower, upper) in
                       zones.items()}

    zone_colors = {
        "Active Recovery (zone 1)": "#F5D400",
        "Aerobic Endurance (zone 2)": "#ECB10A",
        "Tempo (zone 3)": "#E48D13",
        "Lactate Threshold (zone 4)": "#DB6A1D",
        "VO2 Max (zone 5)": "#D24727",
        "Anaerobic Capacity (zone 6)": "#CA2330",
        "Neuromuscular power (zone 7)": "#C1003A"
    }

    form = CommentForm()
    activity = get_object_or_404(Activity, id=activity_id)
    comments = Comment.objects.filter(activity=activity)
    elevation_list = parse_elevation_string(activity.elevation)

    try:
        user_attributes = get_object_or_404(UserAttributes, user=request.user)
        ftp = user_attributes.ftp
        power = parse_elevation_string(activity.power)
        time_per_zone = {zone: 0 for zone in zones}

        if not power:
            pie_html = "<p>No Power Data</p>"
        else:
            for p in power:
                for zone, (lower, upper) in ftp_percentages.items():
                    if lower <= p / ftp <= upper:
                        time_per_zone[zone] += 1

            # Convert seconds to minutes for better readability
            time_per_zone_minutes = {zone: minutes for zone, minutes in time_per_zone.items()}


            pie = px.pie(
                names=[f"{zone}" for zone in time_per_zone_minutes.keys()],
                values=list(time_per_zone_minutes.values()),
                title="Time Spent in Each Power Zone",
                color=list(zones.keys()),  # Use the zone names as colors
                color_discrete_map=zone_colors,
                category_orders={"names": ["Active Recovery (zone 1)", "Aerobic Endurance (zone 2)", "Tempo (zone 3)",
                                           "Lactate Threshold (zone 4)", "VO2 Max (zone 5)",
                                           "Anaerobic Capacity (zone 6)", "Neuromuscular power (zone 7)"]}
            )
            pie.update_traces(hole=0.2)

            pie.update_layout(
                title_x=0.5,
                legend=dict(x=1, y=0.5)
            )

            pie_html = pie.to_html(full_html=False)

        if not elevation_list:
            chart_html = "<p>No Elevation Data</p>"  # or chart_html = ""
        else:
            # Elevation chart generation code
            fig = px.line(y=elevation_list, labels={'y': 'Elevation (Feet)'},
                          title='Elevation Profile')

            fig.update_layout(title_text='Elevation Profile',
                              yaxis_title='Elevation (Feet)',
                              title_x=0.5,
                              xaxis_title='')  # Set x-axis title to an empty string

            chart_html = fig.to_html(full_html=False)
    except:
        return HttpResponseBadRequest("UserAttributes not found for the logged-in user.")

    return render(request, 'activity/activity_details.html', {'activity': activity, 'form': form, 'comments': comments, 'chart_html': chart_html, 'pie_html': pie_html})


@login_required
def add_comment(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.activity = activity
            comment.save()

            # Add success message
            messages.success(request, 'Comment added successfully.')

            # Redirect to the activity details page
            return redirect('activity_details', activity_id=activity.id)
    else:
        form = CommentForm()

    return render(request, 'activity/activity_details.html', {'form': form, 'activity': activity})


def fetch_comments(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    comments = Comment.objects.filter(activity=activity)
    comments_data = [{'text': comment.text, 'id': comment.id} for comment in comments]
    return JsonResponse(comments_data, safe=False)


@require_POST
def edit_comment(request, activity_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, activity__pk=activity_id)

    if request.user != comment.user:
        # You may want to handle unauthorized access here
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    form = CommentForm(request.POST, instance=comment)

    if form.is_valid():
        form.save()
        return JsonResponse({'success': 'Comment updated successfully'})
    else:
        # Return errors if the form is not valid
        return JsonResponse({'error': 'Invalid form data', 'errors': form.errors}, status=400)


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        activity_id = comment.activity.id  # Get the associated activity ID before deletion
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect('activity_details', activity_id=activity_id)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def parse_elevation_string(elevation_string):
    if elevation_string is None:
        return 0

    # Clean up the string
    cleaned_string = elevation_string.replace("'", "").replace("[", "").replace("]", "")

    # Split the cleaned string into a list of values
    elevation_list = [float(value) for value in cleaned_string.split(',')]

    if not elevation_list:
        return 0

    return elevation_list


def update_summary(request):
    timeframe = request.GET.get('timeframe', 'all_time')
    now = timezone.now()

    # Fetch activities based on the selected timeframe
    if timeframe == 'week':
        activities = Activity.objects.filter(user=request.user, ride_date__gte=now - timezone.timedelta(days=7))
    elif timeframe == 'month':
        activities = Activity.objects.filter(user=request.user, ride_date__month=now.month, ride_date__year=now.year)
    elif timeframe == 'year':
        activities = Activity.objects.filter(user=request.user, ride_date__year=now.year)
    else:
        # Default to 'all_time'
        activities = Activity.objects.filter(user=request.user)

    # Calculate summary statistics
    summary = {
        'count': activities.count(),
        'total_miles': activities.aggregate(Sum('distance'))['distance__sum'] or 0,
        'total_elevation': activities.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0,
        'max_power': activities.aggregate(Max('max_power'))['max_power__max'] or 0,

    }

    # Render the activities HTML
    activities_html = render_to_string('activity/activities_partial.html', {'activities': activities})

    # Include the activities HTML and summary in the response
    updated_summary = {
        'activities_html': activities_html,
        'count': summary['count'],
        'total_miles': summary['total_miles'],
        'total_elevation': summary['total_elevation'],
        'max_power': summary['max_power'],
    }

    return JsonResponse(updated_summary)


def upload_activity(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            # Extract fit_file_id from the form data
            fit_file_id = form.cleaned_data['fit_file_id']

            # Check if an activity with the same fit_file_id already exists
            existing_activity = Activity.objects.filter(fit_file_id=fit_file_id).first()

            if existing_activity:
                # Handle the case where a duplicate activity is found
                return HttpResponseBadRequest("Duplicate file. This activity already exists.")
            else:
                # Continue with the upload process
                # ...

                # Save the new activity with the fit_file_id
                new_activity = form.save(commit=False)
                new_activity.fit_file_id = fit_file_id
                new_activity.save()

                # ...

                return redirect('success_page')  # Redirect to success page or another appropriate action

    else:
        form = UploadFileForm()

    return render(request, 'your_template.html', {'form': form})


def calculate_age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age



def delete_activity(request, activity_id):
    # Get the activity instance
    activity = get_object_or_404(Activity, id=activity_id)

    # Check if the request method is POST
    if request.method == 'POST':
        # Delete associated comments
        Comment.objects.filter(activity=activity).delete()

        # Delete the activity
        activity.delete()

        # Add a success message
        messages.success(request, 'Activity deleted successfully.')

        # Redirect to the activity list page
        return redirect('activity_list')  # Replace 'activity_list' with the actual URL name for the activity list page

    # If the request method is not POST, render a confirmation page
    return render(request, 'activity/activity_list.html', {'activity': activity})
