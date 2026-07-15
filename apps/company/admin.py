from django.contrib import admin

from .models import CompanyProfile, ExternalLink, WelcomeMessage

admin.site.register(CompanyProfile)
admin.site.register(WelcomeMessage)
admin.site.register(ExternalLink)
