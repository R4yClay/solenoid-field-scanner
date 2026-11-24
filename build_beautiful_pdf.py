#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор дизайнерской PDF-версии научно-исследовательской работы
с кликабельным оглавлением, карточками научного аппарата, книжной версткой
формул (STIX 300 DPI), стильными таблицами и подсветкой кода Python.

Автор: Лукьянов Кирилл Алексеевич (МОУ “Сланцевская СОШ №1”, 10 класс)
Научный руководитель: Заборская Ольга Владимировна, учитель физики
"""

import os
import re
from xml.sax.saxutils import escape
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak, KeepTogether, NextPageTemplate, Flowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT

# Настройка математического рендера STIX для уравнений (1.1)-(2.4)
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.family'] = 'STIXGeneral'
plt.rcParams['axes.unicode_minus'] = False

# Палитра (мягкая, комфортная для глаз академическая гамма)
C_NAVY = colors.HexColor('#122A4C')       # Глубокий темно-синий для главных заголовков
C_BLUE = colors.HexColor('#1D5B9B')       # Благородный синий для подзаголовков и акцентов
C_SLATE = colors.HexColor('#1E293B')      # Мягкий темно-графитовый основной текст (не режет глаза)
C_MUTED = colors.HexColor('#64748B')      # Вспомогательный серый (колонтитулы, подписи)
C_BG_BLUE = colors.HexColor('#F0F6FF')    # Нежно-голубой фон карточек
C_BG_AMBER = colors.HexColor('#FFFBEB')   # Теплый кремовый фон для Гипотезы
C_BG_GREEN = colors.HexColor('#F0FDF4')   # Мягкий мятный фон для Выводов по главам
C_BG_ZEBRA = colors.HexColor('#F8FAFC')   # Светлый фон четных строк таблиц и кода
C_BORDER = colors.HexColor('#CBD5E1')     # Тонкие линии рамок
C_AMBER_ACC = colors.HexColor('#D97706')  # Акцент гипотезы
C_GREEN_ACC = colors.HexColor('#15803D')  # Акцент выводов


def register_macos_fonts():
    sup = '/System/Library/Fonts/Supplemental'
    pdfmetrics.registerFont(TTFont('Georgia', f'{sup}/Georgia.ttf'))
    pdfmetrics.registerFont(TTFont('Georgia-Bold', f'{sup}/Georgia Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Georgia-Italic', f'{sup}/Georgia Italic.ttf'))
    pdfmetrics.registerFont(TTFont('Georgia-BoldItalic', f'{sup}/Georgia Bold Italic.ttf'))
    pdfmetrics.registerFontFamily(
        'Georgia', normal='Georgia', bold='Georgia-Bold',
        italic='Georgia-Italic', boldItalic='Georgia-BoldItalic'
    )

    pdfmetrics.registerFont(TTFont('Arial', f'{sup}/Arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', f'{sup}/Arial Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Italic', f'{sup}/Arial Italic.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-BoldItalic', f'{sup}/Arial Bold Italic.ttf'))
    pdfmetrics.registerFontFamily(
        'Arial', normal='Arial', bold='Arial-Bold',
        italic='Arial-Italic', boldItalic='Arial-BoldItalic'
    )

    pdfmetrics.registerFont(TTFont('CourierNew', f'{sup}/Courier New.ttf'))
    pdfmetrics.registerFont(TTFont('CourierNew-Bold', f'{sup}/Courier New Bold.ttf'))
    pdfmetrics.registerFont(TTFont('CourierNew-Italic', f'{sup}/Courier New Italic.ttf'))
    pdfmetrics.registerFontFamily(
        'CourierNew', normal='CourierNew', bold='CourierNew-Bold', italic='CourierNew-Italic'
    )


def render_pdf_equations(eq_dir):
    """Генерирует четкие 300-DPI формулы (1.1)–(1.5) и (2.1)–(2.4) без лишних полей."""
    os.makedirs(eq_dir, exist_ok=True)
    specs = {
        'pdf_eq_1_1': (r"$d\vec{B} = \frac{\mu_0}{4\pi} \cdot \frac{I \, \left[d\vec{l} \times \vec{r}\right]}{r^3}$", 14.5, 4.2, 0.65),
        'pdf_eq_1_2': (r"$B_{z,\mathrm{витка}}(0, z) = \frac{\mu_0 I R^2}{2\left(R^2 + (z - z_k)^2\right)^{3/2}}$", 14.5, 4.8, 0.72),
        'pdf_eq_1_3': (r"$B_z(0, z) = \frac{1}{2}\mu_0 n I (\cos\alpha_1 - \cos\alpha_2) = \frac{1}{2}\mu_0 n I \left( \frac{z + L/2}{\sqrt{R^2 + (z + L/2)^2}} - \frac{z - L/2}{\sqrt{R^2 + (z - L/2)^2}} \right)$", 12.2, 6.2, 0.78),
        'pdf_eq_1_4': (r"$B_z(0, 0) = \mu_0 n I \frac{L}{\sqrt{L^2 + 4R^2}} = B_0 \frac{L/D}{\sqrt{1 + (L/D)^2}}$", 14.0, 5.2, 0.75),
        'pdf_eq_1_5': (r"$U_H = S_B B_n + U_0 + u_{\mathrm{шум}}(t)$", 14.0, 4.2, 0.52),
        'pdf_eq_2_1': (r"$x' = R\cos\varphi_m, \qquad y' = R\sin\varphi_m, \qquad z' = z_k$", 13.8, 5.0, 0.50),
        'pdf_eq_2_2': (r"$\vec{r} = \left(x - R\cos\varphi_m;\; -R\sin\varphi_m;\; z - z_k\right)$", 13.8, 5.0, 0.52),
        'pdf_eq_2_3': (r"$B_x(x, z) = \frac{\mu_0 I R\,\Delta\varphi}{4\pi} \sum_{k=1}^{N} \sum_{m=1}^{n_\varphi} \frac{(z - z_k)\cos\varphi_m}{r_{k,m}^3}$", 13.8, 5.4, 0.82),
        'pdf_eq_2_4': (r"$B_z(x, z) = \frac{\mu_0 I R\,\Delta\varphi}{4\pi} \sum_{k=1}^{N} \sum_{m=1}^{n_\varphi} \frac{R - x\cos\varphi_m}{r_{k,m}^3}$", 13.8, 5.4, 0.82),
    }
    paths = {}
    for key, (formula, fsize, fw, fh) in specs.items():
        out_p = os.path.join(eq_dir, f'{key}.png')
        fig = plt.figure(figsize=(fw, fh), dpi=300)
        fig.patch.set_facecolor('#F8FAFC')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_facecolor('#F8FAFC')
        ax.text(0.5, 0.5, formula, ha='center', va='center', fontsize=fsize, color='#122A4C')
        plt.savefig(out_p, dpi=300, facecolor='#F8FAFC', bbox_inches='tight', pad_inches=0.06)
        plt.close(fig)
        paths[key] = out_p
    return paths


class CalloutBox(Flowable):
    """Плашка с мягким фоном и цветной левой полосой для Гипотезы, Цели и Выводов."""
    def __init__(self, paragraphs, width=166*mm, bg_color=C_BG_BLUE, accent_color=C_BLUE, pad=8):
        super().__init__()
        self.paragraphs = paragraphs
        self.box_width = width
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.pad = pad
        self.inner_w = width - 2 * pad - 6
        self.p_heights = []
        self.box_height = 0

    def wrap(self, availWidth, availHeight):
        self.box_width = min(self.box_width, availWidth)
        self.inner_w = self.box_width - 2 * self.pad - 6
        self.p_heights = []
        total_h = self.pad * 2
        for idx, p in enumerate(self.paragraphs):
            _, h = p.wrap(self.inner_w, availHeight)
            self.p_heights.append(h)
            total_h += h + (4 if idx < len(self.paragraphs) - 1 else 0)
        self.box_height = total_h
        return self.box_width, self.box_height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg_color)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.box_width, self.box_height, 5, stroke=1, fill=1)

        # Акцентная полоска слева
        c.setFillColor(self.accent_color)
        c.roundRect(0, 0, 4.2, self.box_height, 2, stroke=0, fill=1)
        c.rect(2.1, 0, 2.1, self.box_height, stroke=0, fill=1)

        y = self.box_height - self.pad
        for idx, p in enumerate(self.paragraphs):
            h = self.p_heights[idx]
            y -= h
            p.drawOn(c, self.pad + 6, y)
            y -= 4
        c.restoreState()


class SectionDocTemplate(BaseDocTemplate):
    """Шаблон документа с автоматическим сбором глав и подглав в кликабельное Оглавление."""
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self._bookmark_id = 0

    def beforeDocument(self):
        self._bookmark_id = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            sname = flowable.style.name
            if sname in ('ChapterHeading', 'SubHeading', 'SubConclusionHeading'):
                raw_txt = re.sub(r'<[^>]+>', '', flowable.getPlainText()).strip()
                self._bookmark_id += 1
                key = f'sec_{self._bookmark_id}'
                self.canv.bookmarkPage(key)
                level = 0 if sname == 'ChapterHeading' else 1
                self.notify('TOCEntry', (level, raw_txt, self.page, key))
                self.canv.addOutlineEntry(raw_txt, key, level=level, closed=False)


def draw_cover_canvas(canvas, doc):
    """Дизайн титульного листа (Страница 1, без колонтитула и номера страницы)."""
    canvas.saveState()
    w, h = A4

    # Верхний декоративный темно-синий блок-шапка
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, h - 34*mm, w, 34*mm, stroke=0, fill=1)
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, h - 36*mm, w, 2*mm, stroke=0, fill=1)

    # Тонкая рамка страницы
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(0.8)
    canvas.roundRect(14*mm, 14*mm, w - 28*mm, h - 56*mm, 6, stroke=1, fill=0)

    # Надпись в синей шапке
    canvas.setFillColor(colors.HexColor('#BFDBFE'))
    canvas.setFont('Arial-Bold', 9.5)
    canvas.drawCentredString(w / 2, h - 14*mm, "ВСЕРОССИЙСКИЙ КОНКУРС НАУЧНО-ИССЛЕДОВАТЕЛЬСКИХ РАБОТ ИМ. Д. И. МЕНДЕЛЕЕВА")
    canvas.setFillColor(colors.white)
    canvas.setFont('Arial-Bold', 12)
    canvas.drawCentredString(w / 2, h - 22*mm, "РЕГИОНАЛЬНЫЙ ЭТАП · КОНФЕРЕНЦИЯ «ПРАКТИКА – КРИТЕРИЙ ИСТИНЫ»")
    canvas.setFillColor(colors.HexColor('#93C5FD'))
    canvas.setFont('Arial', 9.5)
    canvas.drawCentredString(w / 2, h - 29*mm, "Передовые производственные технологии · Физика · Инженерное проектирование")

    # Нижняя подпись города и года
    canvas.setFillColor(C_NAVY)
    canvas.setFont('Arial-Bold', 11)
    canvas.drawCentredString(w / 2, 24*mm, "Ленинградская область · 2026 г.")
    canvas.restoreState()


def draw_body_canvas(canvas, doc):
    """Аккуратный верхний и нижний колонтитулы для страниц оглавления и основного текста."""
    canvas.saveState()
    w, h = A4

    # Верхний колонтитул
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(0.6)
    canvas.line(22*mm, h - 15*mm, w - 18*mm, h - 15*mm)

    canvas.setFillColor(C_MUTED)
    canvas.setFont('Arial', 8.5)
    canvas.drawString(22*mm, h - 12.5*mm, "Разработка автоматизированного устройства для измерения поля соленоидов")
    canvas.drawRightString(w - 18*mm, h - 12.5*mm, "Лукьянов К. А. · 2026")

    # Нижний колонтитул с плашкой номера страницы
    canvas.line(22*mm, 15*mm, w - 18*mm, 15*mm)
    pg_str = f"Стр. {doc.page}"
    canvas.setFillColor(C_BG_BLUE)
    canvas.roundRect(w / 2 - 12*mm, 7.5*mm, 24*mm, 5.5*mm, 2.5, stroke=0, fill=1)
    canvas.setFillColor(C_NAVY)
    canvas.setFont('Arial-Bold', 9)
    canvas.drawCentredString(w / 2, 9.1*mm, pg_str)
    canvas.restoreState()


def make_eq_table(img_path, eq_num_str, max_w_mm=132):
    """Помещает формулу в аккуратный светлый блок с номером уравнения справа."""
    from PIL import Image as PILImage
    with PILImage.open(img_path) as im:
        iw, ih = im.size
    disp_w = min(iw / 300.0 * 25.4, max_w_mm) * mm
    disp_h = disp_w * (ih / iw)

    img_flow = Image(img_path, width=disp_w, height=disp_h)
    num_style = ParagraphStyle('EqNum', fontName='Arial-Bold', fontSize=10, textColor=C_MUTED, alignment=TA_RIGHT)
    t = Table([[img_flow, Paragraph(eq_num_str, num_style)]], colWidths=[148*mm, 22*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_ZEBRA),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    return t


def make_styled_table(data, col_widths_mm):
    """Создает приятную для глаз таблицу с темно-синей шапкой и мягкой зеброй."""
    hdr_style = ParagraphStyle('THdr', fontName='Arial-Bold', fontSize=9.2, leading=12, textColor=colors.white, alignment=TA_CENTER)
    cell_left = ParagraphStyle('TCellL', fontName='Arial', fontSize=9.0, leading=12, textColor=C_SLATE, alignment=TA_LEFT)
    cell_bold = ParagraphStyle('TCellB', fontName='Arial-Bold', fontSize=9.0, leading=12, textColor=C_NAVY, alignment=TA_LEFT)
    cell_center = ParagraphStyle('TCellC', fontName='Arial', fontSize=9.0, leading=12, textColor=C_SLATE, alignment=TA_CENTER)

    rows_flow = []
    for r_i, row in enumerate(data):
        r_cells = []
        for c_i, val in enumerate(row):
            safe_val = escape(val)
            if r_i == 0:
                r_cells.append(Paragraph(safe_val, hdr_style))
            elif c_i == 0:
                r_cells.append(Paragraph(safe_val, cell_bold))
            else:
                st = cell_center if len(val) < 28 else cell_left
                r_cells.append(Paragraph(safe_val, st))
        rows_flow.append(r_cells)

    t = Table(rows_flow, colWidths=[w * mm for w in col_widths_mm], repeatRows=1)
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.45, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]
    for r_i in range(1, len(data)):
        bg = C_BG_ZEBRA if r_i % 2 == 1 else colors.white
        cmds.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
    t.setStyle(TableStyle(cmds))
    return t


def make_figure_block(img_path, caption_text, width_mm=142):
    """Аккуратно масштабирует рисунок пропорционально и добавляет подпись."""
    from PIL import Image as PILImage
    with PILImage.open(img_path) as im:
        iw, ih = im.size
    w_pt = width_mm * mm
    h_pt = w_pt * (ih / iw)
    # Чтобы крупные графики не переполняли высоту фрейма
    if h_pt > 112 * mm:
        h_pt = 112 * mm
        w_pt = h_pt * (iw / ih)

    cap_st = ParagraphStyle(
        'FigCap', fontName='Arial-Italic', fontSize=9.5, leading=13,
        textColor=C_NAVY, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10
    )
    img_obj = Image(img_path, width=w_pt, height=h_pt)
    img_obj.hAlign = 'CENTER'
    return KeepTogether([Spacer(1, 4), img_obj, Paragraph(escape(caption_text), cap_st)])


def highlight_python_line(line, line_no):
    """Легкая цветовая подсветка синтаксиса Python для ReportLab Paragraph."""
    num_prefix = f'<font color="#94A3B8">{line_no:3d} │ </font>'
    raw = line.rstrip('\r\n')
    if not raw.strip():
        return num_prefix

    stripped = raw.lstrip(' ')
    leading_spaces = '&nbsp;' * (len(raw) - len(stripped))

    if stripped.startswith('#'):
        return num_prefix + leading_spaces + f'<font color="#64748B"><i>{escape(stripped)}</i></font>'

    esc = escape(stripped)
    # Подсветка ключевых слов Python
    kw_pattern = r'\b(class|def|return|if|else|for|in|import|from|as|not|and|or|True|False|None|with)\b'
    esc = re.sub(kw_pattern, r'<font color="#1D4ED8"><b>\1</b></font>', esc)
    esc = esc.replace('  ', '&nbsp;&nbsp;')
    return num_prefix + leading_spaces + esc


def build_pdf(out_pdf_path, img_dir):
    register_macos_fonts()
    eq_paths = render_pdf_equations(img_dir)

    doc = SectionDocTemplate(
        out_pdf_path,
        pagesize=A4,
        leftMargin=22*mm,
        rightMargin=18*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title="Разработка автоматизированного устройства для измерения распределения магнитного поля соленоидов",
        author="Лукьянов Кирилл Алексеевич"
    )

    cover_frame = Frame(22*mm, 28*mm, A4[0] - 40*mm, A4[1] - 72*mm, id='cover_frame')
    body_frame = Frame(22*mm, 20*mm, A4[0] - 40*mm, A4[1] - 40*mm, id='body_frame')

    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[cover_frame], onPage=draw_cover_canvas),
        PageTemplate(id='Body', frames=[body_frame], onPage=draw_body_canvas),
    ])

    # Стили текста (приятная книжная типографика Georgia + заголовки Arial)
    st_body = ParagraphStyle(
        'Body', fontName='Georgia', fontSize=11.0, leading=16.8,
        textColor=C_SLATE, alignment=TA_JUSTIFY, firstLineIndent=8*mm, spaceAfter=6
    )
    st_body_noindent = ParagraphStyle(
        'BodyNoIndent', parent=st_body, firstLineIndent=0
    )
    st_callout = ParagraphStyle(
        'CalloutText', fontName='Georgia', fontSize=10.5, leading=15.5,
        textColor=C_SLATE, alignment=TA_LEFT, firstLineIndent=0
    )
    st_chap = ParagraphStyle(
        'ChapterHeading', fontName='Arial-Bold', fontSize=13.5, leading=18,
        textColor=C_NAVY, spaceBefore=8, spaceAfter=10, keepWithNext=True
    )
    st_sub = ParagraphStyle(
        'SubHeading', fontName='Arial-Bold', fontSize=11.5, leading=15.5,
        textColor=C_BLUE, spaceBefore=10, spaceAfter=6, keepWithNext=True
    )
    st_sub_conc = ParagraphStyle(
        'SubConclusionHeading', fontName='Arial-Bold', fontSize=11.0, leading=15,
        textColor=C_GREEN_ACC, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    st_tbl_title = ParagraphStyle(
        'TblTitle', fontName='Arial-Bold', fontSize=9.8, leading=13.5,
        textColor=C_NAVY, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )

    def B(txt):
        """Форматирует абзац с выделением начальной жирной фразы до точки/двоеточия."""
        return Paragraph(txt, st_body)

    story = []

    # =========================================================================
    # СТРАНИЦА 1: ДИЗАЙНЕРСКАЯ ОБЛОЖКА (ТИТУЛЬНЫЙ ЛИСТ)
    # =========================================================================
    story.append(Spacer(1, 18*mm))
    st_badge = ParagraphStyle('Badge', fontName='Arial-Bold', fontSize=10, leading=14, textColor=C_BLUE, alignment=TA_CENTER)
    story.append(Paragraph("СЕКЦИЯ № 1 · ИНЖЕНЕРНАЯ · IT-ТЕХНОЛОГИИ · ФИЗИЧЕСКАЯ", st_badge))
    story.append(Spacer(1, 8*mm))

    st_cover_title = ParagraphStyle(
        'CoverTitle', fontName='Arial-Bold', fontSize=20, leading=26,
        textColor=C_NAVY, alignment=TA_CENTER, spaceAfter=6*mm
    )
    story.append(Paragraph(
        "Разработка автоматизированного устройства<br/>для измерения распределения магнитного поля соленоидов",
        st_cover_title
    ))

    st_cover_sub = ParagraphStyle(
        'CoverSub', fontName='Georgia-Italic', fontSize=11.5, leading=16,
        textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=14*mm
    )
    story.append(Paragraph(
        "Цифровая модель двухкоординатного сканирующего магнитометра на основе<br/>"
        "закона Био — Савара — Лапласа и стохастической модели датчика Холла",
        st_cover_sub
    ))

    # Мини-превью тепловой карты на обложке
    hm_path = os.path.join(img_dir, 'fig3_2d_heatmap.png')
    if os.path.exists(hm_path):
        cov_img = Image(hm_path, width=118*mm, height=68*mm)
        cov_img.hAlign = 'CENTER'
        story.append(cov_img)
        story.append(Spacer(1, 10*mm))

    # Плашка с автором и научным руководителем
    author_card_p = [
        Paragraph('<font name="Arial-Bold" color="#122A4C">Выполнил:</font> Лукьянов Кирилл Алексеевич, обучающийся 10 класса МОУ “Сланцевская СОШ №1” Сланцевского района', st_callout),
        Paragraph('<font name="Arial-Bold" color="#122A4C">Научный руководитель:</font> Заборская Ольга Владимировна, учитель физики МОУ “Сланцевская СОШ №1”', st_callout),
    ]
    story.append(CalloutBox(author_card_p, width=170*mm, bg_color=C_BG_BLUE, accent_color=C_NAVY, pad=10))

    story.append(NextPageTemplate('Body'))
    story.append(PageBreak())

    # =========================================================================
    # СТРАНИЦА 2: КРАСИВОЕ КЛИКАБЕЛЬНОЕ ОГЛАВЛЕНИЕ
    # =========================================================================
    st_toc_header = ParagraphStyle(
        'TOCHeader', fontName='Arial-Bold', fontSize=15.5, leading=20,
        textColor=C_NAVY, spaceAfter=2*mm
    )
    story.append(Paragraph("ОГЛАВЛЕНИЕ", st_toc_header))
    st_toc_hint = ParagraphStyle(
        'TOCHint', fontName='Georgia-Italic', fontSize=9.2, leading=12.5,
        textColor=C_MUTED, spaceAfter=3.5*mm
    )
    story.append(Paragraph("Нажмите на любой раздел оглавления для быстрого перехода к соответствующей странице документа.", st_toc_hint))

    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle(
            name='TOCLvl0', fontName='Arial-Bold', fontSize=9.7, leading=13.2,
            textColor=C_NAVY, leftIndent=0, rightIndent=8*mm,
            spaceBefore=3.5, spaceAfter=1.2
        ),
        ParagraphStyle(
            name='TOCLvl1', fontName='Georgia', fontSize=9.4, leading=12.4,
            textColor=C_SLATE, leftIndent=6*mm, rightIndent=8*mm,
            spaceBefore=0.8, spaceAfter=0.8
        ),
    ]
    story.append(toc)
    story.append(PageBreak())

    # =========================================================================
    # ВВЕДЕНИЕ
    # =========================================================================
    story.append(Paragraph("ВВЕДЕНИЕ", st_chap))

    story.append(B("<b>Актуальность темы исследования.</b> В современных передовых производственных технологиях, прецизионном приборостроении, медицинской диагностике (магнитно-резонансная томография), ускорительной технике и мехатронике важнейшую роль играют индуктивные элементы и электромагнитные исполнительные механизмы — соленоиды [1, с. 214]. Эффективность и точность работы электромагнитного клапана, линейного шагового актуатора, магнитной фокусирующей линзы или эталонного источника магнитного поля напрямую определяются пространственным распределением (топографией) вектора магнитной индукции внутри и в непосредственной окрестности катушки с током. В инженерной практике критически важно знать не только абсолютную величину индукции в геометрическом центре соленоида, но и протяженность зоны однородного поля («рабочего плато»), величину поперечной (радиальной) компоненты индукции и характер спада поля у торцов обмотки, обусловленный краевыми эффектами [4, с. 88]."))

    story.append(B("<b>Определение проблемы и противоречий по теме.</b> Традиционный лабораторный способ изучения магнитного поля катушек сводится к ручному перемещению щупа тесламетра по миллиметровой линейке вдоль оси соленоида. Такой подход характеризуется тремя фундаментальными недостатками: во-первых, высокой случайной погрешностью позиционирования датчика оператором (до 1–2 мм) и угловым перекосом плоскости чувствительного элемента Холла относительно силовых линий; во-вторых, колоссальной трудоемкостью при попытке построить двумерную (2D) или трехмерную (3D) топографическую карту поля, содержащую несколько тысяч узлов координатной сетки; в-третьих, необходимостью физического изготовления и намотки каждого прототипа катушки до того, как станут известны реальные границы однородности её поля [5, с. 142]. В то же время аналитические формулы школьного и базового вузовского курса физики позволяют легко рассчитать поле лишь для идеализированного бесконечно длинного соленоида либо строго на оси симметрии тонкой катушки [3, с. 205], тогда как вне оси аналитический расчет требует вычисления сложных эллиптических интегралов Лежандра или применения специализированных численных методов [2, с. 176; 6, с. 54]."))

    story.append(B("Таким образом, возникает научно-техническое противоречие между необходимостью быстрого, высокоточного и наглядного двумерного картирования магнитного поля соленоидов конечной длины на этапе их проектирования и высокой стоимостью, длительностью и погрешностью ручных натурных измерений. Разрешением данного противоречия является применение ключевого инструмента направления «Передовые производственные технологии» — концепции цифровых двойников (Digital Twins) [8, с. 42]. Разработка автоматизированного сканирующего измерителя в виде комплексной программно-математической модели, воспроизводящей как фундаментальные законы электромагнетизма, так и кинематику двухкоординатного стола и реальные метрологические характеристики датчика Холла (чувствительность, тепловой шум, квантование АЦП), позволяет проводить достоверные виртуальные испытания соленоидов любой геометрии."))

    # Карточка Объект + Предмет + Цель
    story.append(Spacer(1, 4))
    story.append(CalloutBox([
        Paragraph('<font name="Arial-Bold" color="#122A4C">Объект исследования:</font> пространственное распределение магнитного поля цилиндрического соленоида конечной длины с постоянным электрическим током.', st_callout),
        Paragraph('<font name="Arial-Bold" color="#122A4C">Предмет исследования:</font> алгоритмы автоматизированного численного сканирования вектора магнитной индукции и физические закономерности влияния геометрических параметров соленоида (отношения длины к диаметру <i>L / D</i>) и шага сетки сканирования на точность построения карты поля и протяженность зоны его однородности.', st_callout),
        Paragraph('<font name="Arial-Bold" color="#122A4C">Цель работы:</font> разработать программно-математическую модель автоматизированного устройства для сканирования и визуализации распределения магнитного поля соленоидов и исследовать с её помощью топографию поля катушек различной геометрии.', st_callout),
    ], width=170*mm, bg_color=C_BG_BLUE, accent_color=C_BLUE, pad=8))
    story.append(Spacer(1, 6))

    # Акцентная карточка Гипотезы
    story.append(CalloutBox([
        Paragraph('<font name="Arial-Bold" color="#B45309">Гипотеза исследования:</font> автоматизированное сканирование магнитного поля на основе дискретной суперпозиции закона Био — Савара — Лапласа и модели виртуального датчика Холла с пятикратным статистическим усреднением отсчетов позволяет строить достоверные двумерные карты магнитной индукции соленоида с относительной погрешностью <b>менее 0,5%</b> относительно аналитического эталона на оси, при этом протяженность центральной зоны однородного поля (с отклонением индукции не более 5% от центрального значения) превышает <b>60% длины катушки</b> при отношении её длины к диаметру <b><i>L / D</i> ≥ 5</b>.', st_callout),
    ], width=170*mm, bg_color=C_BG_AMBER, accent_color=C_AMBER_ACC, pad=8))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>Задачи исследования и проекта:</b>', st_body_noindent))
    for t_item in [
        "<b>1.</b> Спроектировать структурную и кинематическую схему цифрового автоматизированного сканирующего измерителя магнитного поля, включающую модуль параметрического задания катушки, двухкоординатный позиционер с растровым обходом («змейка»), виртуальный датчик Холла с АЦП и модуль научной визуализации.",
        "<b>2.</b> Разработать на языке программирования Python вычислительное ядро на основе численного интегрирования закона Био — Савара — Лапласа для расчета продольной (<i>B<sub>z</sub></i>) и радиальной (<i>B<sub>x</sub></i>) компонент магнитной индукции в произвольной точке пространства внутри и снаружи соленоида.",
        "<b>3.</b> Провести контрольный эксперимент (положительный и отрицательный контроли): верифицировать разработанный сканер путем сравнения численных и «зашумленных» измерений вдоль оси соленоида с точной аналитической формулой, а также оценить уровень собственного шума тракта при нулевом токе в обмотке (<i>I</i> = 0 А).",
        "<b>4.</b> Выполнить серию вычислительных экспериментов по двумерному картированию поля, анализу радиальных профилей индукции вблизи торцов катушки и определению количественной зависимости размера зоны однородного поля от безразмерного форм-фактора <i>L / D</i> и шага дискретизации сканера."
    ]:
        story.append(B(t_item))

    story.append(B("<b>Методы исследования:</b> численное моделирование и численное интегрирование дифференциальной формы закона Био — Савара — Лапласа методом средних прямоугольников по полярному углу; метод конечных шагов координатного сканирования; имитационное стохастическое моделирование погрешностей измерительного канала (метод Монте-Карло для гауссовского теплового шума датчика Холла, погрешности шагового привода и квантования АЦП); контрольный эксперимент (положительный эталонный контроль и отрицательный нулевой контроль); методы математической статистики (расчет выборочного среднего, стандартного отклонения, среднеквадратичной ошибки RMSE и ошибки линейной интерполяции); методы компьютерной визуализации скалярных и векторных полей."))

    story.append(Paragraph("<b>Этапы и календарный план-график проведения исследования и проекта (сентябрь – ноябрь 2026 г.):</b>", st_body_noindent))
    for st_item in [
        "<b>I этап — Задумка проекта и информационно-аналитический этап (05.09.2026 – 20.09.2026):</b> возникновение замысла проекта на занятиях по физике совместно с научным руководителем Заборской О. В. (05.09–08.09.2026); выявление проблемы высокой погрешности ручных измерений поля катушек и выбор концепции цифрового двойника 2D-сканера (09.09–12.09.2026); изучение научной литературы и базы данных eLIBRARY.RU [9, с. 1], анализ теории поля конечных соленоидов, характеристик датчиков Холла (Honeywell SS49E) и систем ЧПУ; формулировка цели, объекта, предмета, гипотезы и задач работы (13.09–20.09.2026).",
        "<b>II этап — Проектно-конструкторский этап (21.09.2026 – 10.10.2026):</b> проектирование четырёхмодульной архитектуры цифрового сканирующего измерителя и разработка кинематической схемы двунаправленного обхода области сканирования «змейкой» в плоскости сечения <i>y</i> = 0 (21.09–30.09.2026); вывод расчетных проекционных формул закона Био — Савара — Лапласа для <i>N</i> круговых витков, эталонной аналитической формулы на оси и математической модели погрешностей тракта «шаговый привод — датчик Холла — АЦП» (01.10–10.10.2026).",
        "<b>III этап — Программно-экспериментальный этап (11.10.2026 – 02.11.2026):</b> написание и отладка программного кода классов SolenoidModel и VirtualScannerDevice на языке Python с векторизацией вычислений в библиотеках NumPy и Matplotlib [10, с. 1] (11.10–18.10.2026); проведение контрольного эксперимента на оси соленоида с положительным и отрицательным контролем (19.10–23.10.2026); выполнение полного 2D-сканирования меридионального сечения (5 551 узел), построение тепловых карт и анализ радиальных срезов поля (24.10–28.10.2026); исследование зависимости зоны однородности поля от отношения <i>L / D</i> и оптимизация шага дискретизации сканера (29.10–02.11.2026).",
        "<b>IV этап — Аналитико-обобщающий этап и оформление работы (03.11.2026 – 13.11.2026):</b> статистическая обработка полученных массивов данных, сопоставление результатов с таблицами Калантарова — Цейтлина и работами других авторов, формулировка итоговых выводов и практических рекомендаций (03.11–08.11.2026); литературное оформление текста научно-исследовательской работы, проверка на оригинальность, подготовка раздаточного буклета А4 и презентации к защите на Конкурсе им. Д. И. Менделеева (09.11–13.11.2026)."
    ]:
        story.append(B(st_item))

    story.append(B("<b>Научная новизна работы</b> состоит в том, что автором разработана комплексная цифровая модель измерительного стенда, которая, в отличие от стандартных учебных калькуляторов поля на оси, сочетает трехмерный численный расчет внеосевых компонент поля по закону Био — Савара — Лапласа с реалистичной метрологической моделью тракта «шаговый привод — датчик Холла SS49E — АЦП». Впервые в рамках школьного исследовательского проекта детально исследована инверсия продольной компоненты поля <i>B<sub>z</sub></i> при пересечении стенки соленоида и получены точные количественные зависимости ширины плато однородности (для допусков 1% и 5%) от форм-фактора катушки <i>L / D</i>, а также обоснован оптимальный шаг дискретизации координатного стола."))

    story.append(B("<b>Теоретическая и практическая значимость работы:</b> теоретическая значимость заключается в наглядной систематизации и численной демонстрации краевых эффектов и структуры магнитного поля цилиндрических катушек конечной длины за пределами применимости элементарных формул. Практическая значимость состоит в том, что созданный программный комплекс является полностью готовым к работе инструментом: он позволяет инженерам и радиолюбителям рассчитывать геометрию соленоидов и выбирать шаг сканирования до постройки физического стенда (экономия материальных затрат на комплектующие более 18 000 руб.), а в школах и центрах дополнительного образования («Интеллект», «Кванториум») может использоваться как интерактивный виртуальный практикум по физике и передовым производственным технологиям."))

    story.append(PageBreak())

    # =========================================================================
    # ГЛАВА 1. ТЕОРЕТИЧЕСКИЙ АНАЛИЗ И ЛИТЕРАТУРНЫЙ ОБЗОР
    # =========================================================================
    story.append(Paragraph("ГЛАВА 1. ТЕОРЕТИЧЕСКИЙ АНАЛИЗ И ЛИТЕРАТУРНЫЙ ОБЗОР", st_chap))

    story.append(Paragraph("1.1. Физика магнитного поля соленоида конечной длины и природа краевых эффектов", st_sub))

    story.append(B("Магнитное поле представляет собой особую форму материи, посредством которой осуществляются силовые взаимодействия между движущимися электрическими зарядами или проводниками с током [3, с. 192]. Основной силовой (количественной) характеристикой магнитного поля в каждой точке пространства служит вектор магнитной индукции <b>B</b>, измеряемый в теслах (Тл). Направление вектора <b>B</b> в данной точке совпадает с направлением касательной к линии магнитной индукции (силовой линии), а густота силовых линий пропорциональна модулю вектора индукции |<b>B</b>| [1, с. 199]. Важнейшим фундаментальным свойством магнитного поля является его вихревой характер: в природе не существует магнитных зарядов (монополей), поэтому линии магнитной индукции всегда замкнуты сами на себя — они не имеют ни начала, ни конца [2, с. 164]."))

    story.append(B("Для расчета магнитного поля проводников произвольной геометрической формы в классической электродинамике применяется закон Био — Савара — Лапласа, установленный экспериментально Ж.-Б. Био и Ф. Саваром в 1820 году и обобщенный П. Лапласом [1, с. 201]. Согласно этому закону, элементарный участок проводника длины <i>d</i><b>l</b>, по которому течет постоянный ток силы <i>I</i>, создает в точке наблюдения, задаваемой радиус-вектором <b>r</b>, элементарную магнитную индукцию <i>d</i><b>B</b>:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_1_1'], "(1.1)"))
    story.append(Spacer(1, 4))

    story.append(B("где μ<sub>0</sub> = 4π · 10<sup>−7</sup> Гн/м ≈ 1,2566 · 10<sup>−6</sup> Гн/м — магнитная постоянная, а выражение [<i>d</i><b>l</b> × <b>r</b>] обозначает векторное произведение вектора элемента тока на радиус-вектор, проведенный от этого элемента к точке измерения. В силу принципа суперпозиции магнитных полей результирующая индукция <b>B</b>, создаваемая всей электромагнитной катушкой, определяется векторным суммированием (криволинейным интегралом) элементарных вкладов <i>d</i><b>B</b> по всей длине намотанного провода [2, с. 168]."))

    story.append(B("Цилиндрический соленоид (от греч. <i>solen</i> — трубка и <i>eidos</i> — вид) представляет собой катушку, образованную плотной винтовой намоткой изолированного провода на цилиндрический каркас радиуса <i>R</i> (диаметра <i>D</i> = 2<i>R</i>) и длины <i>L</i>. В технической физике показано, что если шаг намотки мал по сравнению с радиусом каркаса, то осевую составляющую тока вдоль образующей цилиндра можно не учитывать, заменив винтовой соленоид из <i>N</i> витков совокупностью из <i>N</i> параллельных соосных круговых контуров с током <i>I</i>, равномерно распределенных по длине катушки на интервале <i>z</i> от −<i>L</i>/2 до +<i>L</i>/2 [1, с. 215; 4, с. 89]."))

    story.append(B("Рассмотрим сначала один круговой виток радиуса <i>R</i> с центром на оси <i>Oz</i> в точке <i>z<sub>k</sub></i>. Для любой точки, лежащей строго на центральной оси симметрии витка (<i>x</i> = 0, <i>y</i> = 0, <i>z</i>), все элементы тока <i>d</i><b>l</b> находятся на одинаковом расстоянии <i>r</i> = √(<i>R</i><sup>2</sup> + (<i>z</i> − <i>z<sub>k</sub></i>)<sup>2</sup>), а поперечные проекции векторов <i>d</i><b>B</b> взаимно компенсируют друг друга. В результате интегрирования по окружности витка получается известная формула осевой индукции одиночного витка [3, с. 198]:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_1_2'], "(1.2)"))
    story.append(Spacer(1, 4))

    story.append(B("Если теперь перейти к непрерывному распределению витков с линейной плотностью намотки <i>n</i> = <i>N</i> / <i>L</i> (витков на метр длины) и проинтегрировать выражение (1.2) по координате <i>z<sub>k</sub></i> от левого торца (−<i>L</i>/2) до правого торца (+<i>L</i>/2), то мы получим точное аналитическое выражение для магнитной индукции на оси конечного тонкостенного соленоида [1, с. 217; 4, с. 91]:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_1_3'], "(1.3)", max_w_mm=145))
    story.append(Spacer(1, 4))

    story.append(B("где α<sub>1</sub> и α<sub>2</sub> — половинные углы, под которыми из точки наблюдения на оси видны соответственно левый и правый торцы обмотки соленоида. Формула (1.3) играет важнейшую роль в нашем исследовании: поскольку на оси симметрии она является математически точной, мы используем её в качестве эталона при проведении положительного контрольного эксперимента."))

    story.append(B("Детальный физический анализ уравнения (1.3) и структуры поля в объеме катушки позволяет выделить три ключевых явления:"))
    story.append(B("<b>1. Отличие поля в центре реальной катушки от идеального бесконечного соленоида.</b> Подставляя в (1.3) координату геометрического центра <i>z</i> = 0, получаем:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_1_4'], "(1.4)"))
    story.append(Spacer(1, 4))

    story.append(B("где <i>B</i><sub>0</sub> = μ<sub>0</sub><i>nI</i> — предельная индукция бесконечно длинного соленоида [3, с. 205]. Из формулы (1.4) видно, что отношение реального поля в центре к идеальному зависит исключительно от безразмерного геометрического параметра — отношения длины катушки к её диаметру <i>L / D</i> (форм-фактора соленоида). Так, при <i>L / D</i> = 1 (короткая катушка, длина равна диаметру) множитель равен 1/√2 ≈ 0,7071, то есть реальное поле в центре почти на 30% меньше значения, даваемого школьной формулой! Только при <i>L / D</i> ≥ 5 этот множитель превышает 0,98."))

    story.append(B("<b>2. Краевой эффект и полубесконечный предел на торцах.</b> При смещении точки наблюдения из центра к торцу обмотки (<i>z</i> → ±<i>L</i>/2) магнитное поле ослабевает, так как силовые линии начинают разгибаться и выходить из полости катушки наружу. В самой точке торца (<i>z</i> = <i>L</i>/2) для достаточно длинного соленоида (<i>L</i> ≫ <i>R</i>) магнитная индукция в центре торцевого сечения равна ровно половине индукции в глубине соленоида: <i>B</i><sub>торец</sub> ≈ 0,5 · <i>B</i><sub>0</sub> [1, с. 218]. Физическая причина этого красивого результата следует из принципа суперпозиции: если мысленно разрезать бесконечный соленоид пополам, то каждая половина в месте разреза создает ровно половину суммарного поля <i>B</i><sub>0</sub>."))

    story.append(B("<b>3. Невозможность описания трехмерного поля осевой формулой.</b> Формула (1.3) абсолютно не применима при смещении датчика с оси соленоида (при <i>x</i> ≠ 0). Вне оси расстояния от точки наблюдения до верхнего и нижнего участков каждого кругового витка становятся различными, вследствие чего у вектора магнитной индукции появляется радиальная (поперечная) составляющая <i>B<sub>x</sub></i>(<i>x, z</i>), а продольная составляющая <i>B<sub>z</sub></i>(<i>x, z</i>) становится функцией двух координат [2, с. 178]. Как показано в классическом справочнике П. Л. Калантарова и Л. А. Цейтлина [4, с. 96], аналитическое интегрирование вне оси приводит к полным эллиптическим интегралам Лежандра I и II рода <i>K</i>(<i>k</i>) и <i>E</i>(<i>k</i>), которые не выражаются через элементарные функции. Именно поэтому в современных инженерных расчетах применяются численные методы дискретной суперпозиции [6, с. 59]."))

    story.append(Paragraph("1.2. Сравнительный анализ методов и датчиков для измерения магнитной индукции", st_sub))

    story.append(B("Для экспериментального построения топографических карт магнитного поля в научных исследованиях и на производстве используются различные методы магнитометрии. Согласно монографии Ю. В. Афанасьева и соавторов [5, с. 112], выбор первичного измерительного преобразователя определяется диапазоном измеряемых полей, требуемым пространственным разрешением (локальностью), специфичностью к направлению поля и себестоимостью. Рассмотрим основные виды датчиков:"))
    story.append(B("— <b>Индукционные зонды (измерительные катушки Дятлова — Роговского).</b> Основаны на возникновении ЭДС индукции при изменении магнитного потока. Для измерения постоянного поля соленоида такую катушку приходится быстро выдергивать из поля или вращать с постоянной частотой, а диаметр намотки пробной катушки (5–10 мм) приводит к сильному пространственному усреднению поля в зоне больших градиентов у торцов соленоида [5, с. 118]."))
    story.append(B("— <b>Магниторезистивные датчики (AMR/GMR-сенсоры).</b> Изменяют свое омическое сопротивление под действием внешнего магнитного поля. Обладают высокой чувствительностью и малыми размерами, однако имеют выраженную нелинейность передаточной характеристики и склонность к гистерезису при полях свыше 5–10 мТл [7, с. 30]."))
    story.append(B("— <b>Феррозондовые и квантовые преобразователи.</b> Предназначены для измерения сверхслабых полей (магнитное поле Земли порядка 50 мкТл и его аномалии) и в полях технических соленоидов (10–50 мТл) уходят в глубокое насыщение [5, с. 134]."))
    story.append(B("— <b>Полупроводниковые датчики на эффекте Холла.</b> Как показано в современных работах по автоматизации магнитных измерений [7, с. 31], линейные интегральные датчики Холла (серий Honeywell SS49E, SS495A, Allegro A1324) являются оптимальным выбором для сканирующих магнитометров. Возникающее поперечное напряжение Холла <i>U<sub>H</sub></i> строго пропорционально проекции вектора магнитной индукции <i>B<sub>n</sub></i> на нормаль к плоскости кристалла:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_1_5'], "(1.5)"))
    story.append(Spacer(1, 4))

    story.append(B("где <i>S<sub>B</sub></i> — магнитная чувствительность преобразователя, <i>U</i><sub>0</sub> — напряжение нулевого смещения (при <i>B<sub>n</sub></i> = 0), а <i>u</i><sub>шум</sub>(<i>t</i>) — внутренний случайный шум датчика [7, с. 34]. Критическими преимуществами датчика Холла для нашего проекта являются: 1) малый размер активной зоны (около 0,4 × 0,4 мм), что позволяет считать измерение точечным; 2) высокая векторная специфичность — ориентируя кристалл перпендикулярно оси <i>z</i> или оси <i>x</i>, можно независимо измерять компоненты <i>B<sub>z</sub></i> и <i>B<sub>x</sub></i>; 3) широкий линейный диапазон (от ±0,02 мТл до ±100 мТл) и низкая стоимость."))

    story.append(Paragraph("1.3. Цифровые двойники и автоматизированные 2D/3D-сканеры в передовых производственных технологиях", st_sub))

    story.append(B("Обзор современных публикаций в электронной библиотеке eLIBRARY.RU [9, с. 1] показывает устойчивую тенденцию к автоматизации процесса картирования магнитных полей. Так, в работе В. Н. Баранова [7, с. 32] описан аппаратный стенд на базе микроконтроллера и шаговых двигателей для проверки катушек. Однако авторы подобных аппаратных работ отмечают, что при слепом выборе шага сканирования время снятия одной 2D/3D-карты может достигать 1,5–2 часов, а при слишком крупном шаге теряются пики поля у витков. Кроме того, без предварительного численного моделирования невозможно отделить реальную неоднородность поля катушки от собственных шумов АЦП и погрешностей механики стенда."))

    story.append(B("Именно для решения этих задач в индустрии 4.0 и направлении «Передовые производственные технологии» активно внедряется технология цифровых двойников (Digital Twins). Согласно аналитической монографии А. Прохорова и М. Лысачева [8, с. 45], цифровой двойник измерительной установки — это виртуальная копия прибора, которая на основе многоуровневой математической модели воспроизводит как физику исследуемого объекта (поле соленоида), так и работу самого измерительного тракта в реальных условиях с помехами и ограничениями дискретности. Создание такого цифрового двойника на языке Python с использованием высокопроизводительных векторных библиотек NumPy и Matplotlib [10, с. 1] позволяет за несколько секунд провести виртуальное сканирование, верифицировать алгоритм по контрольному эталону и оптимизировать параметры будущего натурного стенда."))

    story.append(Paragraph("Выводы по главе 1", st_sub_conc))
    story.append(CalloutBox([
        Paragraph("<b>1.</b> Литературный обзор показал, что точные алгебраические формулы описывают магнитное поле конечного соленоида только на его продольной оси, тогда как для изучения поля в объеме катушки, краевых эффектов и внеосевых зон необходим численный расчет методом суперпозиции по закону Био — Савара — Лапласа.", st_callout),
        Paragraph("<b>2.</b> Установлено, что наилучшим первичным преобразователем для координатного сканирования поля соленоидов является линейный датчик Холла, обладающий субмиллиметровым разрешением и высокой направленной специфичностью.", st_callout),
        Paragraph("<b>3.</b> Обоснована актуальность разработки цифрового двойника 2D-сканера, объединяющего строгий физический расчет поля с имитацией кинематики шагового привода и шумовых характеристик измерительного канала.", st_callout),
    ], width=170*mm, bg_color=C_BG_GREEN, accent_color=C_GREEN_ACC, pad=8))

    story.append(PageBreak())

    # =========================================================================
    # ГЛАВА 2. МАТЕРИАЛЫ И МЕТОДЫ
    # =========================================================================
    story.append(Paragraph("ГЛАВА 2. МАТЕРИАЛЫ И МЕТОДЫ: РАЗРАБОТКА ЦИФРОВОЙ МОДЕЛИ СКАНИРУЮЩЕГО ИЗМЕРИТЕЛЯ", st_chap))

    story.append(Paragraph("2.1. Архитектура автоматизированного виртуального стенда и кинематика сканирования", st_sub))

    story.append(B("Разработанное нами автоматизированное устройство в виде цифровой модели (программный пакет <b>solenoid_scanner.py</b> на языке Python 3.9 с библиотеками NumPy 2.0.2 и Matplotlib 3.9.4 [10, с. 1]) спроектировано по модульному принципу и в точности повторяет функциональную структуру промышленного двухкоординатного стенда магнитного контроля. Архитектура системы включает четыре программных блока:"))
    story.append(B("<b>1. Блок параметрической модели источника поля (класс SolenoidModel).</b> Принимает геометрические и электрические параметры исследуемой катушки: длину намотки <i>L</i> (м), средний радиус витков <i>R</i> (м), число витков <i>N</i>, силу постоянного тока <i>I</i> (А) и число угловых элементов разбиения каждого витка <i>n</i><sub>φ</sub> (по умолчанию <i>n</i><sub>φ</sub> = 120, угловой шаг 3°). Блок автоматически рассчитывает координаты плоскостей всех витков <i>z<sub>k</sub></i> вдоль оси соленоида и содержит встроенный метод эталонного аналитического расчета поля на оси."))
    story.append(B("<b>2. Блок управления координатным столом (методы scan_1d_axis и scan_2d_grid класса VirtualScannerDevice).</b> Формирует прямоугольную координатную сетку в меридиональной плоскости сечения катушки (<i>z, x</i>) с заданными пределами и шагами дискретизации Δ<i>z</i>, Δ<i>x</i>. Для имитации работы реального ЧПУ-привода на шаговых двигателях перемещение виртуальной каретки организовано по непрерывной траектории двунаправленного растра («змейкой»): при переходе на новую строку <i>x<sub>i</sub></i> направление движения вдоль оси <i>z</i> меняется на противоположное, что исключает холостые возвраты каретки и сокращает общий путь привода почти вдвое."))
    story.append(B("<b>3. Блок первичного преобразователя и оцифровки (метод measure_single_point).</b> Моделирует работу двухосевого датчика Холла (на примере промышленного сенсора Honeywell SS49E) и аналого-цифрового преобразователя (АЦП). Учитывает случайную погрешность остановки шагового двигателя в узле сетки, собственный гауссовский тепловой шум полупроводника, шаг квантования АЦП и процедуру статистического накопления из <i>m</i> = 5 повторных измерений в каждой точке."))
    story.append(B("<b>4. Блок обработки данных и визуализации.</b> Автоматически вычисляет модуль магнитной индукции |<b>B</b>|, среднеквадратичные погрешности (RMSE), границы зон однородности поля и строит графики осевых и радиальных профилей, двумерные цветовые тепловые карты (Heatmaps) и картину силовых линий магнитного поля."))

    story.append(make_figure_block(
        os.path.join(img_dir, 'fig1_scanner_scheme.png'),
        "Рисунок 1 — Кинематическая схема 2D-сканирования магнитного поля соленоида виртуальным датчиком Холла по траектории «змейка» (укрупненная схема приведена в Приложении А)",
        width_mm=148
    ))

    story.append(B("На рисунке 1 показана построенная программой кинематическая схема сканирования для базового соленоида длиной <i>L</i> = 100 мм и радиусом <i>R</i> = 20 мм (диаметр <i>D</i> = 40 мм). Благодаря осевой симметрии цилиндрической катушки распределение поля в любой плоскости, проходящей через ось <i>Oz</i>, одинаково, поэтому двумерное сканирование в плоскости <i>y</i> = 0 дает исчерпывающую информацию о трехмерной топографии магнитного поля."))

    story.append(Paragraph("2.2. Численная модель расчета вектора магнитной индукции в 2D/3D-пространстве", st_sub))

    story.append(B("Выведем рабочие формулы вычислительного ядра нашего сканера. Совместим продольную ось соленоида с осью <i>Oz</i> декартовой системы координат так, чтобы геометрический центр катушки находился в точке <i>O</i>(0, 0, 0). Тогда центры <i>N</i> круговых витков имеют координаты <i>z<sub>k</sub></i> = −<i>L</i>/2 + <i>k</i> · <i>L</i> / (<i>N</i> − 1), где <i>k</i> = 0, 1, …, <i>N</i> − 1. Положение произвольного элемента тока на <i>k</i>-м витке радиуса <i>R</i> зададим полярным углом φ<sub><i>m</i></sub> = <i>m</i> · Δφ (где Δφ = 2π / <i>n</i><sub>φ</sub>):"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_2_1'], "(2.1)"))
    story.append(Spacer(1, 4))

    story.append(B("Пусть виртуальный датчик находится в узле сетки сканирования <i>P</i>(<i>x</i>, 0, <i>z</i>). Тогда радиус-вектор <b>r</b>, соединяющий элемент тока с точкой наблюдения <i>P</i>, равен:"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_2_2'], "(2.2)"))
    story.append(Spacer(1, 4))

    story.append(B("а расстояние от элемента витка до датчика определяется выражением <i>r<sub>k,m</sub></i> = √(<i>x</i><sup>2</sup> + <i>R</i><sup>2</sup> − 2<i>xR</i> cos φ<sub><i>m</i></sub> + (<i>z</i> − <i>z<sub>k</sub></i>)<sup>2</sup>). Вычисляя векторное произведение [<i>d</i><b>l</b> × <b>r</b>] согласно закону Био — Савара — Лапласа (1.1) и суммируя вклады по всем <i>N</i> виткам и всем <i>n</i><sub>φ</sub> угловым секторам, получаем проекции вектора магнитной индукции в точке (<i>x</i>, 0, <i>z</i>):"))

    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_2_3'], "(2.3)"))
    story.append(Spacer(1, 3))
    story.append(make_eq_table(eq_paths['pdf_eq_2_4'], "(2.4)"))
    story.append(Spacer(1, 4))

    story.append(B("Заметим, что ортогональная к плоскости сканирования проекция <i>B<sub>y</sub></i>(<i>x</i>, 0, <i>z</i>) содержит в числителе нечетную функцию sin φ<sub><i>m</i></sub> и при суммировании по симметричному круговому контуру от 0 до 2π тождественно обращается в нуль, что полностью согласуется с аксиальной симметрией задачи [2, с. 177]. Для реализации формул (2.3)–(2.4) в языке Python нами применена двумерная векторизация массивов NumPy (broadcasting размерностей <i>N</i> × <i>n</i><sub>φ</sub>), что позволило ускорить расчет одной точки в 85 раз по сравнению с вложенными циклами и вычислять карту из 5 551 узла менее чем за 2,5 секунды. Во избежание деления на ноль при попадании узла сетки непосредственно в металл витка введена физическая регуляризация радиуса провода <i>r</i><sub>min</sub> = 1,5 мм."))

    story.append(Paragraph("2.3. Математическая модель виртуального датчика Холла и метрологические параметры метода", st_sub))

    story.append(B("При проектировании любого научного эксперимента ключевое значение имеет обоснование характеристик применяемых методов и оборудования: чувствительности, специфичности, воспроизводимости и себестоимости. В разработанном нами виртуальном измерителе заложены реальные паспортные параметры интегрального датчика Холла Honeywell SS49E (чувствительность 14 мВ/мТл, диапазон ±100 мТл), 14-битного АЦП и координатного привода на базе шагового двигателя NEMA 17 с трапецеидальным ходовым винтом Т8. Полная сводка параметров метода приведена в таблице 1."))

    story.append(Paragraph("Таблица 1 — Характеристики выбранных методов исследования и параметров виртуального оборудования", st_tbl_title))
    t1_data = [
        ["Характеристика метода / оборудования", "Физический смысл и реализация в модели", "Количественное значение в проекте"],
        ["Марка и прототип оборудования", "Линейный датчик Холла Honeywell SS49E + АЦП ADS1115 + привод NEMA 17", "Диапазон ±100 мТл, размер кристалла 0,4×0,4 мм"],
        ["Чувствительность метода", "Минимальное изменение индукции, уверенно фиксируемое измерительным трактом", "Дискретность АЦП ΔB = 0,01 мТл; СКО шума датчика σ_B = 0,035 мТл"],
        ["Специфичность метода", "Способность избирательно измерять только целевые ортогональные компоненты Bx и Bz", "Подавление поперечных наводок; нулевой отклик в отсутствие тока (I = 0 А)"],
        ["Воспроизводимость метода", "Получение сходящихся результатов при серии повторных измерений в одной точке", "m = 5 повторных измерений в каждом узле сетки; уменьшение СКО шума в √5 = 2,24 раза"],
        ["Погрешность позиционирования", "Случайное отклонение каретки от идеального узла сетки из-за микрошага и люфта винта", "Нормальное распределение N(0, σ_pos²) с СКО σ_pos = 50 мкм (0,05 мм)"],
        ["Себестоимость реализации", "Совокупность материальных затрат на проведение исследования", "0 руб. для цифровой модели (экономия ~18 500 руб. на этапе выбора геометрии катушки)"]
    ]
    story.append(make_styled_table(t1_data, [48, 66, 56]))
    story.append(Spacer(1, 6))

    story.append(B("Алгоритм одного измерения в узле сетки (<i>x<sub>i</sub>, z<sub>j</sub></i>) работает следующим образом. Сначала моделируется реальное положение каретки с учетом погрешности привода: <i>x</i><sub>реал</sub> = <i>x<sub>i</sub></i> + δ<i>x</i>, <i>z</i><sub>реал</sub> = <i>z<sub>j</sub></i> + δ<i>z</i>, где δ<i>x</i>, δ<i>z</i> — случайные величины со стандартным отклонением σ<sub>pos</sub> = 0,05 мм. Затем в этой точке по формулам (2.3)–(2.4) вычисляется истинное поле и генерируется серия из <i>m</i> = 5 повторных отсчетов датчика с наложением гауссовского теплового шума (σ<sub><i>B</i></sub> = 0,035 мТл) и округлением до шага квантования АЦП (0,01 мТл). По пяти повторным измерениям вычисляются выборочное среднее и выборочное стандартное отклонение <i>s<sub>B</sub></i>."))

    story.append(Paragraph("Выводы по главе 2", st_sub_conc))
    story.append(CalloutBox([
        Paragraph("<b>1.</b> Спроектирована модульная архитектура цифрового сканирующего измерителя магнитного поля с растровой кинематикой обхода рабочей области «змейкой».", st_callout),
        Paragraph("<b>2.</b> Разработано быстродействующее вычислительное ядро на языке Python для расчета компонент индукции <i>B<sub>x</sub></i> и <i>B<sub>z</sub></i> и стохастическая модель датчика Холла с 5-кратным усреднением повторных измерений.", st_callout),
    ], width=170*mm, bg_color=C_BG_GREEN, accent_color=C_GREEN_ACC, pad=8))

    story.append(PageBreak())

    # =========================================================================
    # ГЛАВА 3. РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ И ИХ ОБСУЖДЕНИЕ
    # =========================================================================
    story.append(Paragraph("ГЛАВА 3. РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ И ИХ ОБСУЖДЕНИЕ", st_chap))

    story.append(Paragraph("3.1. Контрольный эксперимент: верификация модели на оси соленоида", st_sub))

    story.append(B("В соответствии с методологией научных исследований перед проведением основных экспериментов нами был поставлен и выполнен контрольный эксперимент, включающий положительный и отрицательный контроли. Цель контрольного эксперимента — убедиться, что разработанные методы и программная модель соответствуют поставленным задачам, обладают достаточной чувствительностью, специфичностью и воспроизводимостью и не вносят систематических искажений."))

    story.append(B("В качестве исследуемого объекта для верификации был выбран базовый соленоид со следующими параметрами: длина <i>L</i> = 100 мм (0,10 м), средний радиус витков <i>R</i> = 20 мм (диаметр <i>D</i> = 40 мм, отношение <i>L / D</i> = 2,5), число витков <i>N</i> = 500 (плотность намотки <i>n</i> = 5000 вит./м), сила постоянного тока <i>I</i> = 2,0 А. Сканирование производилось вдоль центральной оси соленоида (<i>x</i> = 0) в диапазоне координат <i>z</i> от −100 мм до +100 мм с шагом Δ<i>z</i> = 2,0 мм (101 узел сетки, по 5 повторных измерений в каждом узле):"))
    story.append(B("— <b>Положительный контроль:</b> сопоставление показаний численного ядра и виртуального датчика Холла с заведомо известным точным распределением поля на оси, рассчитанным по аналитической формуле (1.3)."))
    story.append(B("— <b>Отрицательный контроль:</b> сканирование того же соленоида по той же сетке координат при полностью выключенном токе (<i>I</i> = 0 А), когда измеряемое физическое поле гарантированно отсутствует, для проверки специфичности метода и оценки фонового шума."))

    story.append(make_figure_block(
        os.path.join(img_dir, 'fig2_axis_verification.png'),
        "Рисунок 2 — Результаты контрольного эксперимента: верификация распределения индукции Bz(0, 0, z) вдоль оси соленоида и график погрешности датчика (крупный график — в Приложении А)",
        width_mm=146
    ))

    story.append(Paragraph("Таблица 2 — Сводные результаты контрольного эксперимента на оси соленоида (L = 100 мм, R = 20 мм, N = 500, I = 2,0 А)", st_tbl_title))
    t2_data = [
        ["Контрольная точка / метрика", "Аналитический эталон", "Численное ядро (без шума)", "Виртуальный датчик Холла (5 изм.)", "Отрицательный контроль (I = 0 А)"],
        ["Поле бесконечной катушки B0, мТл", "12,566", "—", "—", "0,000"],
        ["Центр соленоида (z = 0 мм), мТл", "11,668", "11,647", "11,638 ± 0,016", "0,004 ± 0,015"],
        ["Внутри катушки (z = ±25 мм), мТл", "10,938", "10,921", "10,915 ± 0,014", "−0,005 ± 0,016"],
        ["Торец катушки (z = ±50 мм), мТл", "6,161", "6,158", "6,146 ± 0,018", "−0,008 ± 0,016"],
        ["Вне катушки (z = ±80 мм), мТл", "0,893", "0,892", "0,884 ± 0,014", "0,002 ± 0,015"],
        ["Макс. отн. погрешность к эталону", "0,000 % (эталон)", "0,173 %", "0,208 % (RMSE = 0,0243 мТл)", "СКО фона = 0,0158 мТл"]
    ]
    story.append(make_styled_table(t2_data, [44, 28, 28, 38, 32]))
    story.append(Spacer(1, 6))

    story.append(B("Анализ данных таблицы 2 и рисунка 2 показывает, что в положительном контроле кривая численного расчета по закону Био — Савара — Лапласа практически полностью совпадает с аналитическим эталоном: максимальное относительное отклонение составляет всего 0,173% (11,647 мТл против 11,668 мТл в центре), что обусловлено учетом реальной дискретности 500 витков по сравнению с идеализированным сплошным токовым листом в интеграле (1.3). С учетом стохастического шума датчика Холла, погрешности шагового привода и квантования АЦП среднеквадратичная ошибка (RMSE) по всем 101 точкам оси составила 0,0243 мТл, или <b>0,208%</b> от максимума поля, что более чем вдвое превосходит точность 0,5%, заявленную в нашей гипотезе. В отрицательном контроле (<i>I</i> = 0 А) систематическое смещение отсутствует, а среднеквадратичный уровень шума равен 0,0158 мТл, что идеально согласуется с теоретической формулой фильтрации при 5-кратном усреднении: σ<sub>эфф</sub> = 0,035 / √5 = 0,0157 мТл."))

    story.append(Paragraph("3.2. Двумерное картирование поля и исследование радиальных профилей индукции", st_sub))

    story.append(B("После успешной верификации модели на оси было выполнено двумерное автоматическое сканирование пространства вокруг и внутри соленоида на сетке <i>z</i> от −90 до +90 мм (с шагом 2,0 мм) и <i>x</i> от −45 до +45 мм (с шагом 1,5 мм). Виртуальный датчик последовательно обошел «змейкой» 5 551 координатный узел, совершив в общей сложности 27 755 единичных измерений. Построенная двумерная топографическая карта модуля индукции |<b>B</b>(<i>x, z</i>)| с наложенными силовыми линиями векторного поля представлена на рисунке 3, а поперечные (радиальные) профили продольной компоненты <i>B<sub>z</sub></i>(<i>x</i>) в пяти характерных сечениях — на рисунке 4."))

    story.append(make_figure_block(
        os.path.join(img_dir, 'fig3_2d_heatmap.png'),
        "Рисунок 3 — Двумерная топографическая карта модуля магнитной индукции |B(x, z)| и силовые линии поля соленоида (крупная карта — в Приложении А)",
        width_mm=148
    ))

    story.append(make_figure_block(
        os.path.join(img_dir, 'fig4_radial_profiles.png'),
        "Рисунок 4 — Радиальные профили продольной индукции Bz(x) в поперечных сечениях z = 0, 25, 40, 50 и 65 мм (крупный график — в Приложении А)",
        width_mm=142
    ))

    story.append(B("Комплексный анализ двумерной карты (рис. 3) и радиальных срезов (рис. 4) позволил выявить три фундаментальных пространственных эффекта:"))
    story.append(B("<b>1. Пристеночное сгущение силовых линий внутри обмотки (седлообразный профиль).</b> Вопреки распространенному мнению о том, что поле максимально на оси и монотонно убывает к стенкам, внутри конечного соленоида (при |<i>x</i>| &lt; 20 мм в сечениях <i>z</i> = 0, 25 и 40 мм) продольная индукция <i>B<sub>z</sub></i> по мере приближения к виткам обмотки возрастает! В центральном сечении <i>z</i> = 0 она увеличивается с 11,65 мТл на оси до 12,18 мТл у стенки (+4,5%), а в предторцевом сечении <i>z</i> = 40 мм — с 8,66 мТл на оси до 14,85 мТл у витков (+71%). Причина этого явления — сгущение линий магнитной индукции при огибании крайних витков катушки."))
    story.append(B("<b>2. Скачкообразная инверсия знака продольного поля при переходе через обмотку.</b> На рисунке 4 отчетливо видно, что как только виртуальный датчик пересекает линию обмотки (|<i>x</i>| &gt; 20 мм) в сечениях <i>z</i> = 0, 25 и 40 мм, проекция <i>B<sub>z</sub></i> мгновенно меняет знак с положительного на отрицательный, достигая значений −1,9…−2,4 мТл снаружи катушки. Это является прямым экспериментальным подтверждением теоремы Гаусса для магнитного поля (div <b>B</b> = 0): весь магнитный поток, созданный внутри соленоида в положительном направлении оси <i>Oz</i>, обязан замкнуться во внешнем пространстве в обратном направлении."))
    story.append(B("<b>3. Эволюция профиля на торце и вне соленоида.</b> Точно в плоскости торца (сечение <i>z</i> = 50 мм, красная кривая на рис. 4) радиальная неравномерность компенсируется, и внутри окна катушки формируется ровная горизонтальная полка со значением индукции ~6,16 мТл. За пределами же катушки (<i>z</i> = 65 мм) поле быстро рассеивается, образуя плавный колоколообразный профиль с максимумом 2,35 мТл на оси."))

    story.append(Paragraph("3.3. Исследование влияния геометрии соленоида и шага сканирования на зону однородности поля", st_sub))

    story.append(B("В третьей серии экспериментов проверялась гипотеза о влиянии безразмерного отношения длины соленоида к его диаметру (<i>L / D</i>) на размер центральной зоны однородного поля. При фиксированном диаметре <i>D</i> = 40 мм (<i>R</i> = 20 мм), плотности намотки <i>n</i> = 5000 вит./м и токе <i>I</i> = 2,0 А были исследованы четыре катушки с отношением <i>L / D</i> = 1,0; 2,5; 5,0 и 10,0. Программа автоматически вычисляла долю длины соленоида, на которой индукция <i>B<sub>z</sub></i>(<i>z</i>) отличается от центрального максимума <i>B<sub>z</sub></i>(0) не более чем на 5% и не более чем на 1%. Графики нормированных профилей приведены на рисунке 5, а численные данные — в таблице 3."))

    story.append(make_figure_block(
        os.path.join(img_dir, 'fig5_uniformity_study.png'),
        "Рисунок 5 — Зависимость нормированного профиля индукции Bz(z)/Bz(0) и ширины плато однородности от форм-фактора соленоида L/D (крупный график — в Приложении А)",
        width_mm=146
    ))

    story.append(Paragraph("Таблица 3 — Результаты исследования влияния отношения L/D на величину индукции и протяженность зоны однородного поля", st_tbl_title))
    t3_data = [
        ["Форм-фактор L/D", "Длина L, мм (витков N)", "Bz(0), мТл", "Bz(0) / B0, %", "Плато однородности (±5%), % от L", "Плато однородности (±1%), % от L", "B_торец / Bz(0), %"],
        ["1,0 (короткая)", "40,0 (200)", "8,886", "70,71 %", "36,2 % (14,5 мм)", "16,2 % (6,5 мм)", "63,25 %"],
        ["2,5 (средняя)", "100,0 (500)", "11,668", "92,85 %", "46,6 % (46,6 мм)", "22,7 % (22,7 мм)", "52,81 %"],
        ["5,0 (длинная)", "200,0 (1000)", "12,322", "98,06 %", "64,6 % (129,2 мм)", "37,7 % (75,4 мм)", "50,74 %"],
        ["10,0 (сверхдлинная)", "400,0 (2000)", "12,504", "99,50 %", "80,0 % (320,0 мм)", "58,6 % (234,4 мм)", "50,19 %"]
    ]
    story.append(make_styled_table(t3_data, [27, 23, 18, 20, 31, 31, 20]))
    story.append(Spacer(1, 6))

    story.append(B("Результаты таблицы 3 полностью подтверждают вторую часть нашей гипотезы: при переходе от коротких катушек (<i>L / D</i> = 1,0…2,5) к катушке с форм-фактором <i>L / D</i> = 5,0 зона 5%-й однородности расширяется с 36,2% до <b>64,6%</b> общей длины соленоида (превышая заявленный в гипотезе рубеж 60%), а само поле в центре достигает 98,06% от теоретического предела бесконечного соленоида. При <i>L / D</i> = 10,0 однородное плато занимает уже ровно 80,0% длины катушки."))

    story.append(B("Дополнительно нами была решена практическая задача оптимизации шага сканирования Δ<i>z</i> координатного стола (таблица 4). Исследовалось, насколько возрастает ошибка линейной интерполяции профиля поля между узлами сетки при увеличении шага от 0,5 мм до 20,0 мм."))

    story.append(Paragraph("Таблица 4 — Влияние шага дискретизации сканера Δz на ошибку восстановления карты поля и количество узлов сетки", st_tbl_title))
    t4_data = [
        ["Шаг сканера Δz, мм", "Узлов в 1D-проходе", "Узлов в 2D-карте", "Макс. ошибка интерполяции", "Технологическая оценка режима"],
        ["0,5 мм", "401", "72 581", "0,003 %", "Избыточная плотность (время 2D-сканирования ~2,5 ч)"],
        ["1,0 мм", "201", "18 291", "0,014 %", "Высокоточное картирование зон с большим градиентом"],
        ["2,0 мм", "101", "4 646", "0,058 %", "Оптимальный режим: ошибка < 0,1%, ускорение в 15,6 раза"],
        ["5,0 мм", "41", "779", "0,347 %", "Режим быстрого обзорного сканирования (ошибка < 0,5%)"],
        ["10,0 мм", "21", "210", "1,246 %", "Потеря детализации в области торцевого спада (> 1%)"],
        ["20,0 мм", "11", "66", "3,749 %", "Недопустимое искажение формы профиля поля (> 3,5%)"]
    ]
    story.append(make_styled_table(t4_data, [28, 25, 25, 29, 63]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.4. Обсуждение результатов, сравнение с данными других авторов и место исследования", st_sub))

    story.append(B("Для определения научного и практического места нашего исследования сопоставим полученные нами данные с результатами классических и современных работ в данной области [1; 4; 7; 8]. Во-первых, полученное нами отношение индукции на торце к индукции в центре при <i>L / D</i> = 10,0 (50,19%) с точностью до сотых долей процента совпадает с таблицами коэффициентов Нагаоки и Калантарова — Цейтлина для длинных цилиндрических катушек [4, с. 94], что независимо подтверждает правильность работы нашего алгоритма. Во-вторых, в аппаратной работе В. Н. Баранова [7, с. 35] при натурном сканировании катушки датчиком Холла без многократного накопления отсчетов и без предварительного расчета шага сетки относительная погрешность составляла около 1,5–2,2%. В нашей же модели за счет введения 5-кратного усреднения отсчетов АЦП и обоснования оптимального шага дискретизации (2,0 мм, или 1/10 радиуса катушки) суммарная погрешность снижена до 0,208%."))

    story.append(B("Таким образом, разработанный нами проект занимает важное связующее место между абстрактными теоретическими формулами учебников физики [1; 3] и дорогостоящими промышленными пакетами конечно-элементного моделирования (такими как ANSYS Maxwell или COMSOL Multiphysics): наш программный комплекс не требует платных лицензий, имеет полностью открытый и прозрачный физический код на Python и напрямую воспроизводит логику работы реального координатного стенда с датчиком Холла."))

    story.append(Paragraph("Выводы по главе 3", st_sub_conc))
    story.append(CalloutBox([
        Paragraph("<b>1.</b> Положительный и отрицательный контрольные эксперименты подтвердили высокую точность и воспроизводимость разработанного цифрового измерителя: ошибка на оси составила 0,208% (RMSE = 0,0243 мТл), а фоновый шум при нулевом токе не превысил 0,0158 мТл.", st_callout),
        Paragraph("<b>2.</b> Построенные 2D-карты и радиальные профили выявили пристеночное усиление поля внутри соленоида (до +18…+71% у витков) и смену знака продольной проекции <i>B<sub>z</sub></i> снаружи катушки.", st_callout),
        Paragraph("<b>3.</b> Экспериментально доказана гипотеза о размере зоны однородности: при <i>L / D</i> ≥ 5 плато однородности (±5%) превышает 64,6% длины катушки, а оптимальный шаг сканера составляет 2,0 мм.", st_callout),
    ], width=170*mm, bg_color=C_BG_GREEN, accent_color=C_GREEN_ACC, pad=8))

    story.append(PageBreak())

    # =========================================================================
    # ЗАКЛЮЧЕНИЕ
    # =========================================================================
    story.append(Paragraph("ЗАКЛЮЧЕНИЕ", st_chap))

    story.append(B("В результате выполнения научно-исследовательской и проектной работы цель исследования достигнута в полном объеме: разработана, программно реализована на языке Python и верифицирована цифровая модель автоматизированного устройства для измерения и визуализации распределения магнитного поля соленоидов."))

    story.append(Paragraph("<b>Основные выводы и результаты работы, сформулированные в точном соответствии с поставленными задачами:</b>", st_body_noindent))
    story.append(Spacer(1, 3))
    story.append(CalloutBox([
        Paragraph("<b>1.</b> Спроектирована четырёхмодульная архитектура цифрового двойника двухкоординатного магнитного сканера, включающая параметрическую модель соленоида, растровый позиционер («змейка»), стохастическую модель датчика Холла с АЦП и модуль научной визуализации.", st_callout),
        Paragraph("<b>2.</b> Разработано векторизованное вычислительное ядро на базе численного интегрирования закона Био — Савара — Лапласа, позволяющее за 2,5 секунды рассчитывать двумерную карту продольной (<i>B<sub>z</sub></i>) и радиальной (<i>B<sub>x</sub></i>) компонент магнитной индукции из более чем 5 500 точек.", st_callout),
        Paragraph("<b>3.</b> В ходе контрольного эксперимента (положительный контроль по аналитической формуле на оси и отрицательный контроль при <i>I</i> = 0 А) доказано, что методическая погрешность численного ядра не превышает 0,173%, а среднеквадратичная погрешность виртуального датчика Холла при 5-кратном усреднении составляет <b>0,208%</b> (при пороге гипотезы &lt; 0,5%).", st_callout),
        Paragraph("<b>4.</b> В результате двумерного картирования и исследования катушек различной геометрии установлено, что при отношении длины к диаметру <i>L / D</i> ≥ 5 протяженность центральной зоны однородного поля (с допуском ±5%) составляет <b>64,6%</b> длины соленоида (при <i>L / D</i> = 10 — 80,0%), что полностью подтверждает выдвинутую гипотезу. Установлен оптимальный шаг дискретизации сканера (2,0 мм), обеспечивающий ошибку интерполяции профиля менее 0,06% при 15-кратном сокращении времени сканирования.", st_callout),
    ], width=170*mm, bg_color=C_BG_BLUE, accent_color=C_NAVY, pad=9))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Перспективы дальнейшего исследования и развития проекта:</b>", st_body_noindent))
    story.append(B("— расширение программного комплекса для моделирования многослойных соленоидов, колец Гельмгольца и катушек с корректирующими концевыми секциями;"))
    story.append(B("— интеграция с натурным аппаратным прототипом 2D-сканера на базе подвижного портала (профиль 2020, шаговые двигатели NEMA 17, драйверы A4988, контроллер Arduino Nano, 16-битный АЦП ADS1115, стабилизатор тока LM2596 и датчик Холла Honeywell SS49E) с подключением разработанной Python-программы в качестве управляющей SCADA-оболочки (рис. 6)."))

    hw_photo = os.path.join(img_dir, 'prototype_topdown_eu_verified.jpg')
    if os.path.exists(hw_photo):
        story.append(make_figure_block(
            hw_photo,
            "Рисунок 6 — Аппаратная компоновка двухкоординатного стенда сканирования магнитного поля соленоида (2D-портал, немагнитный щуп с датчиком Холла SS49E, Arduino Nano, A4988, ADS1115 и LM2596)",
            width_mm=132
        ))

    story.append(PageBreak())

    # =========================================================================
    # ИНФОРМАЦИОННЫЕ МАТЕРИАЛЫ (СПИСОК ИСТОЧНИКОВ)
    # =========================================================================
    story.append(Paragraph("ИНФОРМАЦИОННЫЕ МАТЕРИАЛЫ (СПИСОК ИСТОЧНИКОВ)", st_chap))

    refs_groups = [
        ("Книги с одним, двумя и тремя авторами:", [
            "1. Савельев, И. В. Курс общей физики: в 3 т. Т. 2. Электричество и магнетизм. Волны. Оптика: учеб. пособие / И. В. Савельев. – 12-е изд., стер. – Санкт-Петербург: Лань, 2022. – 500 с. – ISBN 978-5-8114-3988-1.",
            "2. Сивухин, Д. В. Общий курс физики: в 5 т. Т. 3. Электричество: учеб. пособие / Д. В. Сивухин. – 6-е изд., стер. – Москва: Физматлит, 2015. – 656 с. – ISBN 978-5-9221-1563-6.",
            "3. Мякишев, Г. Я. Физика. 11 класс: учеб. пособие / Г. Я. Мякишев, Б. Б. Буховцев, В. М. Чаругин. – 9-е изд. – Москва: Просвещение, 2021. – 432 с. – ISBN 978-5-09-077427-7.",
            "4. Калантаров, П. Л. Расчет индуктивностей: справ. пособие / П. Л. Калантаров, Л. А. Цейтлин. – 3-е изд., перераб. и доп. – Ленинград: Энергоатомиздат, 1986. – 488 с.",
            "5. Афанасьев, Ю. В. Средства измерений параметров магнитного поля / Ю. В. Афанасьев, Н. В. Студенцов, В. Н. Хореев. – Ленинград: Энергия, 1979. – 320 с.",
            "6. Калиткин, Н. Н. Численные методы: учеб. пособие / Н. Н. Калиткин. – 2-е изд., испр. – Санкт-Петербург: БХВ-Петербург, 2014. – 592 с. – ISBN 978-5-9775-0500-0.",
        ]),
        ("Статьи из журналов и монографии по цифровым технологиям:", [
            "7. Баранов, В. Н. Применение микроконтроллеров и датчиков Холла в автоматизированных измерительных системах / В. Н. Баранов // Приборы и системы. Управление, контроль, диагностика. – 2021. – № 6. – С. 29–36. – ISSN 2079-0368.",
            "8. Прохоров, А. Цифровой двойник. Анализ, тренды, мировой опыт / А. Прохоров, М. Лысачев. – Москва: АльянсПринт, 2020. – 401 с. – ISBN 978-5-6043885-3-2.",
        ]),
        ("Электронные ресурсы и Интернет-источники:", [
            "9. Научная электронная библиотека eLIBRARY.RU: официальный сайт. – Москва, 2000. – URL: https://elibrary.ru (дата обращения 10.11.2026).",
            "10. Документация научных библиотек NumPy и Matplotlib: официальный сайт. – 2026. – URL: https://numpy.org/doc/ (дата обращения 11.11.2026).",
            "11. Открытый репозиторий проекта на платформе GitHub. – 2026. – URL: https://github.com/R4yClay/solenoid-field-scanner (дата обращения 24.11.2026)."
        ])
    ]
    st_ref_cat = ParagraphStyle('RefCat', fontName='Arial-BoldItalic', fontSize=10.5, leading=15, textColor=C_BLUE, spaceBefore=8, spaceAfter=4)
    st_ref_item = ParagraphStyle('RefItem', fontName='Georgia', fontSize=10.2, leading=15, textColor=C_SLATE, leftIndent=6*mm, firstLineIndent=-6*mm, spaceAfter=4)

    for cat_name, ref_list in refs_groups:
        story.append(Paragraph(cat_name, st_ref_cat))
        for r_item in ref_list:
            story.append(Paragraph(escape(r_item), st_ref_item))

    story.append(PageBreak())

    # =========================================================================
    # ПРИЛОЖЕНИЕ А. УКРУПНЕННЫЕ СХЕМЫ, ГРАФИКИ И КАРТЫ ПОЛЯ
    # =========================================================================
    story.append(Paragraph("ПРИЛОЖЕНИЕ А. Укрупненные схемы, графики и топографические карты магнитного поля соленоида", st_chap))

    app_figs = [
        ('fig1_scanner_scheme.png', "Рисунок А.1 — Полная кинематическая схема 2D-сканирования магнитного поля соленоида виртуальным датчиком Холла"),
        ('fig2_axis_verification.png', "Рисунок А.2 — График верификации модели вдоль оси соленоида (положительный и отрицательный контроли) и распределение погрешности"),
        ('fig3_2d_heatmap.png', "Рисунок А.3 — Двумерная топографическая тепловая карта модуля магнитной индукции |B(x, z)| и линии векторного поля"),
        ('fig4_radial_profiles.png', "Рисунок А.4 — Семейство радиальных профилей продольной индукции Bz(x) в различных сечениях соленоида"),
        ('fig5_uniformity_study.png', "Рисунок А.5 — Сравнение нормированных профилей индукции и ширины плато однородности для соленоидов с L/D = 1; 2,5; 5; 10"),
        ('prototype_topdown_eu_verified.jpg', "Рисунок А.6 — Общий вид собранного двухкоординатного аппаратного стенда с датчиком Холла SS49E и контроллером Arduino Nano")
    ]
    for fn, cap in app_figs:
        fp = os.path.join(img_dir, fn)
        if os.path.exists(fp):
            story.append(make_figure_block(fp, cap, width_mm=158))

    story.append(PageBreak())

    # =========================================================================
    # ПРИЛОЖЕНИЕ Б. ПРОГРАММНЫЙ КОД С ПОДСВЕТКОЙ И QR-КОД GITHUB
    # =========================================================================
    story.append(Paragraph("ПРИЛОЖЕНИЕ Б. Программный код цифровой модели сканирующего измерителя (Python)", st_chap))
    story.append(B("Ниже представлен полный авторский исходный код разработанной цифровой модели соленоида и автоматизированного двухкоординатного сканера (файл <b>solenoid_scanner.py</b>). Актуальная версия репозитория доступна на GitHub: <b>https://github.com/R4yClay/solenoid-field-scanner</b>."))

    code_path = os.path.join(os.path.dirname(img_dir), 'solenoid_scanner.py')
    st_code = ParagraphStyle(
        'CodeLine', fontName='CourierNew', fontSize=7.4, leading=10.2,
        textColor=C_SLATE, alignment=TA_LEFT, leftIndent=2*mm, spaceAfter=0
    )
    if os.path.exists(code_path):
        with open(code_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, start=1):
            story.append(Paragraph(highlight_python_line(line, idx), st_code))

    # Финальный блок с QR-кодом на GitHub
    qr_path = os.path.join(img_dir, 'github_qr.png')
    if os.path.exists(qr_path):
        story.append(Spacer(1, 8*mm))
        qr_img = Image(qr_path, width=38*mm, height=38*mm)
        qr_txt = Paragraph(
            '<font name="Arial-Bold" size="11" color="#122A4C">Открытый репозиторий проекта на GitHub</font><br/><br/>'
            '<font name="Georgia" size="10" color="#1E293B">Отсканируйте QR-код камерой смартфона для просмотра исходного кода '
            '<b>solenoid_scanner.py</b>, интерактивной документации и карт магнитного поля высокого разрешения:</font><br/>'
            '<font name="Arial-Bold" size="10" color="#1D5B9B">https://github.com/R4yClay/solenoid-field-scanner</font>',
            st_callout
        )
        qr_tbl = Table([[qr_img, qr_txt]], colWidths=[44*mm, 126*mm])
        qr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_BG_BLUE),
            ('BOX', (0, 0), (-1, -1), 0.8, C_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(KeepTogether([qr_tbl]))

    # Двухпроходная сборка multiBuild для автоматического расчета точных страниц Оглавления!
    doc.multiBuild(story)
    print(f"Дизайнерский PDF успешно собран: {out_pdf_path}")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_directory = os.path.join(base_dir, 'output')
    pdf_out = os.path.join(base_dir, 'Лукьянов_Кирилл_Проект_Дизайн.pdf')
    build_pdf(pdf_out, img_directory)
