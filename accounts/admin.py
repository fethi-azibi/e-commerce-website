from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile
from django.utils.html import format_html

class AdminAccount(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ('is_active',)
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'username')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superadmin')}),
        ('Dates', {'fields': ('date_joined', 'last_login')})
    )


class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="30" style="border-radius:50%;" >'.format(object.profile_picture.url))
    thumbnail.short_description="profile picture"
    list_display = ("thumbnail", "user", "city", "state", "country")

# Register your models here.
admin.site.register(Account, AdminAccount)
admin.site.register(UserProfile, UserProfileAdmin)

