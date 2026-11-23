#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор иллюстрированного трёхстворчатого буклета А4 (альбомная ориентация, 6 страниц)
строго по Приложению № 1 к Положению о региональном этапе Всероссийского конкурса
НИР им. Д.И. Менделеева (2026 г.).
"""

import os
import shutil
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT_DIR = "/Users/pb02_luka/.gemini/antigravity/scratch/solenoid_scanner"
IMG_DIR = os.path.join(OUT_DIR, "output")
AUTHOR_FULL = "Лукьянов Кирилл Алексеевич"


def set_cell_borders(cell, color="2B579A", sz="12", val="single"):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(old)
    tcBorders = OxmlElement("w:tcBorders")
    for border_name in ["top", "left", "bottom", "right"]:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), val)
        border.set(qn("w:sz"), sz)
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)


def set_gutter_fold_line(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(old)
    tcBorders = OxmlElement("w:tcBorders")
    for border_name in ["top", "bottom", "left", "right"]:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "none")
        border.set(qn("w:sz"), "0")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "FFFFFF")
        tcBorders.append(border)
    tcPr.append(tcBorders)


def set_cell_shading(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tcPr.append(shd)


def set_para_bottom_border(p, color="2B579A", sz="8"):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), sz)
    b.set(qn("w:space"), "3")
    b.set(qn("w:color"), color)
    pBdr.append(b)
    pPr.append(pBdr)


def set_para_box(p, border_color="7BA0C7"):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    for b_name in ["top", "left", "bottom", "right"]:
        b = OxmlElement(f"w:{b_name}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:space"), "3")
        b.set(qn("w:color"), border_color)
        pBdr.append(b)
    pPr.append(pBdr)


def set_cell_margins(cell, top=90, bottom=90, left=130, right=130):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(old)
    tcMar = OxmlElement("w:tcMar")
    for m_name, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m_name}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_column_widths(table, col_widths_mm):
    total_dxa = sum(int(w * 56.7) for w in col_widths_mm)
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(total_dxa))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)

    for old in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(old)
    tblLayout = OxmlElement("w:tblLayout")
    tblLayout.set(qn("w:type"), "fixed")
    tblPr.append(tblLayout)

    tblGrid = table._tbl.tblGrid
    for old in list(tblGrid):
        tblGrid.remove(old)
    for w_mm in col_widths_mm:
        gridCol = OxmlElement("w:gridCol")
        gridCol.set(qn("w:w"), str(int(w_mm * 56.7)))
        tblGrid.append(gridCol)

    for row in table.rows:
        for idx, w_mm in enumerate(col_widths_mm):
            cell = row.cells[idx]
            cell.width = Mm(w_mm)
            tcPr = cell._tc.get_or_add_tcPr()
            for old in tcPr.findall(qn("w:tcW")):
                tcPr.remove(old)
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:w"), str(int(w_mm * 56.7)))
            tcW.set(qn("w:type"), "dxa")
            tcPr.append(tcW)


def set_row_height(row, height_mm, rule="exact"):
    trPr = row._tr.get_or_add_trPr()
    for old in trPr.findall(qn("w:trHeight")):
        trPr.remove(old)
    trHeight = OxmlElement("w:trHeight")
    trHeight.set(qn("w:val"), str(int(height_mm * 56.7)))
    trHeight.set(qn("w:hRule"), rule)
    trPr.append(trHeight)


def setup_header_cell(cell, page_title, subtitle_text):
    set_cell_borders(cell, color="1B365D", sz="12", val="single")
    set_cell_shading(cell, "1B365D")
    set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    p0 = cell.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(0)
    p0.paragraph_format.line_spacing = 1.05

    r_top = p0.add_run(page_title.upper() + "\n")
    r_top.bold = True
    r_top.font.name = "Times New Roman"
    r_top.font.size = Pt(11.5)
    r_top.font.color.rgb = RGBColor(255, 220, 115)

    r_sub = p0.add_run(subtitle_text)
    r_sub.bold = False
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(8.5)
    r_sub.font.color.rgb = RGBColor(230, 240, 255)


def setup_body_cell(cell, fill_hex="FFFFFF"):
    set_cell_borders(cell, color="2B579A", sz="12", val="single")
    set_cell_shading(cell, fill_hex)
    set_cell_margins(cell, top=90, bottom=90, left=130, right=130)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP


def add_item(cell, label, text, font_size=9.0, space_after=2.5, box_border=None, use_first_para=False):
    p = cell.paragraphs[0] if use_first_para else cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.06
    p.paragraph_format.space_before = Pt(1.5)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.first_line_indent = Mm(0)
    if box_border:
        set_para_box(p, border_color=box_border)
    if label:
        rl = p.add_run(label)
        rl.bold = True
        rl.font.name = "Times New Roman"
        rl.font.size = Pt(font_size)
        if any(k in label for k in ["Тема", "Гипотеза", "Степень подтверждения"]):
            rl.font.color.rgb = RGBColor(165, 20, 20)
        else:
            rl.font.color.rgb = RGBColor(20, 54, 93)
    if text:
        rt = p.add_run((" " if label else "") + text)
        rt.font.name = "Times New Roman"
        rt.font.size = Pt(font_size)
        rt.font.color.rgb = RGBColor(15, 15, 15)
    return p


def add_image_with_caption(cell, img_filename, width_mm, caption_text):
    img_path = os.path.join(IMG_DIR, img_filename)
    if not os.path.exists(img_path):
        return
    p_img = cell.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(2)
    p_img.paragraph_format.space_after = Pt(1)
    p_img.paragraph_format.first_line_indent = Mm(0)
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Mm(width_mm))

    if caption_text:
        p_cap = cell.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(2)
        p_cap.paragraph_format.line_spacing = 1.0
        p_cap.paragraph_format.first_line_indent = Mm(0)
        rc = p_cap.add_run(caption_text)
        rc.italic = True
        rc.font.name = "Times New Roman"
        rc.font.size = Pt(7.8)
        rc.font.color.rgb = RGBColor(65, 75, 90)


def build_docx_booklet():
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width = Mm(297)
    sec.page_height = Mm(210)
    sec.left_margin = Mm(8)
    sec.right_margin = Mm(8)
    sec.top_margin = Mm(8)
    sec.bottom_margin = Mm(8)

    col_widths = [89.0, 7.0, 89.0, 7.0, 89.0]  # 281 мм

    # ==================== ЛИСТ 1 (СТРАНИЦЫ 1, 2, 3) ====================
    # Строка 0 — цветная шапка, Строка 1 — основной контент с графикой
    tbl1 = doc.add_table(rows=2, cols=5)
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_column_widths(tbl1, col_widths)
    set_row_height(tbl1.rows[0], 13, rule="exact")
    set_row_height(tbl1.rows[1], 177, rule="exact")

    for r_i in [0, 1]:
        for g_idx in [1, 3]:
            set_gutter_fold_line(tbl1.cell(r_i, g_idx))

    setup_header_cell(tbl1.cell(0, 0), "Первая страница", "Всероссийский конкурс НИР им. Д.И. Менделеева · 2026")
    setup_header_cell(tbl1.cell(0, 2), "Вторая страница", "Актуальность, новизна, объект и предмет")
    setup_header_cell(tbl1.cell(0, 4), "Третья страница", "Цель, задачи, гипотеза и методы исследования")

    # --- ПЕРВАЯ СТРАНИЦА (ТЕЛО) ---
    c1 = tbl1.cell(1, 0)
    setup_body_cell(c1, fill_hex="FAFCFF")

    add_item(c1, "Конференция:", "«Практика – критерий истины», секция № 1 (инженерная, IT, физическая).", font_size=8.8, use_first_para=True)
    add_item(
        c1,
        "Тема работы:",
        "Разработка автоматизированного устройства для измерения распределения магнитного поля соленоидов",
        font_size=9.2,
        box_border="2B579A"
    )
    add_item(
        c1,
        "Название ОУ (адрес):",
        "МОУ «Сланцевская СОШ №1» (188560, Ленинградская обл., г. Сланцы, ул. Максима Горького, д. 9; тел.: +7 (81374) 2-22-69).",
        font_size=8.6
    )

    photo_tbl = c1.add_table(rows=1, cols=2)
    photo_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_column_widths(photo_tbl, [26.0, 56.0])
    cell_ph = photo_tbl.cell(0, 0)
    cell_au = photo_tbl.cell(0, 1)
    set_cell_borders(cell_ph, color="4A77A8", sz="8", val="dashed")
    set_cell_borders(cell_au, color="FFFFFF", sz="0", val="none")
    set_cell_shading(cell_ph, "EBF2FA")
    set_cell_margins(cell_ph, top=110, bottom=110, left=50, right=50)
    set_cell_margins(cell_au, top=20, bottom=20, left=100, right=20)
    cell_ph.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    p_ph = cell_ph.paragraphs[0]
    p_ph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ph.paragraph_format.line_spacing = 1.05
    r_ph = p_ph.add_run("Место для\nфото\nучастника\n(3 × 4 см)")
    r_ph.font.name = "Times New Roman"
    r_ph.font.size = Pt(8.0)
    r_ph.font.color.rgb = RGBColor(60, 85, 115)

    p_au1 = cell_au.paragraphs[0]
    p_au1.paragraph_format.space_after = Pt(2)
    p_au1.paragraph_format.line_spacing = 1.08
    r_l1 = p_au1.add_run("ФИО участника, класс:\n")
    r_l1.bold = True
    r_l1.font.name = "Times New Roman"
    r_l1.font.size = Pt(8.8)
    r_l1.font.color.rgb = RGBColor(20, 54, 93)
    r_v1 = p_au1.add_run(f"{AUTHOR_FULL},\n10 класс\n")
    r_v1.font.name = "Times New Roman"
    r_v1.font.size = Pt(8.8)

    r_l2 = p_au1.add_run("Дата рождения:\n")
    r_l2.bold = True
    r_l2.font.name = "Times New Roman"
    r_l2.font.size = Pt(8.8)
    r_l2.font.color.rgb = RGBColor(20, 54, 93)
    r_v2 = p_au1.add_run("«___» ___________ 2010 г.")
    r_v2.font.name = "Times New Roman"
    r_v2.font.size = Pt(8.8)

    add_item(
        c1,
        "Научный руководитель (должность, квалификационная категория):",
        "Заборская Ольга Владимировна, учитель физики МОУ «Сланцевская СОШ №1», высшая квалификационная категория.",
        font_size=8.6
    )

    add_image_with_caption(
        c1,
        "fig1_scanner_scheme.png",
        width_mm=78,
        caption_text="Рис. 1. Архитектура 2D-сканера и схема обхода соленоида «змейкой»"
    )

    # --- ВТОРАЯ СТРАНИЦА (ТЕЛО) ---
    c2 = tbl1.cell(1, 2)
    setup_body_cell(c2, fill_hex="FFFFFF")

    add_item(
        c2,
        "Актуальность исследования:",
        "ручное измерение магнитного поля катушек трудоемко и дает высокую погрешность позиционирования датчика, а аналитические формулы из учебников применимы только строго на оси соленоида. Цифровой двойник 2D-сканера позволяет быстро строить точные карты поля и находить зоны однородности до сборки дорогостоящего стенда.",
        font_size=8.8,
        use_first_para=True
    )
    add_item(
        c2,
        "Новизна исследования:",
        "объединение 3D-расчета по закону Био–Савара–Лапласа с реалистичной метрологической моделью датчика Холла SS49E (учет теплового шума, квантования АЦП и погрешности шагового привода) и количественная оценка плато однородности поля при разных L/D.",
        font_size=8.8
    )
    add_item(
        c2,
        "Объект исследования:",
        "пространственное распределение магнитного поля цилиндрического соленоида конечной длины.",
        font_size=8.8,
        box_border="7BA0C7"
    )
    add_item(
        c2,
        "Предмет исследования:",
        "алгоритмы автоматического численного 2D-сканирования индукции поля и влияние отношения длины к диаметру (L/D) и шага сетки на точность карты поля.",
        font_size=8.8,
        box_border="7BA0C7"
    )

    add_image_with_caption(
        c2,
        "eq1_biot_savart.png",
        width_mm=72,
        caption_text="Закон Био–Савара–Лапласа (суперпозиция N витков)"
    )
    add_image_with_caption(
        c2,
        "eq3_analytical_axis.png",
        width_mm=72,
        caption_text="Аналитический эталон поля Bz(0, z) на оси соленоида"
    )
    add_image_with_caption(
        c2,
        "eq4_sensor_model.png",
        width_mm=76,
        caption_text="Метрологическая модель датчика Холла с шумом и АЦП"
    )

    # --- ТРЕТЬЯ СТРАНИЦА (ТЕЛО) ---
    c3 = tbl1.cell(1, 4)
    setup_body_cell(c3, fill_hex="FFFFFF")

    add_item(
        c3,
        "Цель исследования:",
        "разработать программно-математическую модель автоматизированного устройства для сканирования и визуализации поля соленоидов и исследовать топографию поля катушек различной геометрии.",
        font_size=8.7,
        use_first_para=True
    )
    add_item(
        c3,
        "Задачи исследования:",
        "\n1) Спроектировать кинематику 2D-сканера («змейка»);"
        "\n2) Реализовать на Python расчет компонент Bx, Bz по закону Био–Савара–Лапласа;"
        "\n3) Провести контрольный эксперимент (эталон на оси z и нулевой контроль при I = 0 А);"
        "\n4) Построить 2D-карты поля и исследовать зону однородности при различных L/D.",
        font_size=8.5
    )
    add_item(
        c3,
        "Гипотеза исследования:",
        "численное 2D-сканирование с 5-кратным усреднением обеспечивает погрешность < 0,5% относительно эталона на оси, а при L/D >= 5 зона 5%-й однородности превышает 60% длины соленоида.",
        font_size=8.6,
        box_border="C0504D"
    )
    add_item(
        c3,
        "Методы исследования:",
        "численное интегрирование, метод Монте-Карло (шум датчика), контрольный эксперимент, статистический анализ, научная визуализация.",
        font_size=8.5
    )

    add_image_with_caption(
        c3,
        "fig2_axis_verification.png",
        width_mm=76,
        caption_text="Рис. 2. Верификация сканера по аналитическому эталону (ошибка 0,208%)"
    )

    # Разрыв страницы между Листом 1 и Листом 2
    p_br = doc.add_paragraph()
    p_br.paragraph_format.space_before = Pt(0)
    p_br.paragraph_format.space_after = Pt(0)
    r_br = p_br.add_run()
    br_el = OxmlElement("w:br")
    br_el.set(qn("w:type"), "page")
    r_br._r.append(br_el)

    # ==================== ЛИСТ 2 (СТРАНИЦЫ 4, 5, 6) ====================
    tbl2 = doc.add_table(rows=2, cols=5)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_column_widths(tbl2, col_widths)
    set_row_height(tbl2.rows[0], 13, rule="exact")
    set_row_height(tbl2.rows[1], 177, rule="exact")

    for r_i in [0, 1]:
        for g_idx in [1, 3]:
            set_gutter_fold_line(tbl2.cell(r_i, g_idx))

    setup_header_cell(tbl2.cell(0, 0), "Четвертая страница", "Программа (план) исследования · 05.09 – 13.11.2026")
    setup_header_cell(tbl2.cell(0, 2), "Пятая страница", "Краткое содержание и выводы по главам")
    setup_header_cell(tbl2.cell(0, 4), "Шестая страница", "Заключение: цель, гипотеза, выводы и рекомендации")

    # --- ЧЕТВЕРТАЯ СТРАНИЦА (ТЕЛО) ---
    c4 = tbl2.cell(1, 0)
    setup_body_cell(c4, fill_hex="FFFFFF")

    add_item(
        c4,
        "Этап 1. Задумка и аналитика (05.09 – 20.09.2026):",
        "выбор темы, анализ теории поля конечного соленоида, краевых эффектов, параметров датчика Холла SS49E и шаговых ЧПУ-приводов.",
        font_size=8.5,
        use_first_para=True
    )
    add_item(
        c4,
        "Этап 2. Проектирование (21.09 – 10.10.2026):",
        "разработка кинематической схемы 2D-сканера, траектории «змейка», вывод квадратурных формул Био–Савара–Лапласа и модели погрешностей (шум 0,035 мТл, квант АЦП 0,01 мТл, люфт 50 мкм).",
        font_size=8.5
    )
    add_item(
        c4,
        "Этап 3. Программирование и эксперименты (11.10 – 02.11.2026):",
        "\n• 11.10–18.10: написание модулей SolenoidModel и VirtualScannerDevice на Python (NumPy, Matplotlib)."
        "\n• 19.10–23.10: Эксперимент 1 — верификация на оси (L=100 мм, R=20 мм, N=500, I=2 А) и контроль при I=0 А."
        "\n• 24.10–28.10: Эксперимент 2 — 2D-сканирование (5551 узел) и поперечные профили Bz(x)."
        "\n• 29.10–02.11: Эксперимент 3 — исследование плато однородности для L/D = 1; 2,5; 5; 10 и шага сетки.",
        font_size=8.4,
        box_border="7BA0C7"
    )
    add_item(
        c4,
        "Этап 4. Обобщение и оформление (03.11 – 13.11.2026):",
        "статистическая обработка, формулировка выводов, подготовка НИР, буклета и презентации.",
        font_size=8.5
    )

    add_image_with_caption(
        c4,
        "fig4_radial_profiles.png",
        width_mm=74,
        caption_text="Рис. 3. Поперечные профили индукции Bz(x) в различных сечениях катушки"
    )

    # --- ПЯТАЯ СТРАНИЦА (ТЕЛО) ---
    c5 = tbl2.cell(1, 2)
    setup_body_cell(c5, fill_hex="FFFFFF")

    add_item(
        c5,
        "Глава 1. Теоретические основы расчета и измерения поля соленоидов:",
        "показано, что школьная аналитическая формула работает только на оси z, а для построения полной 2D-карты необходим численный метод суперпозиции витков и точечный датчик Холла.",
        font_size=8.5,
        use_first_para=True
    )
    add_item(
        c5,
        "Глава 2. Разработка программно-математической модели сканера:",
        "создан цифровой двойник на Python, имитирующий пошаговое перемещение зонда «змейкой» и 5-кратное усреднение отсчетов АЦП в каждом узле сетки.",
        font_size=8.5
    )
    add_item(
        c5,
        "Глава 3. Экспериментальное исследование и верификация:",
        "\n• Расхождение численного ядра с эталоном на оси — 0,173%, с учетом шумов датчика — 0,208% (RMSE = 0,024 мТл)."
        "\n• 2D-карта (5551 узел) выявила сгущение поля у внутренних стенок обмотки (+4,3%) и инверсию знака Bz снаружи витков."
        "\n• При росте L/D с 1 до 5 зона 5%-й однородности растет с 36,2% до 64,6% длины (при L/D = 10 — до 80,0%).",
        font_size=8.4,
        box_border="7BA0C7"
    )

    add_image_with_caption(
        c5,
        "fig3_2d_heatmap.png",
        width_mm=78,
        caption_text="Рис. 4. Двумерная тепловая карта поля |B(x, z)| и векторные линии индукции"
    )

    # --- ШЕСТАЯ СТРАНИЦА (ТЕЛО) ---
    c6 = tbl2.cell(1, 4)
    setup_body_cell(c6, fill_hex="FAFCFF")

    add_item(
        c6,
        "- Выполнение цели исследования:",
        "цель полностью достигнута — разработана, программно реализована и верифицирована цифровая модель автоматизированного 2D-сканера магнитного поля соленоидов.",
        font_size=8.6,
        use_first_para=True
    )
    add_item(
        c6,
        "- Степень подтверждения гипотезы:",
        "гипотеза полностью подтверждена: погрешность сканера с 5-кратным усреднением составила 0,208% (при пороге < 0,5%), а при L/D = 5 зона 5%-й однородности достигла 64,6% длины катушки (при пороге > 60%).",
        font_size=8.6,
        box_border="2B579A"
    )
    add_item(
        c6,
        "- Выводы и рекомендации по работе:",
        "\n1) Для лабораторных установок, требующих однородного поля (отклонение <= 5% на участке > 60% длины), рекомендуется проектировать соленоиды с форм-фактором L/D >= 5."
        "\n2) Оптимальный шаг сетки сканирования для катушек D = 40 мм составляет 2–5 мм (погрешность интерполяции < 0,35% при ускорении сканирования в 15 раз)."
        "\n3) Программный комплекс готов к работе в качестве SCADA-системы для натурного ЧПУ-стенда на базе Arduino и датчика SS49E.",
        font_size=8.4
    )

    add_image_with_caption(
        c6,
        "fig5_uniformity_study.png",
        width_mm=75,
        caption_text="Рис. 5. Зависимость протяженности плато однородности (5%) от форм-фактора L/D"
    )

    out_docx = os.path.join(OUT_DIR, "Буклет_А4_Конкурс_Менделеева.docx")
    doc.save(out_docx)
    shutil.copyfile(out_docx, "/Users/pb02_luka/Downloads/Буклет_А4_Конкурс_Менделеева.docx")
    print(f"Сохранен иллюстрированный буклет DOCX: {out_docx}")


if __name__ == "__main__":
    build_docx_booklet()
