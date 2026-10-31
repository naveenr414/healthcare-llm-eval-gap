"""Plot complementary Bean et al. mechanism contrasts.

This figure is intentionally different from the paper's pull figure. Rather
than repeating the aggregate evaluation--deployment gap, it puts condition
identification and disposition side by side and displays the intermediate
comparisons used to diagnose their different failure modes.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / 'plots'

INK, MUTED, GRID, SURFACE = '#0b0b0b', '#898781', '#e1e0d9', '#ffffff'
BLUE = '#477fc9'
LIGHT_BLUE = '#b8cde6'
RED = '#e14949'
PEACH = '#efcbb8'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 10,
    'text.color': INK,
    'axes.edgecolor': '#c3c2b7',
    'axes.labelcolor': INK,
    'axes.labelsize': 10,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'figure.facecolor': SURFACE,
    'axes.facecolor': SURFACE,
    'savefig.facecolor': SURFACE,
    'axes.linewidth': 0.7,
    'pdf.fonttype': 42,
})


def strip_axes(ax, keep=('left', 'bottom')):
    """Hide unnecessary spines and retain the light paper-style axes."""
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)
    ax.tick_params(length=3, width=0.6)


def label_bars(ax, bars, values):
    """Place percentage labels above a set of bars."""
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2.0,
                f'{value:.1f}%', ha='center', va='bottom',
                fontsize=9, fontweight='bold')


def make_figure():
    """Draw outcome-specific intermediate comparisons."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.9), sharey=True)

    # Condition identification: the rewritten disclosed-information result
    # is a diagnostic comparison, while the final-turn and participant values
    # are the real-conversation comparisons.
    condition_values = [94.7, 91.1, 64.9, 35.7]
    condition_colors = [BLUE, PEACH, LIGHT_BLUE, RED]
    x = np.arange(len(condition_values))
    bars = ax.bar(x, condition_values, width=0.58, color=condition_colors,
                  edgecolor='none')
    label_bars(ax, bars, condition_values)
    ax.set_xticks(x)
    ax.set_xticklabels(['Direct\nevaluation', 'Rewritten\ndisclosed info',
                        'GPT-4o\nfinal turn', 'Participant'])
    ax.set_title('Conditions', loc='left', fontweight='bold', fontsize=11, pad=10)
    ax.set_ylabel('accuracy')
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    strip_axes(ax)

    # Disposition: the directly scored model-from-disclosed-information value
    # is the intermediate comparison available for this outcome. There is no
    # stored final-turn disposition estimate used here.
    disposition_values = [58.7, 46.9, 43.8]
    disposition_colors = [BLUE, LIGHT_BLUE, RED]
    x2 = np.arange(len(disposition_values))
    bars = ax2.bar(x2, disposition_values, width=0.58, color=disposition_colors,
                   edgecolor='none')
    label_bars(ax2, bars, disposition_values)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(['Direct\nevaluation', 'Model on disclosed\ninformation',
                         'Participant'])
    ax2.set_title('Dispositions', loc='left', fontweight='bold', fontsize=11, pad=10)
    ax2.set_ylim(0, 108)
    ax2.set_yticks([0, 25, 50, 75, 100])
    ax2.grid(axis='y', color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    strip_axes(ax2)

    fig.tight_layout(pad=0.55, w_pad=0.9)
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS / 'bean_mechanism_contrasts.pdf', bbox_inches='tight')
    fig.savefig(PLOTS / 'bean_mechanism_contrasts.png', dpi=220, bbox_inches='tight')
    plt.close(fig)
    print('  wrote plots/bean_mechanism_contrasts.pdf and .png')


if __name__ == '__main__':
    make_figure()
