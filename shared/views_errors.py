"""shared/views_errors.py — custom error handlers for all 3 sites"""
from django.shortcuts import render


def _site(request):
    return getattr(request, 'current_site', 'visa_main')


def error_400(request, exception=None):
    return render(request, 'errors/400.html', {'site': _site(request)}, status=400)


def error_403(request, exception=None):
    return render(request, 'errors/403.html', {'site': _site(request)}, status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', {'site': _site(request)}, status=404)


def error_500(request):
    return render(request, 'errors/500.html', {'site': _site(request)}, status=500)
