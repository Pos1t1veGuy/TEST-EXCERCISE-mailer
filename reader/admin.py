from django.contrib import admin
from .models import EmailMessage, EmailAttachment, IMAP_server, EmailAccount

@admin.register(EmailMessage)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['From', 'To', 'subject', 'date_sent', 'date_received']

@admin.register(EmailAccount)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'server']

@admin.register(IMAP_server)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['url', 'port']

admin.register(EmailAttachment)