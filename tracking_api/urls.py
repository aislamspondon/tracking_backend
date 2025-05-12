from django.urls import path
from tracking_api import views

urlpatterns = [
    path('tracking/', views.getAllTracking, name="tracking"),
    path('tracking/create/', views.CreateTracking, name="create_tracking"),
    path('tracking/<int:tracking_id>/', views.getSingleTracking, name="details_tracking"),
    path('tracking/<int:tracking_id>/update/', views.updateTracking, name="update_tracking"),
    path('tracking/<int:tracking_id>/delete/', views.deletetracking, name="delete_tracking"),
    path('tracking/delete/', views.deletetracking_list, name="delete_tracking_list"),
    # Blacklist 
    path('blacklist/', views.getAllBlackList, name="blacklist"),
    path('blacklist/create/', views.CreateBlacklisted, name="create_blacklist"),
    path('blacklist/<int:blacklist_id>/', views.getSingleBlacklisted, name="details_blacklist"),
    path('blacklist/<int:blacklist_id>/update/', views.updateBlacklisted, name="update_blacklist"),
    path('blacklist/<int:blacklist_id>/delete/', views.deleteBlacklisted, name="delete_blacklist"),
    # Track
    path('track/', views.trackOrder, name="track_order"),
    path('track_csv_upload/', views.upload_track_csv, name="track_csv_upload"),
    path('trackOrder/<str:order_number>/', views.trackingOrderDetails, name="track_order_details"),
    path('upload/tracking/', views.upload_tracking, name='upload-tracking')

    
]