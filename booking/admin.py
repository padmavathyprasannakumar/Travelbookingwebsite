from django.contrib import admin

from .models import (
    Banner,
    Booking,
    Cab,
    Destination,
    FAQ,
    FooterLink,
    Hotel,
    Offer,
    Payment,
    SiteSetting,
    TourPackage,
    TravelService,
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'support_email', 'support_phone', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    fieldsets = (
        ('Branding', {'fields': ('site_name', 'logo_text', 'hero_title', 'hero_subtitle', 'hero_image')}),
        ('Support & Footer', {'fields': ('support_email', 'support_phone', 'footer_about')}),
        ('Social Links', {'fields': ('instagram_url', 'twitter_url', 'facebook_url')}),
        ('Status', {'fields': ('is_active',)}),
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'button_text', 'display_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('display_order', 'is_active')


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'starting_price', 'is_featured', 'is_active', 'display_order')
    list_filter = ('country', 'is_featured', 'is_active')
    search_fields = ('name', 'country', 'description')
    list_editable = ('starting_price', 'is_featured', 'is_active', 'display_order')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'offer_type', 'discount_text', 'coupon_code', 'valid_until', 'is_active')
    list_filter = ('offer_type', 'is_active')
    search_fields = ('title', 'description', 'coupon_code')


@admin.register(TravelService)
class TravelServiceAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'operator_name', 'source', 'destination', 'departure_date', 'departure_time', 'base_price', 'total_seats', 'is_active')
    list_filter = ('service_type', 'departure_date', 'is_active')
    search_fields = ('operator_name', 'source', 'destination', 'title')
    date_hierarchy = 'departure_date'


@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination', 'category', 'duration_days', 'price_per_person', 'seats_available', 'is_featured', 'is_active')
    list_filter = ('category', 'country', 'is_featured', 'is_active')
    search_fields = ('title', 'destination', 'country', 'description', 'highlights')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Basic Package Details', {
            'fields': ('title', 'destination', 'country', 'category', 'image', 'short_description', 'description')
        }),
        ('Duration & Inventory', {
            'fields': ('duration_days', 'duration_nights', 'start_date', 'end_date', 'price_per_person', 'seats_available')
        }),
        ('Content Blocks', {
            'fields': ('highlights', 'itinerary', 'inclusions', 'exclusions'),
            'description': 'Enter one item per line. These are shown dynamically on the public tour package page.'
        }),
        ('Visibility', {'fields': ('is_featured', 'is_active')}),
    )


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'price_per_night', 'rooms_available', 'rating', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'city', 'address')


@admin.register(Cab)
class CabAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'vehicle_type', 'seats', 'base_fare', 'price_per_km', 'is_active')
    list_filter = ('city', 'vehicle_type', 'is_active')
    search_fields = ('name', 'city')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    list_editable = ('display_order', 'is_active')


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'url')
    list_editable = ('display_order', 'is_active')


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = (
        'transaction_id',
        'cashfree_order_id',
        'payment_session_id',
        'gateway_response',
        'paid_at',
        'created_at',
        'updated_at',
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('pnr', 'user', 'booking_type', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('booking_type', 'status', 'payment_status', 'created_at')
    search_fields = ('pnr', 'user__username', 'user__email')
    readonly_fields = ('pnr', 'created_at', 'cancelled_at')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'cashfree_order_id', 'booking', 'amount', 'method', 'status', 'paid_at')
    list_filter = ('status', 'method')
    search_fields = ('transaction_id', 'cashfree_order_id', 'booking__pnr')
    readonly_fields = ('transaction_id', 'payment_session_id', 'gateway_response', 'paid_at', 'created_at', 'updated_at')
