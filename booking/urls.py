from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Travel search and detail
    path('search/', views.search_results, name='search_results'),
    path('flights/', views.flight_list, name='flight_list'),
    path('buses/', views.bus_list, name='bus_list'),
    path('trains/', views.train_list, name='train_list'),
    path('travel/<int:pk>/', views.travel_detail, name='travel_detail'),
    path('travel/<int:pk>/seats/', views.seat_selection, name='seat_selection'),

    # Tour packages
    path('tours/', views.tour_list, name='tour_list'),
    path('tours/<int:pk>/', views.tour_detail, name='tour_detail'),

    # Cashfree payments
    path('payment/checkout/<int:booking_id>/', views.payment_checkout, name='payment_checkout'),
    path('payment/return/', views.payment_return, name='payment_return'),
    path('payment/webhook/cashfree/', views.cashfree_webhook, name='cashfree_webhook'),
    path('payment/success/<int:booking_id>/', views.payment_success, name='payment_success'),

    # Hotels
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/<int:pk>/', views.hotel_detail, name='hotel_detail'),

    # Cabs
    path('cabs/', views.cab_list, name='cab_list'),
    path('cabs/<int:pk>/', views.cab_detail, name='cab_detail'),

    # My Bookings
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),

    # Staff Reports
    path('dashboard/reports/', views.staff_reports, name='staff_reports'),
]
