from .models import FooterLink, SiteSetting


def global_site_data(request):
    """Expose admin-managed branding/footer data to every template."""
    try:
        return {
            'site_settings': SiteSetting.load(),
            'footer_links': FooterLink.objects.filter(is_active=True)[:8],
        }
    except Exception:
        # During first migrate the database tables may not exist yet.
        return {
            'site_settings': SiteSetting(),
            'footer_links': [],
        }
