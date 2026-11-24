#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор профессиональной конкурсной презентации PowerPoint (.pptx)
с высокочеткими математическими формулами (LaTeX/MathText 300 DPI)
и типографской математической нотацией на всех слайдах.
Автор: Лукьянов Кирилл Алексеевич (МОУ “Сланцевская СОШ №1”, 10 класс).
Научный руководитель: Заборская Ольга Владимировна, учитель физики.
"""

import os
import shutil
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Настройка математического шрифта STIX (выглядит как классический LaTeX Times/Computer Modern)
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.family'] = 'STIXGeneral'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# Цветовая палитра
NAVY = RGBColor(18, 42, 76)
BLUE = RGBColor(31, 119, 180)
TEAL = RGBColor(22, 130, 120)
ORANGE = RGBColor(214, 85, 30)
GREEN = RGBColor(34, 139, 68)
BG_LIGHT = RGBColor(246, 248, 252)
CARD_BORDER = RGBColor(205, 215, 230)
DARK_TEXT = RGBColor(30, 35, 45)
GRAY_TEXT = RGBColor(100, 110, 125)
WHITE = RGBColor(255, 255, 255)


def render_formula_png(latex_lines, out_path, fig_w=6.0, fig_h=1.5, fontsize=16, bg_hex='#EEF5FF', text_hex='#122A4C'):
    """
    Рендерит одну или несколько строк математических формул (MathText/LaTeX)
    в четкое изображение PNG (300 DPI) для вставки на слайд PowerPoint.
    """
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_facecolor(bg_hex)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor(bg_hex)

    n = len(latex_lines)
    for idx, (line_str, fsize, color_str) in enumerate(latex_lines):
        # Равномерное распределение по вертикали сверху вниз
        y_pos = 1.0 - (idx + 0.55) / (n + 0.1)
        ax.text(0.5, y_pos, line_str,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=fsize if fsize else fontsize,
                color=color_str if color_str else text_hex,
                transform=ax.transAxes)

    plt.savefig(out_path, dpi=300, facecolor=bg_hex, bbox_inches='tight', pad_inches=0.08)
    plt.close(fig)
    return out_path


def build_formula_images(img_dir):
    """Создает набор красивых математических формул для слайдов презентации."""
    os.makedirs(img_dir, exist_ok=True)
    formulas = {}

    # 1. Закон Био — Савара — Лапласа и квадрат расстояния r_{k,m}
    f1_path = os.path.join(img_dir, 'eq1_biot_savart.png')
    render_formula_png(
        [
            (r"$d\vec{B} = \frac{\mu_0}{4\pi} \cdot \frac{I \, \left[d\vec{l} \times \vec{r}\right]}{r^3}, \qquad \mu_0 = 4\pi \cdot 10^{-7}\ \mathrm{Гн/м}$", 16, '#122A4C'),
            (r"$r_{k,m} = \sqrt{x^2 + R^2 - 2xR\cos\varphi_m + (z - z_k)^2}$", 14.5, '#1F4E79')
        ],
        f1_path, fig_w=5.6, fig_h=1.45, bg_hex='#EBF3FF'
    )
    formulas['eq1'] = f1_path

    # 2. Рабочие формулы проекций Bx(x, 0, z) и Bz(x, 0, z) (численное интегрирование в плоскости y = 0)
    f2_path = os.path.join(img_dir, 'eq2_projections.png')
    render_formula_png(
        [
            (r"$B_x(x, 0, z) = \frac{\mu_0 I R \, \Delta\varphi}{4\pi} \sum_{k=1}^{N} \sum_{m=1}^{M} \frac{(z - z_k)\cos\varphi_m}{\left(x^2 + R^2 - 2xR\cos\varphi_m + (z - z_k)^2\right)^{3/2}}$", 13.5, '#122A4C'),
            (r"$B_z(x, 0, z) = \frac{\mu_0 I R \, \Delta\varphi}{4\pi} \sum_{k=1}^{N} \sum_{m=1}^{M} \frac{R - x\cos\varphi_m}{\left(x^2 + R^2 - 2xR\cos\varphi_m + (z - z_k)^2\right)^{3/2}}$", 13.5, '#122A4C'),
            (r"$|\vec{B}(x, 0, z)| = \sqrt{B_x^2(x, 0, z) + B_z^2(x, 0, z)}, \qquad B_y(x, 0, z) = 0$", 13.5, '#1F77B4')
        ],
        f2_path, fig_w=5.8, fig_h=2.2, bg_hex='#EBF3FF'
    )
    formulas['eq2'] = f2_path

    # 3. Аналитический эталон на оси соленоида Oz (x = 0, y = 0) (положительный контроль)
    f3_path = os.path.join(img_dir, 'eq3_analytical_axis.png')
    render_formula_png(
        [
            (r"$B_z(0, 0, z) = \frac{1}{2}\mu_0 n I \left( \frac{z + L/2}{\sqrt{R^2 + (z + L/2)^2}} - \frac{z - L/2}{\sqrt{R^2 + (z - L/2)^2}} \right)$", 14.0, '#8B2500'),
            (r"$B_x(0, 0, z) = 0, \quad B_y(0, 0, z) = 0, \quad B_z(0, 0, 0) = B_0 \frac{L/D}{\sqrt{1 + (L/D)^2}}$", 13.5, '#B23A00')
        ],
        f3_path, fig_w=5.8, fig_h=1.55, bg_hex='#FFF8EB'
    )
    formulas['eq3'] = f3_path

    # 4. Математическая модель измерительного канала (датчик Холла + АЦП + усреднение)
    f4_path = os.path.join(img_dir, 'eq4_sensor_model.png')
    render_formula_png(
        [
            (r"$B_{\mathrm{изм}}^{(q)}(x_i, z_j) = \Delta B_{\mathrm{АЦП}} \cdot \mathrm{Round}\!\left( \frac{B_{\mathrm{ист}}(x_i + \delta x,\, z_j + \delta z) + \xi_q}{\Delta B_{\mathrm{АЦП}}} \right), \quad \xi_q \sim \mathcal{N}(0, \sigma_{\mathrm{шум}}^2)$", 13.5, '#122A4C'),
            (r"$\overline{B}(x_i, z_j) = \frac{1}{m}\sum_{q=1}^{m} B_{\mathrm{изм}}^{(q)}, \qquad \sigma_{\overline{B}} = \frac{\sigma_{\mathrm{шум}}}{\sqrt{m}} = \frac{0{,}035}{\sqrt{5}} \approx 0{,}0157\ \mathrm{мТл}$", 14, '#1B612B')
        ],
        f4_path, fig_w=11.6, fig_h=1.35, bg_hex='#F6F8FC'
    )
    formulas['eq4'] = f4_path

    return formulas


def add_header_and_footer(slide, title_text, subtitle_text, slide_num, total_slides=13):
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY
    top_bar.line.fill.background()

    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.05), Inches(13.333), Inches(0.06))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = BLUE
    accent_bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.1), Inches(11.2), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = 'Arial'
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = 'Arial'
        p2.font.size = Pt(12)
        p2.font.color.rgb = RGBColor(190, 215, 245)

    footer_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.45), Inches(7.05), Inches(12.433), Inches(0.02))
    footer_line.fill.solid()
    footer_line.fill.fore_color.rgb = CARD_BORDER
    footer_line.line.fill.background()

    ft_left = slide.shapes.add_textbox(Inches(0.45), Inches(7.08), Inches(9.2), Inches(0.35))
    p_fl = ft_left.text_frame.paragraphs[0]
    p_fl.text = "Лукьянов Кирилл Алексеевич (МОУ “Сланцевская СОШ №1”) | Конкурс им. Д.И. Менделеева (2026)"
    p_fl.font.name = 'Arial'
    p_fl.font.size = Pt(10)
    p_fl.font.color.rgb = GRAY_TEXT

    ft_right = slide.shapes.add_textbox(Inches(10.8), Inches(7.06), Inches(2.1), Inches(0.35))
    p_fr = ft_right.text_frame.paragraphs[0]
    p_fr.text = f"Слайд {slide_num} из {total_slides}"
    p_fr.font.name = 'Arial'
    p_fr.font.size = Pt(11)
    p_fr.font.bold = True
    p_fr.font.color.rgb = NAVY
    p_fr.alignment = PP_ALIGN.RIGHT


def add_card(slide, left, top, width, height, title="", bullets=None, bg_color=BG_LIGHT, border_color=CARD_BORDER, title_color=NAVY, font_size=14):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.adjustments[0] = 0.04
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)

    tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.1), Inches(width - 0.3), Inches(height - 0.2))
    tf = tb.text_frame
    tf.word_wrap = True

    first = True
    if title:
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = 'Arial'
        p.font.size = Pt(font_size + 1.5)
        p.font.bold = True
        p.font.color.rgb = title_color
        p.space_after = Pt(6)
        first = False

    if bullets:
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.text = b
            p.font.name = 'Arial'
            p.font.size = Pt(font_size)
            p.font.color.rgb = DARK_TEXT
            p.space_after = Pt(5)
    return card


def add_kpi_box(slide, left, top, width, height, big_value, label, accent_color=BLUE):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.adjustments[0] = 0.06
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = accent_color
    box.line.width = Pt(2.0)

    tb = slide.shapes.add_textbox(Inches(left + 0.1), Inches(top + 0.08), Inches(width - 0.2), Inches(height - 0.15))
    tf = tb.text_frame
    tf.word_wrap = True

    p1 = tf.paragraphs[0]
    p1.text = big_value
    p1.font.name = 'Arial'
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = accent_color
    p1.alignment = PP_ALIGN.CENTER
    p1.space_after = Pt(2)

    p2 = tf.add_paragraph()
    p2.text = label
    p2.font.name = 'Arial'
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = DARK_TEXT
    p2.alignment = PP_ALIGN.CENTER


def add_picture_with_caption(slide, img_path, left, top, width, caption_text):
    if os.path.exists(img_path):
        pic = slide.shapes.add_picture(img_path, Inches(left), Inches(top), width=Inches(width))
        img_h = pic.height.inches
        cap_box = slide.shapes.add_textbox(Inches(left), Inches(top + img_h + 0.04), Inches(width), Inches(0.45))
        tf = cap_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = caption_text
        p.font.name = 'Arial'
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.italic = True
        p.font.color.rgb = NAVY
        p.alignment = PP_ALIGN.CENTER


def add_ppt_table(slide, left, top, width, height, data, col_widths=None):
    rows = len(data)
    cols = len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)

    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if r_idx == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
            elif r_idx % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = BG_LIGHT
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE

            for p in cell.text_frame.paragraphs:
                p.font.name = 'Arial'
                p.font.size = Pt(12 if r_idx == 0 else 11.5)
                p.font.bold = (r_idx == 0 or c_idx == 0)
                p.font.color.rgb = WHITE if r_idx == 0 else DARK_TEXT
                p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT


def generate_presentation(out_dir, img_dir):
    # Сгенерируем PNG-изображения математических формул
    formulas = build_formula_images(img_dir)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # =========================================================================
    # СЛАЙД 1: ТИТУЛЬНЫЙ СЛАЙД
    # =========================================================================
    s1 = prs.slides.add_slide(blank)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(0.8), Inches(0.15), Inches(5.9))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = ORANGE
    stripe.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(6.8), Inches(5.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "ВСЕРОССИЙСКИЙ КОНКУРС НАУЧНО-ИССЛЕДОВАТЕЛЬСКИХ РАБОТ ИМ. Д.И. МЕНДЕЛЕЕВА"
    p.font.name = 'Arial'
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(160, 205, 255)
    p.space_after = Pt(8)

    p = tf1.add_paragraph()
    p.text = "Конференция «Практика – критерий истины» | Секция № 1"
    p.font.name = 'Arial'
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(210, 225, 245)
    p.space_after = Pt(24)

    p = tf1.add_paragraph()
    p.text = "Разработка автоматизированного устройства для измерения распределения магнитного поля соленоидов"
    p.font.name = 'Arial'
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.space_after = Pt(20)

    p = tf1.add_paragraph()
    p.text = "Направление: Передовые производственные технологии\n(Цифровые двойники, электромагнетизм, 2D-магнитометрия)"
    p.font.name = 'Arial'
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(255, 200, 150)
    p.space_after = Pt(28)

    p = tf1.add_paragraph()
    p.text = "Выполнил: Лукьянов Кирилл Алексеевич\nОбучающийся 10 класса МОУ “Сланцевская СОШ №1”\nНаучный руководитель: Заборская Ольга Владимировна, учитель физики\nЛенинградская область, Сланцевский район, 2026 г."
    p.font.name = 'Arial'
    p.font.size = Pt(14)
    p.font.color.rgb = WHITE

    img3_file = os.path.join(img_dir, 'fig3_2d_heatmap.png')
    if os.path.exists(img3_file):
        s1.shapes.add_picture(img3_file, Inches(7.9), Inches(1.4), width=Inches(5.0))
        cap1 = s1.shapes.add_textbox(Inches(7.9), Inches(4.5), Inches(5.0), Inches(0.5))
        cp = cap1.text_frame.paragraphs[0]
        cp.text = "Рис. Визуализация 2D-карты магнитного поля |B(x, z)|"
        cp.font.name = 'Arial'
        cp.font.size = Pt(11)
        cp.font.italic = True
        cp.font.color.rgb = RGBColor(200, 220, 240)
        cp.alignment = PP_ALIGN.CENTER

    num1 = s1.shapes.add_textbox(Inches(11.0), Inches(6.95), Inches(1.9), Inches(0.4))
    pn1 = num1.text_frame.paragraphs[0]
    pn1.text = "Слайд 1 из 13"
    pn1.font.name = 'Arial'
    pn1.font.size = Pt(11)
    pn1.font.bold = True
    pn1.font.color.rgb = RGBColor(180, 200, 230)
    pn1.alignment = PP_ALIGN.RIGHT

    # =========================================================================
    # СЛАЙД 2: АКТУАЛЬНОСТЬ И ПРОБЛЕМА
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    add_header_and_footer(s2, "1. Актуальность темы и инженерная проблема",
                          "Почему ручные измерения и школьные формулы недостаточны для проектирования катушек?", 2)

    add_card(s2, 0.45, 1.3, 4.0, 4.1,
             title="Где применяются соленоиды?",
             bullets=[
                 "• Электромагнитные клапаны и линейные шаговые актуаторы",
                 "• Магнитные фокусирующие линзы и ускорители частиц",
                 "• Датчики перемещения и системы МРТ-томографии",
                 "• Эталонные источники однородного магнитного поля"
             ], font_size=14)

    add_card(s2, 4.65, 1.3, 4.0, 4.1,
             title="Проблема ручных измерений",
             bullets=[
                 "• Смещение щупа рукой на 1–2 мм дает погрешность до 5–8% у торцов",
                 "• Угловой перекос датчика Холла искажает проекцию поля",
                 "• Для 2D-карты нужно > 5 000 точек (вручную — более 20 часов работы)",
                 "• Дорого наматывать десятки пробных катушек вслепую"
             ], bg_color=RGBColor(255, 245, 242), border_color=ORANGE, title_color=ORANGE, font_size=14)

    add_card(s2, 8.85, 1.3, 4.0, 4.1,
             title="Ограничение простых формул",
             bullets=[
                 "• Формула B₀ = μ₀·n·I работает только для бесконечной катушки",
                 "• На краю катушки поле падает вдвое и разгибается (краевой эффект)",
                 "• Точная алгебраическая формула есть ТОЛЬКО строго на оси (x = 0)",
                 "• Вне оси — сложные эллиптические интегралы Лежандра"
             ], font_size=14)

    add_card(s2, 0.45, 5.6, 12.4, 1.25,
             title="Идея и решение проекта (Передовые производственные технологии):",
             bullets=[
                 "Создать ЦИФРОВОЙ ДВОЙНИК автоматизированного 2D-сканера на языке Python, который перемещает виртуальный датчик Холла с шаговым приводом и АЦП по сетке и строит карту поля за 2,5 секунды!"
             ], bg_color=RGBColor(232, 246, 238), border_color=GREEN, title_color=GREEN, font_size=14.5)

    # =========================================================================
    # СЛАЙД 3: НАУЧНЫЙ АППАРАТ (ЦЕЛЬ, ОБЪЕКТ, ПРЕДМЕТ, ГИПОТЕЗА)
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    add_header_and_footer(s3, "2. Научный аппарат: цель, объект, предмет и гипотеза",
                          "Методологическая основа научно-исследовательской и проектной работы", 3)

    add_card(s3, 0.45, 1.3, 12.4, 1.35,
             title="ЦЕЛЬ РАБОТЫ:",
             bullets=[
                 "Разработать программно-математическую модель автоматизированного устройства для сканирования и визуализации распределения магнитного поля соленоидов и исследовать с её помощью топографию поля катушек различной геометрии."
             ], bg_color=RGBColor(235, 243, 255), border_color=BLUE, title_color=NAVY, font_size=15)

    add_card(s3, 0.45, 2.85, 6.05, 1.85,
             title="ОБЪЕКТ ИССЛЕДОВАНИЯ:",
             bullets=[
                 "Пространственное распределение магнитного поля цилиндрического соленоида конечной длины с постоянным током."
             ], font_size=14.5)

    add_card(s3, 6.8, 2.85, 6.05, 1.85,
             title="ПРЕДМЕТ ИССЛЕДОВАНИЯ:",
             bullets=[
                 "Алгоритмы автоматизированного численного 2D-сканирования индукции и влияние отношения длины к диаметру (L / D) и шага сетки (Δz) на точность карты и зону однородности поля."
             ], font_size=14.5)

    add_card(s3, 0.45, 4.9, 12.4, 1.95,
             title="ПРОВЕРЯЕМАЯ ГИПОТЕЗА ИССЛЕДОВАНИЯ:",
             bullets=[
                 "1) Автоматизированное численное сканирование на основе суперпозиции закона Био — Савара — Лапласа и модели датчика Холла с 5-кратным усреднением позволяет строить карты поля с относительной погрешностью < 0,5% относительно аналитического эталона на оси.",
                 "2) Протяженность центральной зоны однородного поля (с отклонением индукции не более ±5% от центра) превышает 60% длины соленоида при отношении длины к диаметру L / D ≥ 5."
             ], bg_color=RGBColor(255, 248, 235), border_color=ORANGE, title_color=ORANGE, font_size=14.5)

    # =========================================================================
    # СЛАЙД 4: ЗАДАЧИ И ХАРАКТЕРИСТИКИ ВЫБРАННЫХ МЕТОДОВ
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    add_header_and_footer(s4, "3. Задачи проекта и характеристики выбранных методов",
                          "Промежуточные результаты (задачи) и метрологическая оценка метода", 4)

    add_card(s4, 0.45, 1.3, 5.8, 5.5,
             title="4 задачи проекта:",
             bullets=[
                 "Задача 1 (Проектная): спроектировать архитектуру цифрового 2D-сканера с кинематикой обхода «змейка».",
                 "Задача 2 (Программная): реализовать на Python расчет компонент Bx, Bz по закону Био — Савара — Лапласа в любой точке (x, z).",
                 "Задача 3 (Контрольная): провести контрольный эксперимент на оси (положительный эталон и отрицательный при I = 0 А).",
                 "Задача 4 (Исследовательская): построить 2D-карты поля, изучить краевые эффекты и зависимость плато однородности от L / D и шага сетки Δz."
             ], font_size=14)

    t_methods = [
        ["Параметр метода", "Реализация в нашем проекте"],
        ["Прототип датчика", "Линейный датчик Холла Honeywell SS49E + 14-бит АЦП"],
        ["Чувствительность", "Шаг АЦП: ΔB = 0,01 мТл (10 мкТл); СКО шума: σ = 0,035 мТл"],
        ["Специфичность", "Раздельная регистрация ортогональных проекций Bx и Bz"],
        ["Воспроизводимость", "m = 5 повторных измерений в узле (снижение СКО в √5 = 2,24 раза)"],
        ["Точность привода", "Модель шагового привода NEMA 17 (СКО ошибки σ_поз = 50 мкм)"],
        ["Себестоимость", "0 руб. (экономия ~18 500 руб. до сборки ЧПУ-стенда)"]
    ]
    add_ppt_table(s4, 6.45, 1.3, 6.4, 5.5, t_methods, col_widths=[2.3, 4.1])

    # =========================================================================
    # СЛАЙД 5: АРХИТЕКТУРА УСТРОЙСТВА И КИНЕМАТИЧЕСКАЯ СХЕМА (РИС. 1)
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    add_header_and_footer(s5, "4. Архитектура цифрового сканера и кинематика движения",
                          "Блок-схема работы программного комплекса и траектория обхода рабочей области", 5)

    steps_arch = [
        ("Модуль 1. SolenoidModel (Геометрия катушки)", "Задание L = 100 мм, R = 20 мм, N = 500 витков, I = 2 А, разбиение витков на M = 120 угловых секторов Δφ"),
        ("Модуль 2. Координатный 2D-привод («Змейка»)", "Перемещение каретки по сетке (z_j, x_i) с учетом микроошибки позиционирования σ_поз = 50 мкм"),
        ("Модуль 3. Виртуальный датчик Холла + АЦП", "Расчет поля (Bx, Bz) + наложение теплового шума (0,035 мТл) + квантование АЦП + усреднение m = 5 повторов"),
        ("Модуль 4. Визуализация и аналитика", "Построение осевых срезов, 2D тепловых карт |B(x, z)|, силовых линий и расчет зоны однородности")
    ]
    for idx, (st_title, st_desc) in enumerate(steps_arch):
        top_pos = 1.3 + idx * 1.38
        add_card(s5, 0.45, top_pos, 5.5, 1.22, title=st_title, bullets=[st_desc],
                 bg_color=RGBColor(238, 245, 255) if idx % 2 == 0 else BG_LIGHT,
                 border_color=BLUE, font_size=12.5)

    add_picture_with_caption(
        s5,
        os.path.join(img_dir, 'fig1_scanner_scheme.png'),
        left=6.2, top=1.45, width=6.65,
        caption_text="Рис. 1. Кинематическая схема 2D-сканирования поля соленоида по траектории «змейка»"
    )

    # =========================================================================
    # СЛАЙД 6: ФИЗИКО-МАТЕМАТИЧЕСКОЕ ЯДРО МОДЕЛИ (С КРАСИВЫМИ ФОРМУЛАМИ!)
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    add_header_and_footer(s6, "5. Физико-математическая модель расчета поля",
                          "Дискретная суперпозиция закона Био — Савара — Лапласа, эталон на оси и модель датчика", 6)

    # Карточка 1 (слева вверху): Закон Био-Савара + численная суперпозиция
    add_card(s6, 0.45, 1.22, 6.1, 3.65,
             title="1. Численное ядро в 2D/3D (в плоскости сечения y = 0):",
             bullets=[
                 "Проекции индукции в произвольной точке P(x, 0, z) от N витков:"
             ], bg_color=RGBColor(235, 243, 255), border_color=BLUE, font_size=13)
    if os.path.exists(formulas['eq2']):
        s6.shapes.add_picture(formulas['eq2'], Inches(0.6), Inches(1.98), width=Inches(5.8))

    # Карточка 2 (справа вверху): Аналитический эталон на оси
    add_card(s6, 6.75, 1.22, 6.1, 3.65,
             title="2. Аналитический эталон на центральной оси Oz (x = 0, y = 0):",
             bullets=[
                 "На оси соленоида поперечные координаты равны нулю (x = 0, y = 0):"
             ], bg_color=RGBColor(255, 248, 235), border_color=ORANGE, title_color=ORANGE, font_size=13)
    if os.path.exists(formulas['eq3']):
        s6.shapes.add_picture(formulas['eq3'], Inches(6.9), Inches(2.0), width=Inches(5.8))
    # Доп. пояснение под формулой эталона
    tb_c2 = s6.shapes.add_textbox(Inches(6.9), Inches(3.85), Inches(5.8), Inches(0.9))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p_c2 = tf_c2.paragraphs[0]
    p_c2.text = "• При L = 100 мм, R = 20 мм, N = 500, I = 2 А:\n   B₀ = 12,566 мТл  |  Bz(0, 0, 0) = 11,668 мТл  |  Bz(0, 0, ±50 мм) = 6,161 мТл"
    p_c2.font.name = 'Arial'
    p_c2.font.size = Pt(12.5)
    p_c2.font.bold = True
    p_c2.font.color.rgb = DARK_TEXT

    # Карточка 3 (внизу во всю ширину): Модель датчика Холла и АЦП
    add_card(s6, 0.45, 5.0, 12.4, 1.92,
             title="3. Стохастическая функция отклика датчика Холла с АЦП и фильтрацией (m = 5 повторов):",
             bullets=[], bg_color=BG_LIGHT, border_color=GREEN, title_color=GREEN, font_size=13)
    if os.path.exists(formulas['eq4']):
        s6.shapes.add_picture(formulas['eq4'], Inches(0.85), Inches(5.42), width=Inches(11.6))

    # =========================================================================
    # СЛАЙД 7: КОНТРОЛЬНЫЙ ЭКСПЕРИМЕНТ (РИС. 2)
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    add_header_and_footer(s7, "6. Контрольный эксперимент: верификация на оси соленоида",
                          "Положительный контроль (сравнение с эталоном) и отрицательный контроль (при I = 0 А)", 7)

    add_kpi_box(s7, 0.45, 1.3, 2.8, 1.15, "0,173 %", "Погрешность численного\nядра Био — Савара", BLUE)
    add_kpi_box(s7, 3.45, 1.3, 2.8, 1.15, "0,208 %", "Ошибка датчика с шумом\n(гипотеза: < 0,5%)", GREEN)

    t_ctrl = [
        ["Точка на оси z", "Эталон, мТл", "Датчик (5 изм.), мТл", "Контроль I = 0 А"],
        ["Центр (z = 0 мм)", "11,668", "11,638 ± 0,016", "0,004 ± 0,015"],
        ["Внутри (z = 25 мм)", "10,938", "10,915 ± 0,014", "−0,005 ± 0,016"],
        ["Торец (z = 50 мм)", "6,161", "6,146 ± 0,018", "−0,008 ± 0,016"],
        ["Вне (z = 80 мм)", "0,893", "0,884 ± 0,014", "0,002 ± 0,015"],
        ["Итог (RMSE / фон)", "0,000 (эталон)", "RMSE = 0,024 мТл", "СКО = 0,0158 мТл"]
    ]
    add_ppt_table(s7, 0.45, 2.65, 5.8, 4.1, t_ctrl, col_widths=[1.6, 1.3, 1.6, 1.3])

    add_picture_with_caption(
        s7,
        os.path.join(img_dir, 'fig2_axis_verification.png'),
        left=6.45, top=1.25, width=6.4,
        caption_text="Рис. 2. Распределение индукции Bz(z) вдоль оси и погрешность датчика Холла"
    )

    # =========================================================================
    # СЛАЙД 8: ДВУМЕРНАЯ КАРТА МАГНИТНОГО ПОЛЯ (РИС. 3)
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    add_header_and_footer(s8, "7. Результаты: Двумерная топографическая карта поля |B(x, z)|",
                          "Визуализация модуля магнитной индукции и силовых линий внутри и снаружи катушки", 8)

    add_kpi_box(s8, 0.45, 1.3, 2.65, 1.15, "5 551", "узлов координатной\n2D-сетки (91 × 61)", NAVY)
    add_kpi_box(s8, 3.25, 1.3, 2.65, 1.15, "27 755", "отсчетов виртуального\nдатчика Холла", BLUE)

    add_card(s8, 0.45, 2.65, 5.45, 4.1,
             title="Что выявила 2D-карта поля:",
             bullets=[
                 "1. Однородное ядро внутри полости: в центральной зоне (|z| < 23 мм) формируется стабильное плато с индукцией 11,1–11,7 мТл.",
                 "2. Краевой эффект на торцах (z = ±50 мм): силовые линии веерообразно расходятся, а модуль поля падает ровно в 2 раза (до 6,16 мТл).",
                 "3. Замыкание потока снаружи: за пределами обмотки (|x| > 20 мм) линии поля возвращаются от правого полюса к левому, а модуль поля быстро убывает до 0,5–2,2 мТл."
             ], font_size=13.5)

    add_picture_with_caption(
        s8,
        os.path.join(img_dir, 'fig3_2d_heatmap.png'),
        left=6.1, top=1.4, width=6.75,
        caption_text="Рис. 3. Двумерная тепловая карта |B(x, z)| и линии магнитной индукции соленоида"
    )

    # =========================================================================
    # СЛАЙД 9: РАДИАЛЬНЫЕ ПРОФИЛИ И ИНВЕРСИЯ ПОЛЯ (РИС. 4)
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    add_header_and_footer(s9, "8. Поперечные профили поля и эффект инверсии знака Bz",
                          "Физические эффекты вне оси соленоида, недоступные при обычных осевых измерениях", 9)

    add_card(s9, 0.45, 1.3, 5.55, 2.65,
             title="Эффект 1. Седлообразный профиль внутри:",
             bullets=[
                 "• При движении датчика от оси (x = 0) к внутренней стенке обмотки (x → ±20 мм) продольное поле Bz НЕ падает, а растет!",
                 "• В центре (z = 0) рост составляет +4,5% (до 12,18 мТл), а у торца (z = 40 мм) — до +71% (14,85 мТл) из-за сгущения линий у витков."
             ], bg_color=RGBColor(235, 243, 255), border_color=BLUE, font_size=13.5)

    add_card(s9, 0.45, 4.15, 5.55, 2.65,
             title="Эффект 2. Инверсия знака Bz снаружи катушки:",
             bullets=[
                 "• При пересечении обмотки (|x| > 20 мм) проекция Bz скачком меняет знак на противоположный (до −2,4 мТл).",
                 "• Причина: линии магнитного поля замкнуты (div B = 0) и снаружи катушки идут навстречу внутреннему потоку."
             ], bg_color=RGBColor(255, 245, 242), border_color=ORANGE, title_color=ORANGE, font_size=13.5)

    add_picture_with_caption(
        s9,
        os.path.join(img_dir, 'fig4_radial_profiles.png'),
        left=6.2, top=1.35, width=6.65,
        caption_text="Рис. 4. Радиальные профили продольной индукции Bz(x) в сечениях z = 0..65 мм"
    )

    # =========================================================================
    # СЛАЙД 10: ПРОВЕРКА ГИПОТЕЗЫ — ВЛИЯНИЕ L/D НА ОДНОРОДНОСТЬ (РИС. 5)
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    add_header_and_footer(s10, "9. Проверка гипотезы: влияние отношения L/D на однородность",
                          "Зависимость протяженности рабочего плато однородного поля от форм-фактора катушки", 10)

    t_unif = [
        ["Отношение L / D", "Bz(0) / B₀", "Плато ±5% от L", "Плато ±1% от L"],
        ["1,0 (короткая, 40 мм)", "70,71 %", "36,2 %", "16,2 %"],
        ["2,5 (базовая, 100 мм)", "92,85 %", "46,6 %", "22,7 %"],
        ["5,0 (длинная, 200 мм)", "98,06 %", "64,6 % (> 60%!)", "37,7 %"],
        ["10,0 (сверхдлинная)", "99,50 %", "80,0 %", "58,6 %"]
    ]
    add_ppt_table(s10, 0.45, 1.3, 5.65, 3.2, t_unif, col_widths=[1.85, 1.2, 1.4, 1.2])

    add_card(s10, 0.45, 4.7, 5.65, 2.1,
             title="ГИПОТЕЗА ПОЛНОСТЬЮ ПОДТВЕРЖДЕНА!",
             bullets=[
                 "• У короткой катушки (L / D = 1) краевые эффекты смыкаются в центре (плато всего 36,2%).",
                 "• При L / D = 5,0 зона 5%-й однородности достигает 64,6% длины (превышая порог гипотезы 60%), а поле в центре равно 98,1% от B₀."
             ], bg_color=RGBColor(232, 246, 238), border_color=GREEN, title_color=GREEN, font_size=13.5)

    add_picture_with_caption(
        s10,
        os.path.join(img_dir, 'fig5_uniformity_study.png'),
        left=6.3, top=1.35, width=6.55,
        caption_text="Рис. 5. Профили относительной индукции Bz(z)/Bz(0) при различных L/D"
    )

    # =========================================================================
    # СЛАЙД 11: ОПТИМИЗАЦИЯ ШАГА СКАНЕРА И ПРАКТИЧЕСКАЯ ЗНАЧИМОСТЬ
    # =========================================================================
    s11 = prs.slides.add_slide(blank)
    add_header_and_footer(s11, "10. Оптимизация шага сканирования и практическая ценность",
                          "Выбор рационального режима работы шагового привода и области внедрения разработки", 11)

    t_step = [
        ["Шаг сканера Δz", "Узлов в 2D-карте", "Ошибка интерполяции", "Оценка режима"],
        ["0,5 мм", "72 581", "0,003 %", "Избыточно долго (~2,5 часа)"],
        ["1,0 мм", "18 291", "0,014 %", "Для узких торцевых зон"],
        ["2,0 мм (ОПТИМУМ)", "4 646", "0,058 % (< 0,1%)", "Ускорение в 15,6 раза без потери точности!"],
        ["5,0 мм", "779", "0,347 %", "Быстрый экспресс-контроль"],
        ["10,0 мм", "210", "1,246 %", "Сглаживание градиента у торцов"],
        ["20,0 мм", "66", "3,749 %", "Недопустимая потеря разрешения"]
    ]
    add_ppt_table(s11, 0.45, 1.3, 7.1, 5.45, t_step, col_widths=[1.6, 1.4, 1.6, 2.5])

    add_card(s11, 7.8, 1.3, 5.05, 5.45,
             title="Практическое применение проекта:",
             bullets=[
                 "1. Инженерное проектирование (CAE):",
                 "Быстрый подбор длины, радиуса и числа витков катушек клапанов и магнитов до намотки провода.",
                 "",
                 "2. Учебный виртуальный практикум:",
                 "Готовая цифровая лаборатория для уроков физики и центров «Интеллект» и «Кванториум».",
                 "",
                 "3. ПО для реального ЧПУ-стенда:",
                 "Алгоритм «змейки» с оптимальным шагом Δz = 2 мм готов к управлению 2D-столом на базе Arduino Nano + NEMA 17 + АЦП ADS1115 + датчик Холла SS49E."
             ], bg_color=RGBColor(235, 243, 255), border_color=BLUE, font_size=13.5)

    # =========================================================================
    # СЛАЙД 12: АППАРАТНАЯ КОМПОНОВКА ДВУХКООРДИНАТНОГО СТЕНДА (ФОТО)
    # =========================================================================
    s_hw = prs.slides.add_slide(blank)
    add_header_and_footer(s_hw, "11. Аппаратная компоновка двухкоординатного стенда",
                          "Интеграция разработанного цифрового ядра с координатным приводом и датчиком Холла", 12)

    add_card(s_hw, 0.45, 1.3, 5.7, 2.75,
             title="1. Кинематика и немагнитная конструкция:",
             bullets=[
                 "• Подвижный 2D-портал (оси X и Z) на профиле 2020 с рельсами MGN, винтами Т8 и двумя моторами NEMA 17.",
                 "• Все стальные валы вынесены на > 15 см от катушки (отсутствие ферромагнитных искажений поля).",
                 "• Внутрь соленоида консольно входит только немагнитная штанга из PLA с датчиком Холла Honeywell SS49E."
             ], bg_color=RGBColor(235, 243, 255), border_color=BLUE, font_size=13.2)

    add_card(s_hw, 0.45, 4.2, 5.7, 2.65,
             title="2. Электрический тракт и связь с ПК:",
             bullets=[
                 "• Контроллер Arduino Nano (связь с ноутбуком по USB / Serial) + 2 драйвера шаговых двигателей A4988.",
                 "• Внешний 16-битный АЦП ADS1115 (шина I2C) для точной оцифровки аналогового сигнала датчика Холла.",
                 "• Стабилизатор тока LM2596 для питания обмотки медного соленоида от сетевого адаптера 12 В (евровилка)."
             ], bg_color=BG_LIGHT, border_color=GREEN, title_color=GREEN, font_size=13.2)

    add_picture_with_caption(
        s_hw,
        os.path.join(img_dir, 'prototype_topdown_eu_verified.jpg'),
        left=6.4, top=1.3, width=6.45,
        caption_text="Рис. 6. Общий вид двухкоординатного стенда сканирования магнитного поля соленоида"
    )

    # =========================================================================
    # СЛАЙД 13: ИТОГОВЫЕ ВЫВОДЫ ПО РАБОТЕ + QR-КОД НА GITHUB
    # =========================================================================
    s12 = prs.slides.add_slide(blank)
    add_header_and_footer(s12, "12. Основные выводы по работе и открытый репозиторий",
                          "Сводка результатов исследования и QR-код исходного кода проекта на GitHub", 13)

    add_kpi_box(s12, 0.45, 1.3, 2.9, 1.15, "0,208 %", "Точность модели на оси\n(при гипотезе < 0,5%)", GREEN)
    add_kpi_box(s12, 3.6, 1.3, 2.9, 1.15, "64,6 %", "Плато однородности L/D = 5\n(при гипотезе > 60%)", BLUE)
    add_kpi_box(s12, 6.75, 1.3, 2.9, 1.15, "2,0 мм", "Оптимальный шаг сканера\n(ускорение в 15,6 раза)", ORANGE)
    add_kpi_box(s12, 9.9, 1.3, 2.95, 1.15, "2,5 сек", "Время расчета полной\n2D-карты (5 551 узел)", NAVY)

    add_card(s12, 0.45, 2.62, 9.2, 3.35,
             title="Итоговые выводы (в точном соответствии с задачами 1–4):",
             bullets=[
                 "1. Спроектирована 4-модульная архитектура цифрового двойника 2D-сканера магнитного поля с растровым обходом «змейкой».",
                 "2. Реализовано векторизованное ядро на Python (закон Био — Савара — Лапласа + модель датчика Холла SS49E с 5-кратным усреднением).",
                 "3. В контрольном эксперименте (эталон на оси и I = 0 А) доказана достоверность модели: погрешность составила 0,0243 мТл (0,208%).",
                 "4. Построены 2D-карты поля, выявлена инверсия знака Bz снаружи витков и доказано, что при L / D ≥ 5 плато однородности превышает 64,6% длины катушки."
             ], font_size=13.2)

    # Карточка с QR-кодом GitHub справа
    add_card(s12, 9.85, 2.62, 3.0, 3.35,
             title="Код проекта на GitHub",
             bullets=[], bg_color=WHITE, border_color=NAVY, title_color=NAVY, font_size=13)
    s12.shapes[-1].text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    qr_path = os.path.join(img_dir, 'github_qr.png')
    if os.path.exists(qr_path):
        s12.shapes.add_picture(qr_path, Inches(10.35), Inches(3.05), width=Inches(2.0))
        qr_cap = s12.shapes.add_textbox(Inches(9.9), Inches(5.1), Inches(2.9), Inches(0.8))
        tf_qr = qr_cap.text_frame
        tf_qr.word_wrap = True
        p_qr = tf_qr.paragraphs[0]
        p_qr.text = "github.com/R4yClay/\nsolenoid-field-scanner"
        p_qr.font.name = 'Arial'
        p_qr.font.size = Pt(11)
        p_qr.font.bold = True
        p_qr.font.color.rgb = BLUE
        p_qr.alignment = PP_ALIGN.CENTER

    add_card(s12, 0.45, 6.1, 12.4, 0.8,
             title="",
             bullets=["Спасибо за внимание! Готов ответить на вопросы уважаемого жюри."],
             bg_color=NAVY, border_color=NAVY, title_color=WHITE, font_size=16)
    p_end = s12.shapes[-1].text_frame.paragraphs[0]
    p_end.font.bold = True
    p_end.font.color.rgb = WHITE
    p_end.alignment = PP_ALIGN.CENTER

    out_main = os.path.join(out_dir, 'Презентация_Лукьянов_Кирилл.pptx')
    out_copy = os.path.join(out_dir, 'Презентация_Сканер_поля_соленоидов.pptx')
    prs.save(out_main)
    shutil.copyfile(out_main, out_copy)
    print(f"Сохранена презентация с красивыми формулами: {out_main}")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_directory = os.path.join(base_dir, 'output')
    generate_presentation(base_dir, img_directory)
