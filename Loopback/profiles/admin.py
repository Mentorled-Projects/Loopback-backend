from django.contrib import admin
from .models import Profile, Interest, Skill

# Register your models here.
admin.site.register(Profile)

admin.site.register(Interest)

admin.site.register(Skill)