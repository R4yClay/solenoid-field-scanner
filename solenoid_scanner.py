#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Цифровая модель автоматизированного устройства для измерения
распределения магнитного поля соленоидов.

Программа реализует:
1. Физическую модель конечного многослойного/однослойного соленоида
   на основе численного интегрирования закона Био-Савара-Лапласа.
2. Модель виртуального датчика Холла (чувствительность, шум, квантование АЦП,
   погрешность позиционирования шагового привода).
3. Алгоритм автоматического 1D и 2D сканирования («змейкой»).
4. Контрольный эксперимент (сравнение с аналитическим решением на оси z).
5. Визуализацию результатов: схему сканирования, графики на оси, 2D тепловые карты
   и исследование зоны однородности поля при разных отношениях L/D.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Настройка шрифтов для корректного отображения кириллицы
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 200

MU_0 = 4 * np.pi * 1e-7  # Магнитная постоянная, Гн/м


class SolenoidModel:
    """Математическая модель цилиндрического соленоида конечной длины."""

    def __init__(self, length=0.10, radius=0.02, turns=500, current=2.0, n_phi=90):
        """
        :param length: Длина соленоида L, м
        :param radius: Радиус соленоида R, м
        :param turns: Число витков N
        :param current: Сила тока I, А
        :param n_phi: Число разбиений витка по углу для интегрирования Био-Савара
        """
        self.L = length
        self.R = radius
        self.N = turns
        self.I = current
        self.n_phi = n_phi

        # Координаты центров витков вдоль оси z (от -L/2 до +L/2)
        self.z_loops = np.linspace(-self.L / 2.0, self.L / 2.0, self.N)

    def analytical_on_axis(self, z):
        """
        Точная аналитическая формула магнитной индукции B_z на оси тонкого соленоида.
        Используется как положительный контроль для верификации численного сканера.
        """
        n = self.N / self.L  # плотность намотки, витков/м
        term1 = (z + self.L / 2.0) / np.sqrt(self.R ** 2 + (z + self.L / 2.0) ** 2)
        term2 = (z - self.L / 2.0) / np.sqrt(self.R ** 2 + (z - self.L / 2.0) ** 2)
        return 0.5 * MU_0 * n * self.I * (term1 - term2)

    def ideal_infinite_field(self):
        """Индукция в центре бесконечно длинного соленоида B_0 = mu_0 * n * I."""
        return MU_0 * (self.N / self.L) * self.I

    def calc_field_point(self, x, z):
        """
        Численный расчет вектора магнитной индукции (Bx, Bz) в точке (x, 0, z)
        по закону Био-Савара-Лапласа путем суперпозиции полей отдельных витков.
        В силу цилиндрической симметрии плоскость сканирования y = 0.
        """
        if self.I == 0.0:
            return 0.0, 0.0

        phi = np.linspace(0.0, 2.0 * np.pi, self.n_phi, endpoint=False)
        dphi = 2.0 * np.pi / self.n_phi

        cos_phi = np.cos(phi)  # форма (n_phi,)
        # Координата z витков: (N, 1), углы phi: (1, n_phi)
        dz = z - self.z_loops[:, None]  # (N, 1)

        # Квадрат расстояния от элемента тока витка до точки наблюдения (x, 0, z)
        # r^2 = (x - R cos(phi))^2 + (0 - R sin(phi))^2 + (z - z_k)^2
        #     = x^2 + R^2 - 2*x*R*cos(phi) + dz^2
        r2 = x ** 2 + self.R ** 2 - 2.0 * x * self.R * cos_phi[None, :] + dz ** 2
        # Регуляризация вблизи самого провода, чтобы избежать деления на ноль
        r2 = np.maximum(r2, (0.0015) ** 2)
        r3 = r2 ** 1.5

        # Элемент длины витка dl = (-R sin(phi), R cos(phi), 0) dphi
        # Векторное произведение [dl x r] в плоскости y = 0 дает компоненты:
        # dBx ~ R * dz * cos(phi) * dphi / r^3
        # dBz ~ R * (R - x * cos(phi)) * dphi / r^3
        coeff = (MU_0 * self.I / (4.0 * np.pi)) * self.R * dphi

        bx = coeff * np.sum(dz * cos_phi[None, :] / r3)
        bz = coeff * np.sum((self.R - x * cos_phi[None, :]) / r3)

        return float(bx), float(bz)


