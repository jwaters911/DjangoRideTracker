import geocoder
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import json
mapbox_access_token = 'pk.eyJ1IjoiandhdGVyczkxMSIsImEiOiJjbG45ZXZ3a3kwNWF6MnVsbW1oeTA5MTZxIn0.YrMX72gd7B5se8TXluSWzQ'

class Comment(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.activity.ride_date}'


class User(AbstractUser):
    # Add unique related_name attributes to avoid clashes
    groups = models.ManyToManyField(Group, related_name='custom_user_set')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_set')



class UserAttributes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    weight = models.FloatField(blank=True, null=True)
    ftp = models.FloatField(blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)


class Activity(models.Model):
    fit_file_id = models.CharField(max_length=36, blank=True, null=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ride_date = models.DateTimeField(blank=True, null=True)
    elevation = models.TextField(blank=True, null=True)
    elevation_gain = models.FloatField(blank=True, null=True)
    total_elapsed_time = models.TextField(blank=True, null=True)
    max_speed = models.FloatField(blank=True, null=True)
    avg_speed = models.FloatField(blank=True, null=True)
    coordinates = models.TextField(blank=True, null=True)
    power = models.TextField(blank=True, null=True)
    avg_power = models.FloatField(blank=True, null=True)
    np_power = models.FloatField(blank=True, null=True)
    max_power = models.FloatField(blank=True, null=True)
    distance = models.FloatField(blank=True, null=True)
    avg_temp = models.FloatField(blank=True, null=True)
    hr_avg = models.FloatField(blank=True, null=True)
    hr_max = models.FloatField(blank=True, null=True)
    hr_min = models.FloatField(blank=True, null=True)