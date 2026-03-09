# -*- coding: utf-8 -*-
"""
Schema delle relazioni tra agenti del modello MAIO2.
Layout a stella con label esplicite in posizioni fisse non sovrapposte.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

fig, ax = plt.subplots(figsize=(24, 18))
ax.set_xlim(0, 24)
ax.set_ylim(0, 18)
ax.axis('off')
fig.patch.set_facecolor('#0F1117')
ax.set_facecolor('#0F1117')

# ─── Posizioni nodi ──────────────────────────────────────────────────────────
pos = {
    'Household':  (12.0, 15.5),   # top center
    'Firm':       ( 3.0,  9.0),   # left
    'LocalKAU':   (12.0,  9.0),   # center
    'Bank':       (21.0,  9.0),   # right
    'Government': ( 5.5,  2.5),   # bottom left
    'RoW':        (19.5,  2.5),   # bottom right
}

col = {
    'Household':  '#2980B9',
    'Firm':       '#D35400',
    'LocalKAU':   '#27AE60',
    'Bank':       '#8E44AD',
    'Government': '#C0392B',
    'RoW':        '#16A085',
}

BW, BH = 3.2, 1.1

def box(ax, name):
    x, y = pos[name]
    p = FancyBboxPatch((x-BW/2, y-BH/2), BW, BH,
                       boxstyle="round,pad=0.18",
                       fc=col[name], ec='white', lw=2.8, zorder=5, alpha=0.97)
    ax.add_patch(p)
    ax.text(x, y, name, ha='center', va='center',
            fontsize=14, fontweight='bold', color='white', zorder=6)

for n in pos:
    box(ax, n)

# ─── Funzione freccia ────────────────────────────────────────────────────────
def arr(ax, s, d, lbl, c, os=(0,0), od=(0,0), rad=0.0,
        lw=1.9, fs=8.3, label_xy=None):
    x1,y1 = pos[s][0]+os[0], pos[s][1]+os[1]
    x2,y2 = pos[d][0]+od[0], pos[d][1]+od[1]
    a = FancyArrowPatch((x1,y1),(x2,y2), arrowstyle='->',
                        color=c, lw=lw,
                        connectionstyle=f'arc3,rad={rad}',
                        mutation_scale=16, zorder=4, alpha=0.88)
    ax.add_patch(a)
    if label_xy:
        tx, ty = label_xy
    else:
        tx = (x1+x2)/2
        ty = (y1+y2)/2
    ax.text(tx, ty, lbl, ha='center', va='center', fontsize=fs, color='white',
            bbox=dict(boxstyle='round,pad=0.24', fc=c, ec='none', alpha=0.93),
            zorder=7)

# ════════════════════════════════════════════════════════════════════
#  FLUSSI – con label_xy espliciti per evitare sovrapposizioni
# ════════════════════════════════════════════════════════════════════

# ── HH → LocalKAU : consumo beni dom. (sinistra del collegamento) ────────────
arr(ax,'Household','LocalKAU','Consumo\nbeni dom.', col['Household'],
    os=(-0.4,-0.55), od=(-0.4,0.55), rad=0.12,
    label_xy=(9.5, 12.7))

# ── Firm → HH : salari ──────────────────────────────────────────────────────
arr(ax,'Firm','Household','Salari', col['Firm'],
    os=(0.2,0.55), od=(-1.8,-0.55), rad=0.2,
    label_xy=(5.5, 13.5))

# ── Firm → HH : dividendi ───────────────────────────────────────────────────
arr(ax,'Firm','Household','Dividendi Firm', col['Firm'],
    os=(0.7,0.4), od=(-1.3,-0.55), rad=-0.05,
    label_xy=(7.8, 13.2))

# ── HH → GOV : tasse ────────────────────────────────────────────────────────
arr(ax,'Household','Government','Tasse\n(lavoro+div.)', col['Household'],
    os=(-0.5,-0.55), od=(0.5,0.55), rad=-0.12,
    label_xy=(7.0, 10.0))

# ── GOV → HH : sussidi ──────────────────────────────────────────────────────
arr(ax,'Government','Household','Sussidi &\ntrasferimenti', col['Government'],
    os=(1.0,0.55), od=(-1.2,-0.55), rad=0.12,
    label_xy=(10.0, 10.5))

# ── GOV → LocalKAU : spesa pubblica ─────────────────────────────────────────
arr(ax,'Government','LocalKAU','Spesa\npubblica', col['Government'],
    os=(1.4,0.3), od=(-0.4,-0.55), rad=0.05,
    label_xy=(9.0, 5.8))

# ── GOV → RoW : import gov ───────────────────────────────────────────────────
arr(ax,'Government','RoW','Import gov', col['Government'],
    os=(1.5,0.2), od=(-1.5,0.2), rad=0.0,
    label_xy=(12.5, 3.2))

# ── HH → RoW : import privato ───────────────────────────────────────────────
arr(ax,'Household','RoW','Import\nprivato', col['Household'],
    os=(1.2,-0.3), od=(-0.3,0.55), rad=-0.18,
    label_xy=(17.5, 9.5))

# ── RoW → LocalKAU : export ──────────────────────────────────────────────────
arr(ax,'RoW','LocalKAU','Export\n(RoW←KAU dom.)', col['RoW'],
    os=(-1.5,0.5), od=(0.8,-0.55), rad=0.15,
    label_xy=(16.5, 6.5))

# ── Firm → LocalKAU : cassa / coord. ─────────────────────────────────────────
arr(ax,'Firm','LocalKAU','Cassa /\ncoord.', col['Firm'],
    os=(1.3,0.3), od=(-1.8,0.3), rad=0.0,
    label_xy=(7.5, 10.0))

# ── LocalKAU → Firm : utili netti ────────────────────────────────────────────
arr(ax,'LocalKAU','Firm','Utili\nnetti', col['LocalKAU'],
    os=(-1.8,-0.3), od=(1.3,-0.3), rad=0.3,
    label_xy=(7.5, 7.5))

# ── Firm → Bank : rimborso + interessi ───────────────────────────────────────
arr(ax,'Firm','Bank','Rimborso cap.\n+ interessi', '#7F8C8D',
    os=(1.3,0.0), od=(-1.3,0.0), rad=0.35,
    lw=1.6, fs=7.8,
    label_xy=(12.0, 11.5))

# ── Bank → Firm : prestito concesso ──────────────────────────────────────────
arr(ax,'Bank','Firm','Prestito\nconcesso', col['Bank'],
    os=(-1.3,-0.3), od=(1.3,-0.3), rad=0.0,
    label_xy=(12.0, 7.2))

# ── Bank → HH : dividendi ────────────────────────────────────────────────────
arr(ax,'Bank','Household','Dividendi Bank\n(da interessi)', col['Bank'],
    os=(-0.8,0.55), od=(1.8,-0.55), rad=-0.15,
    label_xy=(17.5, 13.0))

# ── LocalKAU loop : beni intermedi ───────────────────────────────────────────
theta = np.linspace(0.1, np.pi*2 - 0.1, 100)
lx = pos['LocalKAU'][0] + 1.5*np.cos(theta)
ly = pos['LocalKAU'][1] - 1.5 + 1.0*np.sin(theta)
ax.plot(lx, ly, color=col['LocalKAU'], lw=1.9, alpha=0.82, zorder=4)
dx = lx[1]-lx[0]; dy = ly[1]-ly[0]
ax.annotate('', xy=(lx[0], ly[0]),
            xytext=(lx[0]-dx*4, ly[0]-dy*4),
            arrowprops=dict(arrowstyle='->', color=col['LocalKAU'], lw=1.9), zorder=4)
ax.text(pos['LocalKAU'][0], pos['LocalKAU'][1]-3.2,
        'Beni intermedi (KAU→KAU)', ha='center', va='center',
        fontsize=8.3, color='white',
        bbox=dict(boxstyle='round,pad=0.24', fc=col['LocalKAU'], ec='none', alpha=0.93),
        zorder=7)

# ════════════════════════════════════════════════════════════════════
#  LEGENDA + TITOLO
# ════════════════════════════════════════════════════════════════════
items = [
    mpatches.Patch(color=col['Household'],  label='Household – famiglie consumatrici'),
    mpatches.Patch(color=col['Firm'],       label='Firm – impresa (holding finanziaria)'),
    mpatches.Patch(color=col['LocalKAU'],   label='LocalKAU – unità di attività economica (KAU)'),
    mpatches.Patch(color=col['Bank'],       label='Bank – settore bancario'),
    mpatches.Patch(color=col['Government'], label='Government – settore pubblico'),
    mpatches.Patch(color=col['RoW'],        label='RoW – Resto del Mondo (import/export)'),
]
leg = ax.legend(handles=items, loc='lower left', fontsize=10,
                facecolor='#1E1E2E', edgecolor='#555', labelcolor='white',
                framealpha=0.92, title='Agenti del modello', title_fontsize=11,
                handlelength=1.2)
leg.get_title().set_color('white')

ax.set_title('Schema delle relazioni tra agenti – Modello MAIO2\n'
             'Flussi monetari (→ denaro) e reali (→ beni/servizi) tra settori istituzionali',
             fontsize=16, fontweight='bold', pad=20, color='white')

plt.tight_layout()
plt.savefig('schema_agenti.png', dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("Schema salvato in schema_agenti.png")