class VirtualScannerDevice:
    """
    Цифровая модель автоматизированного сканирующего измерителя
    (2D-координатный стол на шаговых двигателях + датчик Холла с АЦП).
    """

    def __init__(
        self,
        solenoid: SolenoidModel,
        pos_error_std=0.00005,   # СКО погрешности позиционирования (50 мкм)
        noise_std_mT=0.035,      # СКО собственного шума датчика Холла (0.035 мТл)
        adc_step_mT=0.01,        # Шаг квантования АЦП в пересчете на мТл
        seed=42
    ):
        self.solenoid = solenoid
        self.pos_error_std = pos_error_std
        self.noise_std_T = noise_std_mT * 1e-3
        self.adc_step_T = adc_step_mT * 1e-3
        self.rng = np.random.default_rng(seed)

    def measure_single_point(self, x, z, n_repeats=5, realistic=True):
        """
        Измерение в одной точке с n_repeats повторными отсчетами АЦП
        (для повышения воспроизводимости и снижения случайного шума).
        """
        if not realistic:
            bx, bz = self.solenoid.calc_field_point(x, z)
            return bx, bz, 0.0

        # Погрешность позиционирования каретки
        dx = self.rng.normal(0.0, self.pos_error_std)
        dz = self.rng.normal(0.0, self.pos_error_std)
        true_bx, true_bz = self.solenoid.calc_field_point(x + dx, z + dz)

        # Серия повторных измерений с шумом и квантованием АЦП
        samples_bx = true_bx + self.rng.normal(0.0, self.noise_std_T, size=n_repeats)
        samples_bz = true_bz + self.rng.normal(0.0, self.noise_std_T, size=n_repeats)

        if self.adc_step_T > 0:
            samples_bx = np.round(samples_bx / self.adc_step_T) * self.adc_step_T
            samples_bz = np.round(samples_bz / self.adc_step_T) * self.adc_step_T

        mean_bx = float(np.mean(samples_bx))
        mean_bz = float(np.mean(samples_bz))
        std_bz = float(np.std(samples_bz, ddof=1)) if n_repeats > 1 else 0.0
        return mean_bx, mean_bz, std_bz

    def scan_1d_axis(self, z_min, z_max, step_z, n_repeats=5):
        """Линейное сканирование вдоль оси соленоида (x = 0)."""
        z_points = np.arange(z_min, z_max + 0.5 * step_z, step_z)
        bz_exact = np.zeros_like(z_points)
        bz_measured = np.zeros_like(z_points)
        bz_std = np.zeros_like(z_points)

        for idx, z in enumerate(z_points):
            _, bz_id, _ = self.measure_single_point(0.0, z, realistic=False)
            _, bz_m, s_bz = self.measure_single_point(0.0, z, n_repeats=n_repeats, realistic=True)
            bz_exact[idx] = bz_id
            bz_measured[idx] = bz_m
            bz_std[idx] = s_bz

        bz_analytical = self.solenoid.analytical_on_axis(z_points)
        return z_points, bz_analytical, bz_exact, bz_measured, bz_std

    def scan_2d_grid(self, x_min, x_max, step_x, z_min, z_max, step_z, realistic=False):
        """
        Двумерное сканирование области пространства «змейкой»
        (как двигается каретка автоматизированного стенда).
        """
        x_coords = np.arange(x_min, x_max + 0.5 * step_x, step_x)
        z_coords = np.arange(z_min, z_max + 0.5 * step_z, step_z)

        BX = np.zeros((len(x_coords), len(z_coords)))
        BZ = np.zeros((len(x_coords), len(z_coords)))
        trajectory = []

        for i, x in enumerate(x_coords):
            # Траектория «змейкой»: четные строки слева направо, нечетные справа налево
            j_indices = range(len(z_coords)) if i % 2 == 0 else range(len(z_coords) - 1, -1, -1)
            for j in j_indices:
                z = z_coords[j]
                trajectory.append((z, x))
                bx, bz, _ = self.measure_single_point(x, z, n_repeats=5, realistic=realistic)
                BX[i, j] = bx
                BZ[i, j] = bz

        return x_coords, z_coords, BX, BZ, np.array(trajectory)


