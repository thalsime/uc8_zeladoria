import os
import qrcode
from io import BytesIO

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_salas_pdf():
    """
    Gera um arquivo PDF com uma página para cada sala ativa.

    A página possui um layout de duas colunas, com o QR Code no canto
    superior esquerdo e os detalhes textuais da sala à direita. O texto é
    formatado com quebras de linha, negrito nos rótulos e espaçamento
    para garantir a legibilidade, respeitando as margens do documento.
    """
    from .models import Sala
    file_path = os.path.join(settings.MEDIA_ROOT, 'salas_qr_codes.pdf')
    salas = Sala.objects.filter(ativa=True).order_by('nome_numero')
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='TitleText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=18,
        leading=22,
    ))

    for sala in salas:
        qr_size = 6 * cm
        padding = 1 * cm

        qr_x = margin
        qr_y = height - margin - qr_size

        text_x = qr_x + qr_size + padding
        available_text_width = width - text_x - margin
        text_frame_height = height - (2 * margin)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(str(sala.qr_code_id))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        image_for_pdf = ImageReader(buffer)

        c.drawImage(image_for_pdf, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 0.5 * cm, str(sala.qr_code_id))

        responsaveis = sala.responsaveis.all()
        nomes_responsaveis = ", ".join([user.username for user in responsaveis])

        def format_text(text):
            if text:
                return str(text).replace('\n', '<br/>')
            return 'N/A'

        story = []
        spacer = Spacer(1, 0.4 * cm)

        # Adiciona o título como parágrafos separados
        story.append(Paragraph(f"<b>Sala: {sala.nome_numero}</b>", styles['TitleText']))
        story.append(spacer)

        # Cria uma lista de campos para iterar
        info_fields = [
            ("Descrição", format_text(sala.descricao)),
            ("Instruções de Limpeza", format_text(sala.instrucoes)),
            ("Localização", format_text(sala.localizacao)),
            ("Capacidade", f"{sala.capacidade} pessoas"),
            ("Validade da Limpeza", f"{sala.validade_limpeza_horas} horas"),
            ("Responsáveis", nomes_responsaveis or 'N/A'),
        ]

        # Adiciona cada campo como um par de parágrafos (rótulo e valor)
        for label, value in info_fields:
            story.append(Paragraph(f"<b>{label}:</b>", styles['BoldLabel']))
            story.append(Paragraph(value, styles['NormalText']))
            story.append(spacer)

        text_frame = Frame(text_x, margin, available_text_width, text_frame_height, id='text_frame')
        text_frame.addFromList(story, c)

        c.showPage()

    c.save()
