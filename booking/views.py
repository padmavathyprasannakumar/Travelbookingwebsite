from decimal import Decimal
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    CabBookingForm,
    HotelBookingForm,
    SeatSelectionForm,
    SignUpForm,
    TourPackageBookingForm,
    TravelSearchForm,
)
from .models import Banner, Booking, Cab, Destination, FAQ, Hotel, Offer, Payment, SiteSetting, TourPackage, TravelService
from .services.cashfree import CashfreeAPIError, create_order as cashfree_create_order, fetch_order as cashfree_fetch_order


def home(request):
    banners = Banner.objects.filter(is_active=True)[:5]
    offers = Offer.objects.filter(is_active=True)[:6]
    flights = TravelService.objects.filter(is_active=True, service_type='flight')[:4]
    buses = TravelService.objects.filter(is_active=True, service_type='bus')[:4]
    trains = TravelService.objects.filter(is_active=True, service_type='train')[:4]
    popular_services = TravelService.objects.filter(is_active=True, service_type__in=['flight', 'bus', 'train'])[:6]
    tour_packages = TourPackage.objects.filter(is_active=True, is_featured=True)[:6]
    destinations = Destination.objects.filter(is_active=True, is_featured=True)[:6]
    hotels = Hotel.objects.filter(is_active=True)[:4]
    cabs = Cab.objects.filter(is_active=True)[:4]
    faqs = FAQ.objects.filter(is_active=True)[:4]
    form = TravelSearchForm()
    return render(request, 'home.html', {
        'site_setting': SiteSetting.load(),
        'banners': banners,
        'offers': offers,
        'flights': flights,
        'buses': buses,
        'trains': trains,
        'popular_services': popular_services,
        'tour_packages': tour_packages,
        'destinations': destinations,
        'hotels': hotels,
        'cabs': cabs,
        'faqs': faqs,
        'form': form,
    })


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def search_results(request):
    form = TravelSearchForm(request.GET or None)
    services = TravelService.objects.filter(is_active=True, service_type__in=['flight', 'bus', 'train'])
    if form.is_valid():
        services = services.filter(
            service_type=form.cleaned_data['service_type'],
            source__icontains=form.cleaned_data['source'],
            destination__icontains=form.cleaned_data['destination'],
            departure_date=form.cleaned_data['departure_date'],
        )
    else:
        services = TravelService.objects.none()
    return render(request, 'search_results.html', {'form': form, 'services': services})


SERVICE_PAGE_CONFIG = {
    'flight': {
        'title': 'Flights',
        'subtitle': 'Compare admin-managed flight schedules, timings, seats and prices.',
        'eyebrow': 'Book Flights',
        'icon': '✈',
        'add_label': 'Add flight details',
    },
    'bus': {
        'title': 'Buses',
        'subtitle': 'Find available bus routes, operators, timings, seats and prices.',
        'eyebrow': 'Book Buses',
        'icon': '🚌',
        'add_label': 'Add bus details',
    },
    'train': {
        'title': 'Trains',
        'subtitle': 'View train schedules, routes, seat availability and prices.',
        'eyebrow': 'Book Trains',
        'icon': '🚆',
        'add_label': 'Add train details',
    },
}


def service_list(request, service_type):
    config = SERVICE_PAGE_CONFIG[service_type]
    services = TravelService.objects.filter(is_active=True, service_type=service_type)

    source = request.GET.get('source', '').strip()
    destination = request.GET.get('destination', '').strip()
    departure_date = request.GET.get('departure_date', '').strip()

    if source:
        services = services.filter(source__icontains=source)
    if destination:
        services = services.filter(destination__icontains=destination)
    if departure_date:
        services = services.filter(departure_date=departure_date)

    return render(request, 'service_list.html', {
        'services': services,
        'service_type': service_type,
        'config': config,
        'source': source,
        'destination': destination,
        'departure_date': departure_date,
    })


def flight_list(request):
    return service_list(request, 'flight')


def bus_list(request):
    return service_list(request, 'bus')


def train_list(request):
    return service_list(request, 'train')


def travel_detail(request, pk):
    service = get_object_or_404(TravelService, pk=pk, is_active=True, service_type__in=['flight', 'bus', 'train'])
    unavailable = booked_seats_for_service(service)
    available_count = service.total_seats - len(unavailable)
    return render(request, 'travel_detail.html', {
        'service': service,
        'available_count': available_count,
        'unavailable': unavailable,
    })


def booked_seats_for_service(service):
    """Reserve seats while payment is pending so two users cannot choose the same seat."""
    taken = []
    bookings = Booking.objects.filter(travel_service=service, status__in=['pending', 'paid'])
    for booking in bookings:
        taken.extend(booking.selected_seats)
    return sorted(set(taken))


