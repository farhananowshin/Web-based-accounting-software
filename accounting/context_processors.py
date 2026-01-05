from .models import CompanySettings


def site_settings(request):
    """
    Make SITE_NAME, SITE_LOGO, and CURRENCY available to all templates.
    """
    # Default values
    site_name = "Accounting Software"
    site_logo = None
    currency = "৳"

    try:
        settings_obj = CompanySettings.objects.first()

        if settings_obj:
            if settings_obj.company_name:
                site_name = settings_obj.company_name

            if settings_obj.currency_symbol:
                currency = settings_obj.currency_symbol

            if settings_obj.logo:
               
                site_logo = settings_obj.logo.url

    except Exception:
        
        pass

    return {
        "SITE_NAME": site_name,
        "SITE_LOGO": site_logo,
        "CURRENCY": currency,
    }
