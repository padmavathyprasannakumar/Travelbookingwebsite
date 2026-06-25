import random
import string
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class SiteSetting(models.Model):
    """Editable website-wide content for the admin dashboard."""
    site_name = models.CharField(max_length=100, default='myTrip Global')
    logo_text = models.CharField(max_length=40, default='myTrip')
    tagline = models.CharField(max_length=150, blank=True, default="")
    hero_title = models.CharField(max_length=180, default='Book flights, buses, trains, hotels, tours and cabs in one place')
    hero_subtitle = models.TextField(default='Search travel, select seats, choose packages and pay securely online with Cashfree.')
    hero_image = models.ImageField(upload_to='site/', blank=True, null=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=25, blank=True)
    footer_about = models.TextField(default='Book flights, buses, trains, tour packages, hotels and cabs from one trusted travel platform.')
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def load(cls):
        return cls.objects.filter(is_active=True).order_by('-updated_at').first() or cls()


class Banner(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    button_text = models.CharField(max_length=40, default='Book Now')
    button_link = models.CharField(max_length=255, default='/')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.title


class Destination(models.Model):
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=80, default='India')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f'{self.name}, {self.country}'


class Offer(models.Model):
    OFFER_TYPES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('tour', 'Tour'),
        ('hotel', 'Hotel'),
        ('cab', 'Cab'),
    ]
    title = models.CharField(max_length=150)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    description = models.TextField()
    discount_text = models.CharField(max_length=80, help_text='Example: FLAT 10% OFF')
    coupon_code = models.CharField(max_length=30, blank=True)
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    button_text = models.CharField(max_length=40, default='Book Now')
    button_link = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['offer_type', 'title']

    def __str__(self):
        return self.title


class TravelService(models.Model):
    SERVICE_TYPES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('train', 'Train'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    title = models.CharField(max_length=140)
    operator_name = models.CharField(max_length=100)
    source = models.CharField(max_length=80)
    destination = models.CharField(max_length=80)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_seats = models.PositiveIntegerField(default=40)
    seat_columns = models.PositiveIntegerField(default=4, help_text='Use 4 for bus/flight style, 6 for train style')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['departure_date', 'departure_time']

    def __str__(self):
        return f'{self.get_service_type_display()} - {self.source} to {self.destination}'

    @property
    def service_icon(self):
        return {'flight': '✈', 'bus': '🚌', 'train': '🚆'}.get(self.service_type, '🧳')

    @property
    def duration_label(self):
        start = timezone.datetime.combine(self.departure_date, self.departure_time)
        end = timezone.datetime.combine(self.arrival_date, self.arrival_time)
        minutes = int((end - start).total_seconds() // 60)
        if minutes < 0:
            minutes += 24 * 60
        hours, mins = divmod(minutes, 60)
        return f'{hours}h {mins}m'

    def all_seat_numbers(self):
        letters = string.ascii_uppercase
        seats = []
        for i in range(1, self.total_seats + 1):
            row = ((i - 1) // self.seat_columns) + 1
            col = letters[(i - 1) % self.seat_columns]
            seats.append(f'{row}{col}')
        return seats


class TourPackage(models.Model):
    CATEGORY_CHOICES = [
        ('family', 'Family'),
        ('honeymoon', 'Honeymoon'),
        ('adventure', 'Adventure'),
        ('pilgrimage', 'Pilgrimage'),
        ('weekend', 'Weekend'),
        ('international', 'International'),
    ]
    title = models.CharField(max_length=160)
    destination = models.CharField(max_length=120)
    country = models.CharField(max_length=80, default='India')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='family')
    duration_days = models.PositiveIntegerField(default=3)
    duration_nights = models.PositiveIntegerField(default=2)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    seats_available = models.PositiveIntegerField(default=20)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    highlights = models.TextField(blank=True, help_text='Add one highlight per line.')
    itinerary = models.TextField(blank=True, help_text='Add day-wise itinerary. One item per line is shown as a step.')
    inclusions = models.TextField(blank=True, help_text='Add one inclusion per line.')
    exclusions = models.TextField(blank=True, help_text='Add one exclusion per line.')
    image = models.ImageField(upload_to='tours/', blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price_per_person', 'destination']

    def __str__(self):
        return f'{self.title} - {self.destination}'

    @property
    def duration_label(self):
        return f'{self.duration_days} Days / {self.duration_nights} Nights'

    def highlights_list(self):
        return [item.strip() for item in self.highlights.splitlines() if item.strip()]

    def itinerary_list(self):
        return [item.strip() for item in self.itinerary.splitlines() if item.strip()]

    def inclusions_list(self):
        return [item.strip() for item in self.inclusions.splitlines() if item.strip()]

    def exclusions_list(self):
        return [item.strip() for item in self.exclusions.splitlines() if item.strip()]


class Hotel(models.Model):
    name = models.CharField(max_length=130)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    rooms_available = models.PositiveIntegerField(default=10)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    image = models.ImageField(upload_to='hotels/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'price_per_night']

    def __str__(self):
        return f'{self.name}, {self.city}'


class Cab(models.Model):
    VEHICLE_TYPES = [
        ('mini', 'Mini'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('tempo', 'Tempo Traveller'),
    ]
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    seats = models.PositiveIntegerField(default=4)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='cabs/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'base_fare']

    def __str__(self):
        return f'{self.name} - {self.get_vehicle_type_display()}'


class FAQ(models.Model):
    question = models.CharField(max_length=220)
    answer = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class FooterLink(models.Model):
    """Admin-managed footer links so footer content stays dynamic and clean."""
    title = models.CharField(max_length=80)
    url = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title


class Booking(models.Model):
    BOOKING_TYPES = [
        ('travel', 'Flight/Bus/Train'),
        ('tour', 'Tour Package'),
        ('hotel', 'Hotel'),
        ('cab', 'Cab'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid / Confirmed'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES)
    travel_service = models.ForeignKey(TravelService, on_delete=models.SET_NULL, null=True, blank=True)
    tour_package = models.ForeignKey(TourPackage, on_delete=models.SET_NULL, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    cab = models.ForeignKey(Cab, on_delete=models.SET_NULL, null=True, blank=True)
    pnr = models.CharField(max_length=15, unique=True, blank=True)
    travellers = models.PositiveIntegerField(default=1)
    selected_seats = models.JSONField(default=list, blank=True)
    check_in = models.DateField(blank=True, null=True)
    check_out = models.DateField(blank=True, null=True)
    rooms = models.PositiveIntegerField(default=1)
    pickup_location = models.CharField(max_length=150, blank=True)
    drop_location = models.CharField(max_length=150, blank=True)
    pickup_date = models.DateField(blank=True, null=True)
    tour_travel_date = models.DateField(blank=True, null=True)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    special_requests = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.pnr} - {self.user.username}'

    def save(self, *args, **kwargs):
        if not self.pnr:
            self.pnr = self.generate_pnr()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_pnr():
        while True:
            code = 'TRV' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            if not Booking.objects.filter(pnr=code).exists():
                return code

    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if self.payment_status == 'pending':
            self.payment_status = 'failed'
        self.save(update_fields=['status', 'cancelled_at', 'payment_status'])


class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default='Cashfree')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    cashfree_order_id = models.CharField(max_length=80, blank=True, db_index=True)
    payment_session_id = models.TextField(blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = 'PAY' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.booking.pnr} - {self.status}'
