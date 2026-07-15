from django.contrib import admin

from .models import Attachment, Conversation, Message, MessageReaction


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["sender", "content", "created_at", "status"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["client", "updated_at", "is_archived"]
    search_fields = ["client__username", "client__email"]
    inlines = [MessageInline]


admin.site.register(Message)
admin.site.register(Attachment)
admin.site.register(MessageReaction)