def run_experiments_and_plot(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    summary = {}

    # Базовый исследуемый соленоид: L = 100 мм, R = 20 мм (D = 40 мм), N = 500, I = 2.0 А
    sol = SolenoidModel(length=0.10, radius=0.02, turns=500, current=2.0, n_phi=120)
    scanner = VirtualScannerDevice(sol, seed=42)

    # -------------------------------------------------------------------------
    # ЭКСПЕРИМЕНТ 1: Контрольный эксперимент (Положительный и Отрицательный контроль)
    # -------------------------------------------------------------------------
    z_pts, bz_ana, bz_num, bz_meas, bz_std = scanner.scan_1d_axis(
        z_min=-0.10, z_max=0.10, step_z=0.002, n_repeats=5
    )

    # Отрицательный контроль (I = 0 А)
    sol_zero = SolenoidModel(length=0.10, radius=0.02, turns=500, current=0.0)
    scanner_zero = VirtualScannerDevice(sol_zero, seed=101)
    _, _, _, bz_zero_meas, _ = scanner_zero.scan_1d_axis(-0.10, 0.10, 0.002, n_repeats=5)

    # Метрики точности (в мТл)
    bz_ana_mT = bz_ana * 1e3
    bz_num_mT = bz_num * 1e3
    bz_meas_mT = bz_meas * 1e3
    bz_zero_mT = bz_zero_meas * 1e3

    rel_err_num = np.max(np.abs(bz_num_mT - bz_ana_mT)) / np.max(bz_ana_mT) * 100.0
    rmse_meas_mT = np.sqrt(np.mean((bz_meas_mT - bz_ana_mT) ** 2))
    rel_err_meas = rmse_meas_mT / np.max(bz_ana_mT) * 100.0
    zero_noise_rms = np.sqrt(np.mean(bz_zero_mT ** 2))

    summary['control_experiment'] = {
        'B0_infinite_mT': round(sol.ideal_infinite_field() * 1e3, 3),
        'B_center_analytical_mT': round(float(sol.analytical_on_axis(0.0) * 1e3), 3),
        'B_center_numerical_mT': round(float(bz_num_mT[len(z_pts) // 2]), 3),
        'B_center_measured_mT': round(float(bz_meas_mT[len(z_pts) // 2]), 3),
        'B_edge_analytical_mT': round(float(sol.analytical_on_axis(0.05) * 1e3), 3),
        'max_rel_error_numerical_percent': round(float(rel_err_num), 4),
        'rmse_virtual_sensor_mT': round(float(rmse_meas_mT), 4),
        'rel_error_virtual_sensor_percent': round(float(rel_err_meas), 3),
        'negative_control_rms_mT': round(float(zero_noise_rms), 4)
    }

    # График 1: Схема сканирования и архитектура виртуального стенда
    _, _, _, _, traj = scanner.scan_2d_grid(-0.035, 0.035, 0.007, -0.08, 0.08, 0.01, realistic=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    # Траектория датчика
    ax.plot(traj[:, 0] * 1000, traj[:, 1] * 1000, '--', color='#1f77b4', alpha=0.65, lw=1.2,
            label='Траектория сканирования («змейка»)')
    ax.scatter(traj[:, 0] * 1000, traj[:, 1] * 1000, s=16, color='#1f77b4', zorder=3,
               label='Узлы сетки измерений $(z_j, x_i)$')

    # Стенки соленоида (верхняя и нижняя обмотки в сечении)
    rect_top = patches.Rectangle((-50, 18.5), 100, 3.0, linewidth=1.2,
                                 edgecolor='#b22222', facecolor='#ff7f50', alpha=0.85,
                                 label='Сечение обмотки соленоида')
    rect_bot = patches.Rectangle((-50, -21.5), 100, 3.0, linewidth=1.2,
                                 edgecolor='#b22222', facecolor='#ff7f50', alpha=0.85)
    ax.add_patch(rect_top)
    ax.add_patch(rect_bot)

    # Показ витков кружками
    loop_z_vis = np.linspace(-48, 48, 22)
    ax.scatter(loop_z_vis, np.full_like(loop_z_vis, 20.0), c='darkred', s=25, zorder=5)
    ax.scatter(loop_z_vis, np.full_like(loop_z_vis, -20.0), c='darkred', s=25, zorder=5)

    # Положение виртуального датчика
    ax.scatter([10], [7], color='#2ca02c', s=90, marker='s', zorder=6,
               label='Виртуальный датчик Холла')
    ax.annotate('Датчик Холла\n(шаг $\\Delta z, \\Delta x$)', xy=(10, 7), xytext=(28, 26),
                arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=1.5),
                fontsize=9, fontweight='bold', color='#1b611b')

    ax.axhline(0, color='gray', linestyle=':', lw=1)
    ax.set_title('Рис. 1. Кинематическая схема 2D-сканирования магнитного поля соленоида', fontsize=11, pad=10)
    ax.set_xlabel('Продольная координата оси $z$, мм', fontsize=10)
    ax.set_ylabel('Поперечная координата $x$, мм', fontsize=10)
    ax.set_xlim(-95, 95)
    ax.set_ylim(-42, 45)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.92)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig1_scanner_scheme.png'))
    plt.close()

    # График 2: Контрольный эксперимент на оси z
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 7.0), gridspec_kw={'height_ratios': [3, 1.35]})
    ax1.plot(z_pts * 1000, bz_ana_mT, '-', color='#d62728', lw=2.2,
             label='Аналитический эталон (формула на оси, положительный контроль)')
    ax1.plot(z_pts * 1000, bz_num_mT, '--', color='#1f77b4', lw=1.8,
             label='Численная модель Био–Савара–Лапласа (без шума)')
    ax1.scatter(z_pts[::2] * 1000, bz_meas_mT[::2], color='#2ca02c', s=22, zorder=4,
                label='Виртуальный датчик Холла (с шумом и АЦП, среднее из 5 изм.)')
    ax1.plot(z_pts * 1000, bz_zero_mT, ':', color='#555555', lw=1.6,
             label='Отрицательный контроль ($I = 0$ А: $B_z = 0,00$ мТл, фоновый шум)')

    # Отметки торцов и центра соленоида, а также нулевого уровня поля
    ax1.axhline(0, color='black', linestyle='-', lw=0.9, alpha=0.7)
    ax1.axvline(0, color='gray', linestyle='--', lw=0.9, alpha=0.7, label='Центр соленоида ($z = 0$ мм, $x = 0$, $y = 0$)')
    ax1.axvline(-50, color='#ff7f0e', linestyle='-.', alpha=0.8, label='Торцы соленоида ($z = \\pm 50$ мм)')
    ax1.axvline(50, color='#ff7f0e', linestyle='-.', alpha=0.8)
    ax1.axhline(sol.ideal_infinite_field() * 1e3, color='purple', linestyle=':', alpha=0.7,
                label=f'Бесконечный соленоид $B_0 = {sol.ideal_infinite_field()*1e3:.2f}$ мТл')

    ax1.set_title('Рис. 2. Верификация модели: распределение индукции $B_z(0, 0, z)$ вдоль оси соленоида', fontsize=11)
    ax1.set_xlabel('Продольная координата вдоль оси соленоида $z$, мм (на центральной оси $x = 0$ мм, $y = 0$ мм)', fontsize=9.5)
    ax1.set_ylabel('Магнитная индукция $B_z$, мТл', fontsize=10)
    ax1.set_xlim(-105, 105)
    ax1.set_xticks([-100, -75, -50, -25, 0, 25, 50, 75, 100])
    ax1.tick_params(labelbottom=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=7.8, framealpha=0.92)

    # Нижняя панель: абсолютная погрешность измерений датчика
    err_meas = bz_meas_mT - bz_ana_mT
    ax2.plot(z_pts * 1000, err_meas, '-', color='#2ca02c', lw=1.2, label='Отклонение датчика $\\Delta B_z = B_{изм} - B_{эт}$')
    ax2.fill_between(z_pts * 1000, -bz_std * 1e3, bz_std * 1e3, color='#2ca02c', alpha=0.2,
                     label='Доверительный коридор $\\pm \\sigma$ (5 повторов)')
    ax2.axhline(0, color='black', lw=0.9)
    ax2.axvline(0, color='gray', linestyle='--', lw=0.8, alpha=0.6)
    ax2.set_xlabel('Продольная координата вдоль оси соленоида $z$, мм ($x = 0$ мм, $y = 0$ мм)', fontsize=9.5)
    ax2.set_ylabel('Погрешность $\\Delta B_z$, мТл', fontsize=9.5)
    ax2.set_xlim(-105, 105)
    ax2.set_xticks([-100, -75, -50, -25, 0, 25, 50, 75, 100])
    ax2.set_ylim(-0.08, 0.08)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig2_axis_verification.png'))
    plt.close()

    # -------------------------------------------------------------------------
    # ЭКСПЕРИМЕНТ 2: Построение полной 2D карты магнитного поля
    # -------------------------------------------------------------------------
    x_grid, z_grid, BX, BZ, _ = scanner.scan_2d_grid(
        x_min=-0.045, x_max=0.045, step_x=0.0015,
        z_min=-0.09, z_max=0.09, step_z=0.002,
        realistic=False
    )
    B_mag_mT = np.sqrt(BX ** 2 + BZ ** 2) * 1e3
    # Ограничим пики непосредственно в точках провода для наглядной цветовой шкалы
    B_mag_clipped = np.clip(B_mag_mT, 0, 14.5)

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    Z_mesh, X_mesh = np.meshgrid(z_grid * 1000, x_grid * 1000)

    pcm = ax.pcolormesh(Z_mesh, X_mesh, B_mag_clipped, shading='gouraud', cmap='viridis')
    cbar = fig.colorbar(pcm, ax=ax, pad=0.02)
    cbar.set_label('Модуль магнитной индукции $|B|$, мТл', fontsize=10)

    # Линии магнитного поля (streamplot)
    ax.streamplot(z_grid * 1000, x_grid * 1000, BZ * 1e3, BX * 1e3,
                  color='white', linewidth=0.85, density=1.2, arrowsize=1.0)

    # Обмотка соленоида
    ax.plot([-50, 50], [20, 20], color='#ff4500', lw=4, label='Обмотка соленоида ($R = 20$ мм, $L = 100$ мм)')
    ax.plot([-50, 50], [-20, -20], color='#ff4500', lw=4)

    ax.set_title('Рис. 3. Двумерная топографическая карта магнитного поля $|B(x, z)|$ и силовые линии', fontsize=11)
    ax.set_xlabel('Продольная координата $z$, мм', fontsize=10)
    ax.set_ylabel('Поперечная координата $x$, мм', fontsize=10)
    ax.set_xlim(-90, 90)
    ax.set_ylim(-45, 45)
    ax.legend(loc='upper right', fontsize=8.5, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig3_2d_heatmap.png'))
    plt.close()

    # -------------------------------------------------------------------------
    # ЭКСПЕРИМЕНТ 3: Поперечные профили поля и краевой эффект
    # -------------------------------------------------------------------------
    z_slices_mm = [0, 25, 40, 50, 65]
    x_prof = np.linspace(-0.04, 0.04, 161)

    fig, ax = plt.subplots(figsize=(8.5, 5))
    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
    for z_mm, col in zip(z_slices_mm, colors):
        z_val = z_mm / 1000.0
        bz_prof = [sol.calc_field_point(x_val, z_val)[1] * 1e3 for x_val in x_prof]
        ax.plot(x_prof * 1000, bz_prof, lw=2, color=col, label=f'Сечение $z = {z_mm}$ мм')

    ax.axvline(-20, color='gray', linestyle='--', lw=1.2, label='Стенка катушки ($x = \\pm 20$ мм)')
    ax.axvline(20, color='gray', linestyle='--', lw=1.2)
    ax.axhline(0, color='black', lw=0.8, alpha=0.6)

    ax.set_title('Рис. 4. Радиальные профили продольной индукции $B_z(x)$ в различных сечениях', fontsize=11)
    ax.set_xlabel('Поперечная координата $x$, мм', fontsize=10)
    ax.set_ylabel('Продольная компонента индукции $B_z$, мТл', fontsize=10)
    ax.set_ylim(-3.5, 16.0)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig4_radial_profiles.png'))
    plt.close()

    # -------------------------------------------------------------------------
    # ЭКСПЕРИМЕНТ 4: Влияние геометрии соленоида (L/D) на зону однородности поля
    # Проверка гипотезы исследования!
    # -------------------------------------------------------------------------
    ratios_LD = [1.0, 2.5, 5.0, 10.0]
    radius_fixed = 0.02  # D = 40 мм
    n_density = 5000.0   # постоянная плотность намотки 5000 витков/м
    current_fixed = 2.0

    uniformity_results = []
    fig, ax = plt.subplots(figsize=(9, 5.2))
    u_colors = ['#e41a1c', '#ff7f00', '#377eb8', '#4daf4a']

    z_norm = np.linspace(-1.0, 1.0, 401)  # нормированная координата z / (L/2)

    for ratio, col in zip(ratios_LD, u_colors):
        L_val = ratio * (2.0 * radius_fixed)
        N_val = int(round(n_density * L_val))
        s_model = SolenoidModel(length=L_val, radius=radius_fixed, turns=N_val, current=current_fixed)

        z_real = z_norm * (L_val / 2.0)
        bz_vals = s_model.analytical_on_axis(z_real)
        b_center = bz_vals[len(z_norm) // 2]
        b_inf = s_model.ideal_infinite_field()

        # Доля длины соленоида, где поле отличается от центрального не более чем на 5% и на 1%
        within_5pct = np.abs(bz_vals - b_center) / b_center <= 0.05
        within_1pct = np.abs(bz_vals - b_center) / b_center <= 0.01

        zone_5pct = float(np.sum(within_5pct) / len(z_norm) * 100.0)
        zone_1pct = float(np.sum(within_1pct) / len(z_norm) * 100.0)

        uniformity_results.append({
            'L_to_D': ratio,
            'L_mm': round(L_val * 1000, 1),
            'N_turns': N_val,
            'B_center_mT': round(float(b_center * 1e3), 3),
            'B_center_to_B0_pct': round(float(b_center / b_inf * 100.0), 2),
            'uniform_zone_5pct_of_L': round(zone_5pct, 1),
            'uniform_zone_1pct_of_L': round(zone_1pct, 1),
            'B_edge_to_B_center_pct': round(float(s_model.analytical_on_axis(L_val / 2.0) / b_center * 100.0), 2)
        })

        ax.plot(z_norm, bz_vals / b_center, lw=2.2, color=col,
                label=f'$L/D = {ratio}$ (зона однородности $\\pm 5\\%$: {zone_5pct:.1f}% длины)')

    ax.axhline(0.95, color='gray', linestyle='--', lw=1.2, label='Граница однородности $0,95 \\cdot B(0)$ (отклонение 5%)')
    ax.axhline(0.99, color='black', linestyle=':', lw=1.0, label='Граница высокой однородности $0,99 \\cdot B(0)$ (отклонение 1%)')
    ax.axvline(-1.0, color='gray', alpha=0.4)
    ax.axvline(1.0, color='gray', alpha=0.4)

    ax.set_title('Рис. 5. Влияние отношения длины к диаметру $L/D$ на размер плато однородного поля', fontsize=11)
    ax.set_xlabel('Нормированная продольная координата $2z / L$ (торцы катушки при $\\pm 1$)', fontsize=10)
    ax.set_ylabel('Относительная индукция $B_z(z) / B_z(0)$', fontsize=10)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(0.45, 1.04)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower center', fontsize=8.5, framealpha=0.95)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig5_uniformity_study.png'))
    plt.close()

    summary['uniformity_study'] = uniformity_results

    # -------------------------------------------------------------------------
    # ЭКСПЕРИМЕНТ 5: Влияние шага дискретизации сканера на точность карты поля
    # -------------------------------------------------------------------------
    steps_mm = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    z_fine = np.linspace(-0.10, 0.10, 1001)
    bz_fine = sol.analytical_on_axis(z_fine) * 1e3

    step_study = []
    for st_mm in steps_mm:
        st_m = st_mm / 1000.0
        z_coarse = np.arange(-0.10, 0.10 + 0.5 * st_m, st_m)
        bz_coarse = sol.analytical_on_axis(z_coarse) * 1e3
        # Линейная интерполяция восстановленного профиля на густую сетку
        bz_interp = np.interp(z_fine, z_coarse, bz_coarse)
        max_interp_err = float(np.max(np.abs(bz_interp - bz_fine)) / np.max(bz_fine) * 100.0)
        n_points_1d = len(z_coarse)
        step_study.append({
            'step_mm': st_mm,
            'n_points_1d': n_points_1d,
            'max_interpolation_error_pct': round(max_interp_err, 3)
        })

    summary['step_discretization_study'] = step_study

    with open(os.path.join(out_dir, 'experiment_results.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Все эксперименты успешно выполнены! Сводка результатов:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    run_experiments_and_plot(output_directory)
