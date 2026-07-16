from django.urls import path

from . import api_views, views

app_name = "chat"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/conversations/", api_views.ConversationListView.as_view(), name="api_conversations"),
    path(
        "api/conversations/<int:conversation_id>/messages/",
        api_views.ConversationHistoryView.as_view(),
        name="api_conversation_history",
    ),
]
