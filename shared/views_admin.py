"""shared/views_admin.py — analytics dashboard for admin"""
import json
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from .models import Enquiry, Product, ProductCategory


@staff_member_required
def analytics_dashboard(request):
    now   = timezone.now()
    today = now.date()

    # ── Summary cards ─────────────────────────────────────────────────────────
    total        = Enquiry.objects.count()
    today_count  = Enquiry.objects.filter(created_at__date=today).count()
    week_count   = Enquiry.objects.filter(created_at__date__gte=today - timedelta(days=7)).count()
    month_count  = Enquiry.objects.filter(created_at__date__gte=today - timedelta(days=30)).count()
    new_count    = Enquiry.objects.filter(status='new').count()
    converted    = Enquiry.objects.filter(status='converted').count()
    conversion_rate = round(converted / total * 100, 1) if total else 0

    # ── 30-day daily trend ────────────────────────────────────────────────────
    trend_labels, trend_data = [], []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        trend_labels.append(day.strftime('%d %b'))
        trend_data.append(Enquiry.objects.filter(created_at__date=day).count())

    # ── Status breakdown ──────────────────────────────────────────────────────
    status_qs = Enquiry.objects.values('status').annotate(count=Count('id'))
    status_labels = [s['status'].title() for s in status_qs]
    status_data   = [s['count'] for s in status_qs]

    # ── Top 5 products by enquiries ───────────────────────────────────────────
    top_products = (
        Enquiry.objects.exclude(product=None)
        .values('product__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    prod_labels = [p['product__name'] or 'General' for p in top_products]
    prod_data   = [p['count'] for p in top_products]

    # ── Source breakdown ──────────────────────────────────────────────────────
    source_qs     = Enquiry.objects.values('source').annotate(count=Count('id'))
    source_labels = [s['source'].replace('_', ' ').title() for s in source_qs]
    source_data   = [s['count'] for s in source_qs]

    # ── City breakdown (top 5) ────────────────────────────────────────────────
    city_qs = (
        Enquiry.objects.exclude(city='').exclude(city=None)
        .values('city').annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # ── Recent 10 enquiries ───────────────────────────────────────────────────
    recent = Enquiry.objects.select_related('product').order_by('-created_at')[:10]

    # ── Product stats ─────────────────────────────────────────────────────────
    total_products  = Product.objects.filter(is_active=True).count()
    total_cats      = ProductCategory.objects.filter(is_active=True).count()

    return render(request, 'admin/visa_dashboard.html', {
        'title':           'Analytics Dashboard',
        # cards
        'total':           total,
        'today_count':     today_count,
        'week_count':      week_count,
        'month_count':     month_count,
        'new_count':       new_count,
        'converted':       converted,
        'conversion_rate': conversion_rate,
        'total_products':  total_products,
        'total_cats':      total_cats,
        # charts (JSON)
        'trend_labels':    json.dumps(trend_labels),
        'trend_data':      json.dumps(trend_data),
        'status_labels':   json.dumps(status_labels),
        'status_data':     json.dumps(status_data),
        'prod_labels':     json.dumps(prod_labels),
        'prod_data':       json.dumps(prod_data),
        'source_labels':   json.dumps(source_labels),
        'source_data':     json.dumps(source_data),
        # tables
        'recent':          recent,
        'city_qs':         city_qs,
    })
