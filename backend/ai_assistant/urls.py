from django.urls import path
from .views import (
    AIChatView,
    AIConfirmSetupView,
    AIBookingView,
    
)

urlpatterns = [
    path(
        "chat/",
        AIChatView.as_view(),
        name="ai-chat",
    ),

    path(
        "confirm/",
        AIConfirmSetupView.as_view(),
        name="ai-confirm-setup",
    ),
    path(
        "book/",
        AIBookingView.as_view(),
        name="ai-booking",
    ),
    
]