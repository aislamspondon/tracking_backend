from authentication import views
from django.urls import path

urlpatterns = [
    path('', views.intro, name="Authenticate"),
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('create/', views.registerUser, name="Authenticate"),
    path('delete/<str:pk>/', views.deleteUser, name="delete-user"),
    
]