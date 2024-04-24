from .models import Settings

def company_settings(request):
    company_settings = Settings.objects.first()
    return {'company_settings': company_settings}