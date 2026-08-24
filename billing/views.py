"""billing/views.py — PDF and Excel generation for invoices"""
import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Invoice

LOGO_PATH = os.path.join(settings.BASE_DIR, 'static', 'visa', 'img', 'logo.png')

TERMS = [
    'Goods once sold will not be taken back.',
    'Our responsibility ceases absolutely as soon as the goods have been handed over to carriers.',
]

BANK_DETAILS = (
    'Beneficiary name: M/s Virtual Instrumentation &amp; Software Applications Pvt Ltd, '
    'Current Account No: 21260210000991, Bank Name: UCO Bank, Chennai - 600087, '
    'RTGS/IFSC Code: UCBA0002126, MICR Code: 600028027'
)


@staff_member_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
    except ImportError:
        return HttpResponse('reportlab is not installed. Run: pip install reportlab', status=500)

    buffer = io.BytesIO()
    page_w, page_h = A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    usable_w = page_w - 30*mm

    def style(name, **kw):
        base = {'fontName': 'Helvetica', 'fontSize': 9, 'leading': 12}
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_company  = style('company', fontName='Helvetica-Bold', fontSize=13, alignment=TA_LEFT, leading=16)
    s_sub      = style('sub', fontSize=8.5, alignment=TA_LEFT, leading=11, textColor=colors.HexColor('#333333'))
    s_title    = style('title', fontName='Helvetica-Bold', fontSize=16, alignment=TA_RIGHT, leading=18)
    s_label    = style('label', fontName='Helvetica-Bold', fontSize=8.5)
    s_value    = style('value', fontSize=8.5)
    s_billto   = style('billto', fontSize=9, leading=12)
    s_head     = style('head', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white, alignment=TA_CENTER)
    s_cell     = style('cell', fontSize=8.5, leading=11)
    s_cell_sm  = style('cell_sm', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#555555'))
    s_cell_r   = style('cell_r', fontSize=8.5, leading=11, alignment=TA_RIGHT)
    s_cell_c   = style('cell_c', fontSize=8.5, leading=11, alignment=TA_CENTER)
    s_summary_label = style('summary_label', fontSize=9, alignment=TA_RIGHT)
    s_summary_val   = style('summary_val', fontSize=9, alignment=TA_RIGHT)
    s_grand_label   = style('grand_label', fontName='Helvetica-Bold', fontSize=10.5, alignment=TA_RIGHT)
    s_grand_val     = style('grand_val', fontName='Helvetica-Bold', fontSize=10.5, alignment=TA_RIGHT)
    s_footer   = style('footer', fontSize=7.5, leading=10, textColor=colors.HexColor('#444444'))
    s_center8  = style('center8', fontSize=8, alignment=TA_CENTER)

    elements = []

    # ---------------- Header: logo + company + INVOICE title ----------------
    company_block = Paragraph(
        'Virtual Instrumentation &amp; Software Applications Pvt. Ltd.<br/>'
        '<font size="8">Office &amp; works: Vision Tower, Yogam Garden, 15/16/17, '
        'Brindhavan Nagar, Valasaravakkam, Chennai - 600 087<br/>'
        'Phone: 044 24860722 &nbsp;|&nbsp; www.visapvtltd.co.in &nbsp;|&nbsp; support@visapvtltd.co.in<br/>'
        'GST: 33AABCV2361D1ZT</font>',
        s_company,
    )
    title_block = Paragraph('PROFORMA INVOICE' if invoice.document_type == 'proforma' else 'INVOICE', s_title)

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=15*mm, height=15*mm)
        header_table = Table(
            [[logo, company_block, title_block]],
            colWidths=[18*mm, usable_w - 18*mm - 45*mm, 45*mm],
        )
    else:
        header_table = Table(
            [[company_block, title_block]],
            colWidths=[usable_w - 45*mm, 45*mm],
        )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#1D4ED8')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # ---------------- Bill To + Invoice meta ----------------
    bill_to = Paragraph(
        f'<b>To:</b><br/>{invoice.client.name}<br/>{invoice.client.address}'.replace('\n', '<br/>'),
        s_billto,
    )

    def meta_row(label, value):
        return [Paragraph(f'<b>{label}</b>', s_label), Paragraph(str(value) if value else '', s_value)]

    meta_rows = [
        meta_row('Invoice No.', invoice.invoice_no),
        meta_row('Date', invoice.invoice_date.strftime('%d-%m-%Y')),
        meta_row('Your PO No.', invoice.po_no),
        meta_row('PO Date', invoice.po_date.strftime('%d-%m-%Y') if invoice.po_date else ''),
        meta_row('DC No', invoice.dc_no),
        meta_row('RR/LR/RPP No', invoice.rr_lr_rpp_no),
        meta_row('Buyer GST', invoice.client.gstin),
        meta_row('From / To', f'{invoice.from_place} → {invoice.to_place}'),
    ]
    meta_table = Table(meta_rows, colWidths=[28*mm, 40*mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    top_block = Table(
        [[bill_to, meta_table]],
        colWidths=[usable_w - 70*mm, 70*mm],
    )
    top_block.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(top_block)
    elements.append(Spacer(1, 4*mm))

    # ---------------- Line items table ----------------
    headers = ['S.No', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total Price']
    data = [[Paragraph(h, s_head) for h in headers]]

    for i, item in enumerate(invoice.line_items.all(), start=1):
        sub_lines = []
        if item.model_no:
            sub_lines.append(f'Model: {item.model_no}')
        if item.hsn_code:
            sub_lines.append(f'HSN: {item.hsn_code}')
        if item.serial_no:
            sub_lines.append(f'S.No: {item.serial_no}')
        desc_html = item.description
        if sub_lines:
            desc_html += '<br/>' + '<br/>'.join(f'<font color="#555555" size="7.5">{s}</font>' for s in sub_lines)

        data.append([
            Paragraph(str(i), s_cell_c),
            Paragraph(desc_html, s_cell),
            Paragraph(f'{item.qty:g}', s_cell_c),
            Paragraph(item.unit, s_cell_c),
            Paragraph(f'{item.unit_price:,.2f}', s_cell_r),
            Paragraph(f'{item.amount:,.2f}', s_cell_r),
        ])

    col_widths = [usable_w * w for w in [0.07, 0.43, 0.08, 0.08, 0.15, 0.19]]
    items_table = Table(data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D4ED8')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))

    # ---------------- Tax summary block ----------------
    resolved = invoice.resolved_tax_type()
    summary_rows = [
        ['Sub Total', f'{invoice.subtotal:,.2f}'],
    ]
    if invoice.p_and_f:
        summary_rows.append(['Add: P & F', f'{invoice.p_and_f:,.2f}'])
    summary_rows.append(['Taxable Value', f'{invoice.taxable_value:,.2f}'])

    if resolved == 'igst':
        summary_rows.append([f'IGST {invoice.igst_rate:g}%', f'{invoice.igst_amount:,.2f}'])
    else:
        summary_rows.append([f'CGST {invoice.cgst_rate:g}%', f'{invoice.cgst_amount:,.2f}'])
        summary_rows.append([f'SGST {invoice.sgst_rate:g}%', f'{invoice.sgst_amount:,.2f}'])

    if invoice.insurance:
        summary_rows.append(['Insurance', f'{invoice.insurance:,.2f}'])
    if invoice.less_advance:
        summary_rows.append(['Less: Advance', f'-{invoice.less_advance:,.2f}'])
    summary_rows.append(['Round Off', f'{invoice.round_off:,.2f}'])

    summary_data = [
        [Paragraph(label, s_summary_label), Paragraph(val, s_summary_val)]
        for label, val in summary_rows
    ]
    summary_data.append([
        Paragraph('Grand Total', s_grand_label),
        Paragraph(f'&#8377; {invoice.grand_total:,.2f}', s_grand_val),
    ])

    summary_table = Table(summary_data, colWidths=[45*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1D4ED8')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    wrapper = Table([[None, summary_table]], colWidths=[usable_w - 85*mm, 85*mm])
    wrapper.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(wrapper)
    elements.append(Spacer(1, 3*mm))

    # ---------------- Amount in words ----------------
    if invoice.amount_in_words:
        elements.append(Paragraph(f'<b>Rupees:</b> {invoice.amount_in_words}', s_value))
        elements.append(Spacer(1, 4*mm))

    # ---------------- Bank details ----------------
    elements.append(Paragraph(BANK_DETAILS, s_footer))
    elements.append(Spacer(1, 4*mm))

    # ---------------- Terms ----------------
    terms_text = invoice.notes.strip() if invoice.notes.strip() else None
    terms_list = [terms_text] if terms_text else TERMS
    for i, t in enumerate(terms_list, start=1):
        elements.append(Paragraph(f'{i}. {t}', s_footer))
    elements.append(Spacer(1, 10*mm))

    # ---------------- Signature ----------------
    sig_table = Table(
        [[Paragraph('', s_center8), Paragraph('<b>Authorized Signatory</b>', s_center8)]],
        colWidths=[usable_w - 55*mm, 55*mm],
    )
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (1, 0), (1, 0), 0.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    doc_label = 'Proforma_Invoice' if invoice.document_type == 'proforma' else 'Invoice'
    filename = f'{doc_label}_{invoice.invoice_no}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@staff_member_required
def invoice_excel(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from io import BytesIO
    except ImportError:
        return HttpResponse('openpyxl is not installed. Run: pip install openpyxl', status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = f'Invoice {invoice.invoice_no}'

    bold = Font(bold=True)
    header_fill = PatternFill('solid', fgColor='1D4ED8')
    header_font = Font(bold=True, color='FFFFFF')
    thin = Side(style='thin', color='CCCCCC')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center')
    wrap = Alignment(wrap_text=True, vertical='top')
    right = Alignment(horizontal='right')

    LAST_COL = 6  # A..F

    # --- Company header ---
    ws.merge_cells('A1:F1')
    ws['A1'] = 'VIRTUAL INSTRUMENTATION & SOFTWARE APPLICATIONS PVT. LTD.'
    ws['A1'].font = Font(bold=True, size=13)
    ws['A1'].alignment = center

    ws.merge_cells('A2:F2')
    ws['A2'] = 'Office & works: Vision Tower, Yogam Garden, 15/16/17, Brindhavan Nagar, Valasaravakkam, Chennai - 600 087'
    ws['A2'].alignment = center
    ws['A2'].font = Font(size=9)

    ws.merge_cells('A3:F3')
    ws['A3'] = 'Phone: 044 24860722  |  www.visapvtltd.co.in  |  support@visapvtltd.co.in  |  GST: 33AABCV2361D1ZT'
    ws['A3'].alignment = center
    ws['A3'].font = Font(size=9)

    ws.merge_cells('A5:F5')
    doc_title = 'PROFORMA INVOICE' if invoice.document_type == 'proforma' else 'INVOICE'
    ws['A5'] = f'{doc_title} — {invoice.invoice_no}'
    ws['A5'].font = Font(bold=True, size=13, color='1D4ED8')
    ws['A5'].alignment = center

    # --- Bill To / meta ---
    row = 7
    ws.cell(row=row, column=1, value='To:').font = bold
    ws.cell(row=row, column=4, value='Invoice No.').font = bold
    ws.cell(row=row, column=5, value=invoice.invoice_no)
    ws.cell(row=row, column=6, value=invoice.invoice_date.strftime('%d-%m-%Y'))
    row += 1
    ws.cell(row=row, column=1, value=invoice.client.name)
    ws.cell(row=row, column=4, value='Your PO No.').font = bold
    ws.cell(row=row, column=5, value=invoice.po_no)
    row += 1
    for line in (invoice.client.address or '').splitlines():
        if line.strip():
            ws.cell(row=row, column=1, value=line.strip())
            row += 1
    ws.cell(row=row, column=4, value='DC No').font = bold
    ws.cell(row=row, column=5, value=invoice.dc_no)
    row += 1
    ws.cell(row=row, column=4, value='RR/LR/RPP No').font = bold
    ws.cell(row=row, column=5, value=invoice.rr_lr_rpp_no)
    row += 1
    ws.cell(row=row, column=4, value='Buyer GST').font = bold
    ws.cell(row=row, column=5, value=invoice.client.gstin)
    row += 1
    ws.cell(row=row, column=4, value='From / To').font = bold
    ws.cell(row=row, column=5, value=f'{invoice.from_place} -> {invoice.to_place}')
    row += 2

    # --- Line items ---
    headers = ['S.No', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total Price']
    header_row = row
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border
    row += 1

    for i, item in enumerate(invoice.line_items.all(), start=1):
        desc = item.description
        extra = []
        if item.model_no:
            extra.append(f'Model: {item.model_no}')
        if item.hsn_code:
            extra.append(f'HSN: {item.hsn_code}')
        if item.serial_no:
            extra.append(f'S.No: {item.serial_no}')
        if extra:
            desc += '\n' + '\n'.join(extra)

        ws.cell(row=row, column=1, value=i).border = border
        ws.cell(row=row, column=1).alignment = center
        c = ws.cell(row=row, column=2, value=desc)
        c.border = border
        c.alignment = wrap
        ws.cell(row=row, column=3, value=float(item.qty)).border = border
        ws.cell(row=row, column=3).alignment = center
        ws.cell(row=row, column=4, value=item.unit).border = border
        ws.cell(row=row, column=4).alignment = center
        p_cell = ws.cell(row=row, column=5, value=float(item.unit_price))
        p_cell.number_format = '#,##0.00'
        p_cell.border = border
        t_cell = ws.cell(row=row, column=6, value=float(item.amount))
        t_cell.number_format = '#,##0.00'
        t_cell.border = border
        row += 1

    row += 1

    # --- Tax summary ---
    resolved = invoice.resolved_tax_type()
    summary_rows = [('Sub Total', invoice.subtotal)]
    if invoice.p_and_f:
        summary_rows.append(('Add: P & F', invoice.p_and_f))
    summary_rows.append(('Taxable Value', invoice.taxable_value))
    if resolved == 'igst':
        summary_rows.append((f'IGST {invoice.igst_rate:g}%', invoice.igst_amount))
    else:
        summary_rows.append((f'CGST {invoice.cgst_rate:g}%', invoice.cgst_amount))
        summary_rows.append((f'SGST {invoice.sgst_rate:g}%', invoice.sgst_amount))
    if invoice.insurance:
        summary_rows.append(('Insurance', invoice.insurance))
    if invoice.less_advance:
        summary_rows.append(('Less: Advance', -invoice.less_advance))
    summary_rows.append(('Round Off', invoice.round_off))

    for label, val in summary_rows:
        ws.cell(row=row, column=5, value=label).font = bold
        ws.cell(row=row, column=5).alignment = right
        v_cell = ws.cell(row=row, column=6, value=float(val))
        v_cell.number_format = '#,##0.00'
        row += 1

    ws.cell(row=row, column=5, value='Grand Total').font = Font(bold=True, size=11, color='1D4ED8')
    ws.cell(row=row, column=5).alignment = right
    gt_cell = ws.cell(row=row, column=6, value=float(invoice.grand_total))
    gt_cell.font = Font(bold=True, size=11, color='1D4ED8')
    gt_cell.number_format = '#,##0.00'
    row += 2

    if invoice.amount_in_words:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        ws.cell(row=row, column=1, value=f'Rupees: {invoice.amount_in_words}').font = bold
        row += 2

    # --- Column widths ---
    widths = [8, 42, 8, 10, 14, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    doc_label = 'Proforma_Invoice' if invoice.document_type == 'proforma' else 'Invoice'
    filename = f'{doc_label}_{invoice.invoice_no}.xlsx'
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response