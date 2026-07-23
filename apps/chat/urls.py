from django.urls import path

from . import api_views, views

app_name = "chat"

urlpatterns = [
    path('home/', views.client_dashboard, name='client_home'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path("api/conversations/", api_views.ConversationListView.as_view(), name="api_conversations"),
    path(
        "api/conversations/<int:conversation_id>/messages/",
        api_views.ConversationHistoryView.as_view(),
        name="api_conversation_history",
    ),
    path(
        "api/conversations/<int:conversation_id>/attachments/",
        api_views.AttachmentUploadView.as_view(),
        name="api_attachment_upload",
    ),
]
from django.urls import path
from . import views


