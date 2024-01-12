from django.contrib import admin
from .models import Activity, User, Comment, UserAttributes

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'coordinates', 'avg_power', 'np_power', 'avg_temp', 'hr_avg', 'hr_max', 'hr_min', 'elevation','power']
    search_fields = ['user__username', 'coordinates', 'avg_power', 'np_power', 'avg_temp', 'hr_avg', 'hr_max', 'hr_min', 'elevation','power']


admin.site.register(User)
admin.site.register(UserAttributes)
admin.site.register(Comment)