@login_required
def seat_selection(request, pk):
    service = get_object_or_404(TravelService, pk=pk, is_active=True, service_type__in=['flight', 'bus', 'train'])
    unavailable = booked_seats_for_service(service)
    all_seats = service.all_seat_numbers()

    if request.method == 'POST':
        form = SeatSelectionForm(request.POST)
        if form.is_valid():
            selected = form.cleaned_data['selected_seats']
            unavailable_now = booked_seats_for_service(service)
            overlap = set(selected).intersection(set(unavailable_now))
            invalid = set(selected).difference(set(all_seats))

            if overlap:
                messages.error(request, f'Seats already booked: {", ".join(sorted(overlap))}')
            elif invalid:
                messages.error(request, 'Invalid seat selection detected.')
            else:
                total = service.base_price * Decimal(len(selected))
                booking = Booking.objects.create(
                    user=request.user,
                    booking_type='travel',
                    travel_service=service,
                    travellers=len(selected),
                    selected_seats=selected,
                    total_amount=total,
                    status='pending',
                    payment_status='pending',
                )
                Payment.objects.create(booking=booking, amount=total, method='Cashfree', status='pending')
                messages.info(request, 'Seats reserved. Complete Cashfree payment to confirm your booking.')
                return redirect('payment_checkout', booking_id=booking.id)
    else:
        form = SeatSelectionForm()

    return render(request, 'seat_selection.html', {
        'service': service,
        'all_seats': all_seats,
        'unavailable': unavailable,
        'form': form,
    })


def tour_list(request):
    destination = request.GET.get('destination', '')
    category = request.GET.get('category', '')
    packages = TourPackage.objects.filter(is_active=True)
    if destination:
        packages = packages.filter(destination__icontains=destination)
    if category:
        packages = packages.filter(category=category)
    return render(request, 'tour_list.html', {
        'packages': packages,
        'destination': destination,
        'category': category,
        'categories': TourPackage.CATEGORY_CHOICES,
    })


@login_required
def tour_detail(request, pk):
    package = get_object_or_404(TourPackage, pk=pk, is_active=True)
    if request.method == 'POST':
        form = TourPackageBookingForm(request.POST)
        if form.is_valid():
            travellers = form.cleaned_data['travellers']
            if travellers > package.seats_available:
                messages.error(request, 'Requested travellers exceed available package slots.')
            else:
                with transaction.atomic():
                    package = TourPackage.objects.select_for_update().get(pk=package.pk)
                    if travellers > package.seats_available:
                        messages.error(request, 'This package was just booked by someone else. Please reduce travellers.')
                    else:
                        total = package.price_per_person * Decimal(travellers)
                        booking = Booking.objects.create(
                            user=request.user,
                            booking_type='tour',
                            tour_package=package,
                            travellers=travellers,
                            tour_travel_date=form.cleaned_data.get('travel_date') or package.start_date,
                            special_requests=form.cleaned_data.get('special_requests', ''),
                            total_amount=total,
                            status='pending',
                            payment_status='pending',
                        )
                        package.seats_available -= travellers
                        package.save(update_fields=['seats_available'])
                        Payment.objects.create(booking=booking, amount=total, method='Cashfree', status='pending')
                        messages.info(request, 'Tour package reserved. Complete Cashfree payment to confirm.')
                        return redirect('payment_checkout', booking_id=booking.id)
    else:
        form = TourPackageBookingForm(initial={'travel_date': package.start_date})
    return render(request, 'tour_detail.html', {'package': package, 'form': form})


def hotel_list(request):
    city = request.GET.get('city', '')
    hotels = Hotel.objects.filter(is_active=True)
    if city:
        hotels = hotels.filter(city__icontains=city)
    return render(request, 'hotel_list.html', {'hotels': hotels, 'city': city})


@login_required
def hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk, is_active=True)
    if request.method == 'POST':
        form = HotelBookingForm(request.POST)
        if form.is_valid():
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            nights = (check_out - check_in).days
            rooms = form.cleaned_data['rooms']
            if rooms > hotel.rooms_available:
                messages.error(request, 'Requested rooms are not available.')
            else:
                with transaction.atomic():
                    hotel = Hotel.objects.select_for_update().get(pk=hotel.pk)
                    if rooms > hotel.rooms_available:
                        messages.error(request, 'Requested rooms are no longer available.')
                    else:
                        total = hotel.price_per_night * Decimal(nights) * Decimal(rooms)
                        booking = Booking.objects.create(
                            user=request.user,
                            booking_type='hotel',
                            hotel=hotel,
                            travellers=form.cleaned_data['travellers'],
                            check_in=check_in,
                            check_out=check_out,
                            rooms=rooms,
                            special_requests=form.cleaned_data.get('special_requests', ''),
                            total_amount=total,
                            status='pending',
                            payment_status='pending',
                        )
                        hotel.rooms_available -= rooms
                        hotel.save(update_fields=['rooms_available'])
                        Payment.objects.create(booking=booking, amount=total, method='Cashfree', status='pending')
                        messages.info(request, 'Hotel rooms reserved. Complete Cashfree payment to confirm.')
                        return redirect('payment_checkout', booking_id=booking.id)
    else:
        form = HotelBookingForm()
    return render(request, 'hotel_detail.html', {'hotel': hotel, 'form': form})


