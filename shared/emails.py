"""shared/emails.py — send enquiry notification emails"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_enquiry_notification(enquiry):
    """Send email to VISA sales team when new enquiry arrives"""
    product_name = (
        enquiry.product.name if enquiry.product
        else enquiry.product_name or 'General Enquiry'
    )
    subject = f'New Lead: {enquiry.name} — {product_name}'
    message = f"""
New enquiry received on VISA website!

Name:      {enquiry.name}
Company:   {enquiry.company or '—'}
Phone:     {enquiry.phone}
Email:     {enquiry.email}
City:      {enquiry.city or '—'}
Product:   {product_name}
Quantity:  {enquiry.quantity or '—'}
Source:    {enquiry.get_source_display()}

Message:
{enquiry.message}

---
View all leads: https://www.visapvtltd.co.in/admin/shared/enquiry/
    """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ENQUIRY_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        logger.error('Failed to send enquiry notification to sales team: %s', e)

    try:
        send_mail(
            subject='Thank you for contacting VISA Pvt. Ltd',
            message=f"""Dear {enquiry.name},

Thank you for your enquiry regarding {product_name}.

Our team will get back to you within 24 hours.

For urgent queries, please call us at +91 94453 50717 or WhatsApp us.

Best regards,
VISA Pvt. Ltd — Sales Team
Virtual Instrumentation & Software Applications Pvt. Ltd
Valasaravakkam, Chennai — 600 087
Phone: +91 94453 50717
Email: support@visapvtltd.co.in
Web: www.visapvtltd.co.in
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enquiry.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error('Failed to send auto-reply to customer %s: %s', enquiry.email, e)
