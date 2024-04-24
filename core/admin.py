from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.forms import CustomUserChangeForm, CustomUserCreationForm
from django.contrib.auth.models import Group
from allauth.account.models import EmailAddress
from core.models import (
    User,
    Skill,
    Category,
    Document,
    Event,
    Client,
    Worker,
    Sms,
    Timesheet,
    Invoice,
    Settings,
    EventStatus
    )

admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.unregister(EmailAddress)
admin.site.register(Skill)
admin.site.register(Category)
admin.site.register(Document)
admin.site.register(Event)
admin.site.register(Client)
admin.site.register(Worker)
admin.site.register(Sms)
admin.site.register(Timesheet)
admin.site.register(Invoice)
admin.site.register(Settings)
admin.site.register(EventStatus)