def cab_list(request):
    city = request.GET.get('city', '')
    cabs = Cab.objects.filter(is_active=True)
    if city:
        cabs = cabs.filter(city__icontains=city)
    return render(request, 'cab_list.html', {'cabs': cabs, 'city': city})


@login_required
def cab_detail(request, pk):
    cab = get_object_or_404(Cab, pk=pk, is_active=True)
    if request.method == 'POST':
        form = CabBookingForm(request.POST)
        if form.is_valid():
            total = cab.base_fare + (cab.price_per_km * form.cleaned_data['distance_km'])
            booking = Booking.objects.create(
                user=request.user,
                booking_type='cab',
                cab=cab,
                travellers=1,
                pickup_location=form.cleaned_data['pickup_location'],
                drop_location=form.cleaned_data['drop_location'],
                pickup_date=form.cleaned_data['pickup_date'],
                distance_km=form.cleaned_data['distance_km'],
                special_requests=form.cleaned_data.get('special_requests', ''),
                total_amount=total,
                status='pending',
                payment_status='pending',
            )
            Payment.objects.create(booking=booking, amount=total, method='Cashfree', status='pending')
            messages.info(request, 'Cab booking created. Complete Cashfree payment to confirm.')
            return redirect('payment_checkout', booking_id=booking.id)
    else:
        form = CabBookingForm()
    return render(request, 'cab_detail.html', {'cab': cab, 'form': form})


def _payment_for_booking(booking):
    payment, _ = Payment.objects.get_or_create(
        booking=booking,
        defaults={'amount': booking.total_amount, 'method': 'Cashfree', 'status': 'pending'},
    )
    return payment


def _release_reserved_inventory(booking):
    if booking.booking_type == 'hotel' and booking.hotel and booking.rooms:
        booking.hotel.rooms_available += booking.rooms
        booking.hotel.save(update_fields=['rooms_available'])
    if booking.booking_type == 'tour' and booking.tour_package and booking.travellers:
        booking.tour_package.seats_available += booking.travellers
        booking.tour_package.save(update_fields=['seats_available'])


def _mark_booking_paid(booking, order_data):
    payment = _payment_for_booking(booking)
    booking.status = 'paid'
    booking.payment_status = 'success'
    booking.save(update_fields=['status', 'payment_status'])
    payment.status = 'success'
    payment.method = 'Cashfree'
    payment.cashfree_order_id = str(order_data.get('cf_order_id') or payment.cashfree_order_id or '')
    payment.payment_session_id = str(order_data.get('payment_session_id') or payment.payment_session_id or '')
    payment.gateway_response = order_data or payment.gateway_response
    payment.paid_at = timezone.now()
    payment.save(update_fields=['status', 'method', 'cashfree_order_id', 'payment_session_id', 'gateway_response', 'paid_at', 'updated_at'])


def _mark_booking_failed(booking, order_data):
    if booking.status == 'pending':
        _release_reserved_inventory(booking)
    payment = _payment_for_booking(booking)
    booking.status = 'failed'
    booking.payment_status = 'failed'
    booking.save(update_fields=['status', 'payment_status'])
    payment.status = 'failed'
    payment.gateway_response = order_data or payment.gateway_response
    payment.save(update_fields=['status', 'gateway_response', 'updated_at'])


def _extract_order_id(payload):
    data = payload.get('data', {}) if isinstance(payload, dict) else {}
    order = data.get('order', {}) if isinstance(data, dict) else {}
    return (
        payload.get('order_id') if isinstance(payload, dict) else None
    ) or order.get('order_id') or payload.get('orderId')


def _extract_order_status(payload):
    data = payload.get('data', {}) if isinstance(payload, dict) else {}
    order = data.get('order', {}) if isinstance(data, dict) else {}
    payment = data.get('payment', {}) if isinstance(data, dict) else {}
    return (
        (payload.get('order_status') if isinstance(payload, dict) else None)
        or order.get('order_status')
        or payment.get('payment_status')
        or ''
    ).upper()


