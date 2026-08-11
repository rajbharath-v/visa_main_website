"""office/views.py — PDF generation for vouchers"""
import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Voucher

LOGO_PATH = os.path.join(settings.BASE_DIR, 'static', 'visa', 'img', 'logo.png')


@staff_member_required
def voucher_pdf(request, pk):
    voucher = get_object_or_404(Voucher, pk=pk)
    try:
        from reportlab.lib.pagesizes import A5, landscape
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
    except ImportError:
        return HttpResponse('reportlab is not installed. Run: pip install reportlab', status=500)

    buffer = io.BytesIO()
    page_w, page_h = landscape(A5)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A5),
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )

    # Styles
    def style(name, **kw):
        base = {'fontName': 'Helvetica', 'fontSize': 9, 'leading': 12}
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_company   = style('company',  fontName='Helvetica-Bold', fontSize=11, alignment=TA_LEFT, leading=15)
    s_title     = style('title',    fontName='Helvetica-Bold', fontSize=10, alignment=TA_CENTER, leading=14)
    s_normal    = style('normal',   fontSize=9)
    s_label     = style('label',    fontName='Helvetica-Bold', fontSize=8)
    s_value     = style('value',    fontSize=9)
    s_center    = style('center',   alignment=TA_CENTER, fontSize=8)
    s_right     = style('right',    alignment=TA_RIGHT,  fontSize=9)

    elements = []

    # Header — logo + company name (left-aligned, two lines) + voucher type
    company_para = Paragraph(
        'VIRTUAL INSTRUMENTATION &amp; SOFTWARE<br/>APPLICATIONS PVT. LTD.',
        s_company,
    )

    usable_w = page_w - 30*mm

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=13*mm, height=13*mm)
        logo_w = 16*mm
        title_w = 50*mm
        company_w = usable_w - logo_w - title_w
        header_data = [[
            logo,
            company_para,
            Paragraph(voucher.get_voucher_type_display().upper(), s_title),
        ]]
        header_table = Table(
            header_data,
            colWidths=[logo_w, company_w, title_w],
        )
    else:
        title_w = 50*mm
        company_w = usable_w - title_w
        header_data = [[
            company_para,
            Paragraph(voucher.get_voucher_type_display().upper(), s_title),
        ]]
        header_table = Table(
            header_data,
            colWidths=[company_w, title_w],
        )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # Voucher No & Date
    meta_data = [[
        Paragraph(f'<b>Voucher No:</b> {voucher.voucher_no}', s_normal),
        Paragraph(f'<b>Date:</b> {voucher.date.strftime("%d-%m-%Y")}', s_right),
    ]]
    meta_table = Table(meta_data, colWidths=[(page_w - 30*mm)/2]*2)
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(meta_table)
    elements.append(Spacer(1, 3*mm))

    # Debit row
    elements.append(Table(
        [[Paragraph('<b>Debit</b>', s_label), Paragraph(str(voucher.debit_account), s_value)]],
        colWidths=[20*mm, usable_w - 20*mm],
        style=TableStyle([('LINEBELOW', (1,0), (1,0), 0.5, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 4)])
    ))
    elements.append(Spacer(1, 2*mm))

    # Pay to row
    elements.append(Table(
        [[Paragraph('<b>Pay to</b>', s_label), Paragraph(voucher.pay_to, s_value)]],
        colWidths=[20*mm, usable_w - 20*mm],
        style=TableStyle([('LINEBELOW', (1,0), (1,0), 0.5, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 4)])
    ))
    elements.append(Spacer(1, 2*mm))

    # Amount row
    amt_str = f'₹ {voucher.amount:,.2f}'
    elements.append(Table(
        [[
            Paragraph('<b>Rs</b>', s_label),
            Paragraph(amt_str, s_value),
            Paragraph('<b>Rupees</b>', s_label),
            Paragraph(voucher.amount_in_words, s_value),
        ]],
        colWidths=[10*mm, 35*mm, 18*mm, usable_w - 63*mm],
        style=TableStyle([
            ('LINEBELOW', (1,0), (1,0), 0.5, colors.black),
            ('LINEBELOW', (3,0), (3,0), 0.5, colors.black),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ])
    ))
    elements.append(Spacer(1, 2*mm))

    # Cheque row (bank only)
    if voucher.voucher_type == 'bank':
        chq_date_str = voucher.chq_date.strftime('%d-%m-%Y') if voucher.chq_date else ''
        elements.append(Table(
            [[
                Paragraph('<b>Chq No</b>', s_label),
                Paragraph(voucher.chq_no or '', s_value),
                Paragraph('<b>dt.</b>', s_label),
                Paragraph(chq_date_str, s_value),
                Paragraph('<b>drawn on</b>', s_label),
                Paragraph(voucher.drawn_on or '', s_value),
            ]],
            colWidths=[16*mm, 30*mm, 8*mm, 28*mm, 20*mm, usable_w - 102*mm],
            style=TableStyle([
                ('LINEBELOW', (1,0), (1,0), 0.5, colors.black),
                ('LINEBELOW', (3,0), (3,0), 0.5, colors.black),
                ('LINEBELOW', (5,0), (5,0), 0.5, colors.black),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ])
        ))
        elements.append(Spacer(1, 2*mm))

    # Towards row
    elements.append(Table(
        [[Paragraph('<b>towards</b>', s_label), Paragraph(voucher.towards, s_value)]],
        colWidths=[20*mm, usable_w - 20*mm],
        style=TableStyle([('LINEBELOW', (1,0), (1,0), 0.5, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 4)])
    ))
    elements.append(Spacer(1, 8*mm))

    # Signatures
    sig_names = [
        ('Prepared by', voucher.prepared_by),
        ('Checked by',  voucher.checked_by),
        ('Approved by', voucher.approved_by),
        ('Received by', voucher.received_by),
    ]
    sig_data = [[Paragraph(f'<b>{lbl}</b><br/>{(str(s) if s else "")}', s_center) for lbl, s in sig_names]]
    sig_table = Table(sig_data, colWidths=[usable_w/4]*4)
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    filename = f'{voucher.voucher_no}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response