#!/usr/bin/env python3
"""
EMF Visualizer
==============
Interactive plot of the EMF induced by a rotating coil in a uniform magnetic field.

    EMF(t) = N ┬À B ┬À A ┬À ¤ë ┬À sin(¤ë ┬À t)

Sliders let you adjust:
  N  ÔÇô number of turns
  B  ÔÇô magnetic flux density (Tesla)
  A  ÔÇô coil area (m┬▓)
  ¤ë  ÔÇô angular velocity (rad/s)

Requirements: matplotlib, numpy
    pip install matplotlib numpy
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# ÔöÇÔöÇ time axis ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
T_MAX = 2.0          # seconds shown on the x-axis
N_POINTS = 1000
t = np.linspace(0, T_MAX, N_POINTS)

# ÔöÇÔöÇ default parameter values ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
N0 = 100             # number of turns
B0 = 0.5             # Tesla
A0 = 0.01            # m┬▓
OMEGA0 = 2 * np.pi   # rad/s  (1 Hz)


def emf(t, N, B, A, omega):
    """Instantaneous EMF of a rotating coil: ╬Á = N┬ÀB┬ÀA┬À¤ë┬Àsin(¤ë┬Àt)."""
    return N * B * A * omega * np.sin(omega * t)


# ÔöÇÔöÇ figure layout ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
fig, ax = plt.subplots(figsize=(9, 5))
plt.subplots_adjust(left=0.1, bottom=0.38, right=0.95, top=0.92)

emf_values = emf(t, N0, B0, A0, OMEGA0)
(line,) = ax.plot(t, emf_values, color="royalblue", linewidth=2)

ax.set_xlabel("Time  (s)", fontsize=11)
ax.set_ylabel("EMF  (V)", fontsize=11)
ax.set_title("Induced EMF of a Rotating Coil\n"
             r"$\varepsilon(t) = N \cdot B \cdot A \cdot \omega \cdot \sin(\omega t)$",
             fontsize=12)
ax.set_xlim(0, T_MAX)
ax.grid(True, linestyle="--", alpha=0.5)

# ÔöÇÔöÇ sliders ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
SLIDER_COLOR = "lightsteelblue"

ax_N     = plt.axes([0.15, 0.26, 0.70, 0.03], facecolor=SLIDER_COLOR)
ax_B     = plt.axes([0.15, 0.20, 0.70, 0.03], facecolor=SLIDER_COLOR)
ax_A     = plt.axes([0.15, 0.14, 0.70, 0.03], facecolor=SLIDER_COLOR)
ax_omega = plt.axes([0.15, 0.08, 0.70, 0.03], facecolor=SLIDER_COLOR)

slider_N     = Slider(ax_N,     "N  (turns)", 1,    500,  valinit=N0,     valstep=1)
slider_B     = Slider(ax_B,     "B  (T)",     0.01, 5.0,  valinit=B0)
slider_A     = Slider(ax_A,     "A  (m┬▓)",    0.001, 0.5, valinit=A0)
slider_omega = Slider(ax_omega, "¤ë  (rad/s)", 1,    100,  valinit=OMEGA0)


def update(_):
    N     = slider_N.val
    B     = slider_B.val
    A     = slider_A.val
    omega = slider_omega.val

    new_emf = emf(t, N, B, A, omega)
    line.set_ydata(new_emf)

    # auto-scale y-axis to peak value
    peak = max(abs(new_emf.max()), abs(new_emf.min())) or 1
    ax.set_ylim(-peak * 1.15, peak * 1.15)
    fig.canvas.draw_idle()


for s in (slider_N, slider_B, slider_A, slider_omega):
    s.on_changed(update)

# initialize y-limits
update(None)

plt.show()