@login_required
def payment_checkout(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related('payment'), id=booking_id, user=request.user)
    if booking.status == 'paid' and booking.payment_status == 'success':
        return redirect('payment_success', booking_id=booking.id)
    if booking.status in ['cancelled', 'failed']:
        messages.error(request, 'This booking cannot be paid because it is cancelled or failed.')
        return redirect('booking_detail', pk=booking.pk)

    payment = _payment_for_booking(booking)
    config_error = ''
    gateway_error = ''

    if not payment.payment_session_id:
        try:
            order_data = cashfree_create_order(booking, request)
            payment.cashfree_order_id = str(order_data.get('cf_order_id') or '')
            payment.payment_session_id = str(order_data.get('payment_session_id') or '')
            payment.gateway_response = order_data
            payment.save(update_fields=['cashfree_order_id', 'payment_session_id', 'gateway_response', 'updated_at'])
        except ImproperlyConfigured as exc:
            config_error = str(exc)
        except CashfreeAPIError as exc:
            gateway_error = str(exc)

    return render(request, 'payment_checkout.html', {
        'booking': booking,
        'payment': payment,
        'cashfree_mode': getattr(settings, 'CASHFREE_ENVIRONMENT', 'sandbox'),
        'config_error': config_error,
        'gateway_error': gateway_error,
    })


@login_required
def payment_return(request):
    order_id = request.GET.get('order_id') or request.GET.get('orderId') or request.GET.get('order')
    if not order_id:
        messages.error(request, 'Cashfree did not return an order id.')
        return redirect('my_bookings')

    booking = get_object_or_404(Booking, pnr=order_id, user=request.user)
    try:
        order_data = cashfree_fetch_order(order_id)
    except (ImproperlyConfigured, CashfreeAPIError) as exc:
        messages.error(request, f'Payment verification failed: {exc}')
        return redirect('payment_checkout', booking_id=booking.id)

    status = _extract_order_status(order_data)
    if status == 'PAID':
        _mark_booking_paid(booking, order_data)
        messages.success(request, f'Payment successful! Your PNR is {booking.pnr}.')
        return redirect('payment_success', booking_id=booking.id)
    if status in ['EXPIRED', 'TERMINATED', 'FAILED', 'CANCELLED']:
        _mark_booking_failed(booking, order_data)
        messages.error(request, 'Payment failed or expired. Your reserved inventory has been released.')
        return redirect('booking_detail', pk=booking.pk)

    payment = _payment_for_booking(booking)
    payment.gateway_response = order_data
    payment.save(update_fields=['gateway_response', 'updated_at'])
    messages.warning(request, 'Payment is still pending. Please complete the payment or retry after a few minutes.')
    return redirect('payment_checkout', booking_id=booking.id)


@csrf_exempt
def cashfree_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ignored'})
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid-json'}, status=400)

    order_id = _extract_order_id(payload)
    if not order_id:
        return JsonResponse({'status': 'missing-order-id'}, status=400)

    try:
        booking = Booking.objects.get(pnr=order_id)
    except Booking.DoesNotExist:
        return JsonResponse({'status': 'booking-not-found'}, status=404)

    status = _extract_order_status(payload)
    if status in ['PAID', 'SUCCESS']:
        _mark_booking_paid(booking, payload)
    elif status in ['FAILED', 'EXPIRED', 'TERMINATED', 'CANCELLED']:
        _mark_booking_failed(booking, payload)
    else:
        payment = _payment_for_booking(booking)
        payment.gateway_response = payload
        payment.save(update_fields=['gateway_response', 'updated_at'])
    return JsonResponse({'status': 'ok'})


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status != 'paid' or booking.payment_status != 'success':
        messages.warning(request, 'Please complete payment before viewing the success page.')
        return redirect('payment_checkout', booking_id=booking.id)
    return render(request, 'payment_success.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('travel_service', 'tour_package', 'hotel', 'cab', 'payment')
    return render(request, 'my_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('travel_service', 'tour_package', 'hotel', 'cab', 'payment'),
        pk=pk,
        user=request.user,
    )
    return render(request, 'booking_detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        if booking.status == 'cancelled':
            messages.info(request, 'This booking is already cancelled.')
        else:
            if booking.status in ['pending', 'paid']:
                _release_reserved_inventory(booking)
            booking.cancel()
            if hasattr(booking, 'payment') and booking.payment.status == 'pending':
                booking.payment.status = 'failed'
                booking.payment.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Booking cancelled successfully.')
        return redirect('booking_detail', pk=booking.pk)
    return render(request, 'cancel_booking.html', {'booking': booking})


@login_required
def staff_reports(request):
    # Reports contain revenue and all customer bookings. Only admin/staff users can view this page.
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Reports are available only for admin/staff users.')
        return redirect('home')

    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='paid').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    revenue = Booking.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    by_type = Booking.objects.values('booking_type').annotate(count=Count('id'), revenue=Sum('total_amount')).order_by('booking_type')
    latest_bookings = Booking.objects.select_related('user', 'travel_service', 'tour_package', 'hotel', 'cab').order_by('-created_at')[:10]
    return render(request, 'staff_reports.html', {
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'revenue': revenue,
        'by_type': by_type,
        'latest_bookings': latest_bookings,
    })
