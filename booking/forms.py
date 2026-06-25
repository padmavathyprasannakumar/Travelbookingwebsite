from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class TravelSearchForm(forms.Form):
    SERVICE_CHOICES = [
        ('flight', 'Flights'),
        ('bus', 'Buses'),
        ('train', 'Trains'),
    ]
    service_type = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        widget=forms.Select(attrs={'aria-label': 'Service type'}),
    )
    source = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'placeholder': 'From city'}),
    )
    destination = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'placeholder': 'To city'}),
    )
    departure_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    travellers = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=1,
        widget=forms.NumberInput(attrs={'min': 1, 'max': 8}),
    )


class SeatSelectionForm(forms.Form):
    selected_seats = forms.CharField(widget=forms.HiddenInput())

    def clean_selected_seats(self):
        raw = self.cleaned_data['selected_seats']
        seats = [seat.strip().upper() for seat in raw.split(',') if seat.strip()]
        if not seats:
            raise forms.ValidationError('Please select at least one seat.')
        if len(seats) != len(set(seats)):
            raise forms.ValidationError('Duplicate seats are not allowed.')
        return seats


class HotelBookingForm(forms.Form):
    check_in = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    rooms = forms.IntegerField(min_value=1, max_value=5, initial=1)
    travellers = forms.IntegerField(min_value=1, max_value=10, initial=1)
    special_requests = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Room preference, early check-in, etc.'}))

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_in < timezone.localdate():
            self.add_error('check_in', 'Check-in date cannot be in the past.')
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError('Check-out date must be after check-in date.')
        return cleaned


class CabBookingForm(forms.Form):
    pickup_location = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Pickup location'}))
    drop_location = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Drop location'}))
    pickup_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    distance_km = forms.DecimalField(min_value=Decimal('1'), max_digits=8, decimal_places=2, initial=10)
    special_requests = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Pickup time, luggage, route notes, etc.'}))

    def clean_pickup_date(self):
        pickup_date = self.cleaned_data['pickup_date']
        if pickup_date < timezone.localdate():
            raise forms.ValidationError('Pickup date cannot be in the past.')
        return pickup_date


class TourPackageBookingForm(forms.Form):
    travel_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    travellers = forms.IntegerField(min_value=1, max_value=20, initial=2)
    special_requests = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Food preference, pickup request, room sharing, etc.'}))

    def clean_travel_date(self):
        travel_date = self.cleaned_data.get('travel_date')
        if travel_date and travel_date < timezone.localdate():
            raise forms.ValidationError('Travel date cannot be in the past.')
        return travel_date
