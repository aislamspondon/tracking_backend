from django.contrib import admin
from tracking_api.models import BlackListed, Tracking

# Register your models here.
admin.site.register(Tracking)
admin.site.register(BlackListed)