# -*- coding: utf-8 -*-
"""
Created on Thu Nov 27 02:26:43 2025

@author: frado
"""

import numpy as np
import os
from NewExperimenter import Experimenter

Galileo = Experimenter()

# -----------------------
# 1) Struttura di base
# -----------------------
seed = 32
n_sectors = 15  # numero settori
n_KAUs4sector = [1] * n_sectors  # numero di KAU per settore
n_KAUs = sum(n_KAUs4sector)
n_firms = n_sectors # numero imprese
n_households = 2000 # numero famiglie

# -----------------------
# 2) Matrice tecnica domestica C (15×15)
# -----------------------
C = np.array([
    [0.05635661, 0.03917081, 0.00310933, 0.00339481, 0.00284872, 0.00087681, 0.0,        0.00072567, 0.00057172, 0.00264441, 0.00295318, 0.00402152, 0.00020936, 0.00402077, 0.00236178],
    [0.00641337, 0.00467569, 0.00381971, 0.00399480, 0.00724028, 0.00025609, 0.00000805, 0.00025651, 0.00092152, 0.00295016, 0.00392139, 0.00421371, 0.01460948, 0.00172832, 0.00224597],
    [0.00028321, 0.00026586, 0.00001667, 0.00000035, 0.00003700, 0.00007936, 0.00001447, 0.00006257, 0.00002441, 0.00010814, 0.00016737, 0.00605714, 0.00003024, 0.00092521, 0.00055428],
    [0.00034328, 0.00035118, 0.00001945, 0.00000040, 0.00006863, 0.00009616, 0.00001753, 0.00007595, 0.00002836, 0.00012973, 0.00023345, 0.01326232, 0.00003420, 0.00134906, 0.00039459],
    [0.00330574, 0.00390687, 0.00535551, 0.00569178, 0.15251887, 0.00369126, 0.00124442, 0.00148847, 0.01060983, 0.00398909, 0.01137838, 0.00535794, 0.00044897, 0.00382481, 0.00527995],
    [0.00862466, 0.00792029, 0.00903639, 0.00976958, 0.00948060, 0.08330571, 0.13699003, 0.05325007, 0.02419658, 0.01373787, 0.01034056, 0.01019238, 0.00445723, 0.00780759, 0.01316900],
    [0.00101342, 0.00115167, 0.00032424, 0.00026578, 0.00471763, 0.00196366, 0.04788840, 0.00196227, 0.00257380, 0.00168405, 0.00200989, 0.00053215, 0.00034208, 0.00135796, 0.00183850],
    [0.00348644, 0.00257954, 0.00156254, 0.00153595, 0.00214725, 0.13834451, 0.21483953, 0.05216208, 0.00226842, 0.00680497, 0.00625291, 0.00187615, 0.00246836, 0.00234027, 0.00560654],
    [0.00984715, 0.01107628, 0.00906459, 0.00987867, 0.00819024, 0.02135421, 0.04310214, 0.02816224, 0.00968095, 0.03365535, 0.02108980, 0.00970994, 0.01490693, 0.01227089, 0.02206716],
    [0.00698224, 0.00678963, 0.01322022, 0.01441022, 0.00810853, 0.03601617, 0.01491312, 0.02740305, 0.00248157, 0.12960924, 0.02390534, 0.01381160, 0.01638754, 0.00512649, 0.00880642],
    [0.02930339, 0.03744343, 0.04167248, 0.04512208, 0.08171335, 0.03433223, 0.00970628, 0.05902225, 0.02687033, 0.12270662, 0.16372155, 0.04419021, 0.08227439, 0.04071788, 0.05227864],
    [0.00588698, 0.00647367, 0.00035173, 0.00000914, 0.00129173, 0.00179497, 0.00032728, 0.00141805, 0.00052857, 0.00211526, 0.00461657, 0.22496454, 0.00068260, 0.03879143, 0.00720129],
    [0.00189595, 0.00249550, 0.21016664, 0.45970715, 0.00141297, 0.00088427, 0.00021701, 0.00087275, 0.00035698, 0.00146085, 0.00294472, 0.06874739, 0.00659870, 0.01171492, 0.00411151],
    [0.01447667, 0.01970472, 0.00772089, 0.00649567, 0.05107095, 0.00060390, 0.00001267, 0.00467853, 0.00197940, 0.00453939, 0.01587506, 0.01575084, 0.00633070, 0.10861069, 0.01705305],
    [0.27660836, 0.26612267, 0.10660618, 0.11694219, 0.16279672, 0.02865157, 0.00921244, 0.11418935, 0.03122069, 0.12834790, 0.19105433, 0.15259144, 0.25218719, 0.20367991, 0.24710283]
], dtype=float)

# alpha famiglie
alpha_H = np.array([0.00091, 0.00036, 0.00032, 0.00035, 0.00903,
                    0.01189, 0.01821, 0.00327, 0.19716, 0.00006,
                    0.01774, 0.01596, 0.00003, 0.05012, 0.67459], dtype=float) # Households

# alpha RoW
alpha_R = np.array([0.23719, 0.0000005, 0.00001061, 0.00000604, 0.00159955,
                    0.00195773, 0.00242505, 0.00006525, 0.00704757, 0.00433677,
                    0.01672453, 0.00017495, 0.00000003, 0.01801484, 0.71044658], dtype=float) # RoW

# alpha governo
alpha_Gov = {
    'P1': 0.0, 'P2': 0.0003425, 'P3': 0.0000036, 'P4': 0.0000001, 'P5': 0.0010357,
    'P6': 0.0002660, 'P7': 0.0, 'P8': 0.0000258, 'P9': 0.0, 'P10': 0.0022456,
    'P11': 0.0052978, 'P12': 0.0008367, 'P13': 0.0001137, 'P14': 0.0000383, 'P15': 0.9897942
}   # Governo

# RoW: Y_R e c_R
Y_R = 2145707.18/12
c_R = 0.10

# Imposte e trasferimenti
tax_rates = {
    'VAT': {'P1': 0.0, 'P2': 0.0, 'P3': 0.0, 'P4': 0.0, 'P5': 0.0, 'P6': 0.0, 'P7': 0.0, 'P8': 0.0, 'P9': 0.0, 'P10': 0.0, 'P11': 0.0, 'P12': 0.0, 'P13': 0.0, 'P14': 0.0, 'P15': 0.0}, #0.2
    'corporate': 0.0, #0.25
    'labor': {float('inf'): 0.25}, #0.1
    'dividends': 0.2, #0.05
}
transfer_fraction = 0.0
ub_fraction = 0.0

# salari e coefficiente di lavoro (scegliere valori adatti per avere monte salari e tasso di disoccupazione desiderati)
wages = np.array([40, 40, 5, 1, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40], dtype=float) 
labor_tech_coeff = np.array([0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085, 0.0085], dtype=float)

# preferenze famiglie (settoriali -> già n=3)
alpha = alpha_H.reshape(n_sectors, 1) @ np.ones((1, n_households))
alpha = alpha / alpha.sum(axis=0, keepdims=True)          # normalizza per colonna

# ricchezza-target (lambdaT) e propensione a consumare della ricchezza (csi)
lambda_groups = [0.0, 2.39, 4.01, 4.92, 9.92]
lambdaT = np.concatenate([np.full(400, v, dtype=float) for v in lambda_groups])
assert len(lambdaT) == n_households
csi = np.full(n_households, 0.02, float)                        

# Mapping venditori
vec = np.arange(n_sectors).reshape(n_sectors, 1)
households_sellers = np.tile(vec, (1, n_households))
KAUs_sellers      = np.tile(vec, (1, n_KAUs))

exp = Experimenter()

Y_scale = 1653577.0/12 # (GDP italiano mensile in mln di euro)

params, q, KAU_workers = exp.create_initcond_Baseline(
    seed=seed,
    Y=Y_scale,
    n_firms=n_firms,
    n_KAUs4sector=n_KAUs4sector,
    C=C,
    wages=wages,
    labor_tech_coeff=labor_tech_coeff,
    n_households=n_households,
    lambdaT=lambdaT,
    csi=csi,
    alpha=alpha,
    households_sellers=households_sellers,
    KAUs_sellers=KAUs_sellers,
    rat_threshold=1,            # alto -> cambiano seller solo se fortemente razionati
    n_indep_periods= 150,       # segliere in modo da non avere razionameni
    shocks={'active': False},
)

# Dopo create_initcond_Baseline(...)
params['localKAUs_var']['target_speed']        = np.zeros(n_KAUs)     # niente drift verso i target
params['localKAUs_var']['markup_speed']        = np.zeros(n_KAUs)          # prezzi fissi

# valori iniziali di stock di intermedi per le commodity più critiche, forzati a valori elevati per non avere razionamenti
params['localKAUs_var']['commodities_stock'][0]['P1'] = 90000.0
params['localKAUs_var']['commodities_stock'][1]['P2'] = 90000.0
params['localKAUs_var']['commodities_stock'][2]['P3'] = 90000.0
params['localKAUs_var']['commodities_stock'][3]['P4'] = 90000.0

# ==== B) EXTRA DOMANDA: EXPORT (RoW) ====
# ricostruisco la C (i×j) dai tech_coeff che sono già in params
n = n_KAUs
names = params['commodities_list']
Cmat = np.zeros((n, n), float)
for j in range(n):
    for i, pname in enumerate(names):
        Cmat[i, j] = float(params['localKAUs_var']['tech_coeff'][j][pname])

I = np.eye(n)
L = np.linalg.inv(I - Cmat)

# final demand estera in valore (p=1 => quantità)
X_tot = float(Y_R * c_R)
x_sh = (alpha_R / alpha_R.sum()).reshape(n, 1)   # shares normalizzati
F_X  = x_sh * X_tot                               # (n×1)

# extra output per soddisfare l'export
dx = L.dot(F_X)                                   # (n×1)

# la domanda “di vendita” del j-esimo settore è (1 - a_jj) * x_j
extra_prev = (1.0 - np.diag(Cmat)) * dx.reshape(n)

for j in range(n):
    params['localKAUs_var']['previous_demand'][j] += float(extra_prev[j])

# Coefficienti di capitale
B_cap = np.array([
    [0.093, 0.093, 10, 5, 0.043, 0.063, 0.063, 0.063, 0.044, 0.021, 0.063, 1.266, 0.071, 0.111, 0.098],
    [0.093, 0.093, 10, 5, 0.043, 0.063, 0.063, 0.063, 0.044, 0.021, 0.063, 1.266, 0.071, 0.111, 0.098],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.066, 0.066, 1.25, 2.5, 0.056, 0.1, 0.1, 0.1, 1.667, 0.052, 0.1, 0.365, 0.129, 0.183, 0.134],
    [0.074, 0.074, 0.137, 0.526, 0.002, 0.044, 0.044, 0.044, 0.012, 0.047, 0.044, 0.037, 0.02, 0.01, 0.009],
    [0.074, 0.074, 0.137, 0.526, 0.002, 0.044, 0.044, 0.044, 0.012, 0.047, 0.044, 0.037, 0.02, 0.01, 0.009],
    [0.074, 0.074, 0.137, 0.526, 0.002, 0.044, 0.044, 0.044, 0.012, 0.047, 0.044, 0.037, 0.02, 0.01, 0.009],
    [0.074, 0.074, 0.137, 0.526, 0.002, 0.044, 0.044, 0.044, 0.012, 0.047, 0.044, 0.037, 0.02, 0.01, 0.009],
    [0.008, 0.008, 0.137, 0.833, 0.002, 0.031, 0.031, 0.031, 0.031, 0.01, 0.083, 0.031, 0.062, 0.003, 0.004],
    [0.074, 0.074, 0.137, 0.526, 0.002, 0.044, 0.044, 0.044, 0.012, 0.047, 0.044, 0.037, 0.02, 0.01, 0.009],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.007, 0.007, 0.0, 0.0, 0.004, 0.037, 0.037, 0.037, 0.015, 0.012, 0.037, 0.072, 0.006, 0.008, 0.008]
], dtype=float)


# Tassi di deprezzamento
D_cap = np.array([
    [0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012],
    [0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012, 0.012],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025, 0.0025],
    [0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018],
    [0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018],
    [0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018],
    [0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018],
    [0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032, 0.032],
    [0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.017, 0.017, 0.0, 0.0, 0.016, 0.017, 0.017, 0.017, 0.015, 0.017, 0.017, 0.015, 0.016, 0.016, 0.016]
], dtype=float)

# Target di utilizzo capacità
u_star = 0.75

# --- Scrittura nei params e stock iniziali coerenti con u* ---
params['localKAUs_var']['capital_coeff'].clear()
params['localKAUs_var']['capital_depreciation'].clear()
params['localKAUs_var']['capital_stocks'].clear()
params['localKAUs_var']['target_capacity_utilization'] = np.ones(n_KAUs) * u_star

names = params['commodities_list']  # ['P1',...,'P15']

for j in range(n_KAUs):
    cap_coeff = {}
    cap_depr  = {}
    cap_stock = {}
    prev = params['localKAUs_var']['previous_demand'][j]
    # q[j,0] è la produzione “baseline” della KAU j, usata per calibrare gli stock
    qj0 = float(q[j, 0])
    cuj = float(u_star)
    
    # for w in range(n):
    #     prev = params['localKAUs_var']['previous_demand'][w]
    for i, pname in enumerate(names):
        b_ij = float(B_cap[i, j])
        d_ij = float(D_cap[i, j]) if not np.isnan(D_cap[i, j]) else 0.0
        cap_coeff[pname] = b_ij
        cap_depr[pname]  = max(0.0, d_ij)
        
        cap_stock[pname] = ((prev / cuj) * b_ij) if b_ij > 0.0 else 0.0
        
    
    params['localKAUs_var']['capital_coeff'].append(cap_coeff)
    params['localKAUs_var']['capital_depreciation'].append(cap_depr)
    params['localKAUs_var']['capital_stocks'].append(cap_stock)


params['import_policy'] = {
    # quote domestiche (0..1)
    # puoi passare uno scalare (es. 0.8) oppure un dict {'P1':0.8,'P2':0.8,'P3':0.8}
    'qD_final':        {'P1': 0.64, 'P2': 1.0, 'P3': 0.87, 'P4': 0.97, 'P5': 1.0, 'P6': 1.0, 'P7': 1.0, 'P8': 1.0, 'P9': 1.0, 'P10': 1.0, 'P11': 1.0, 'P12': 0.98, 'P13': 1.0, 'P14': 0.92, 'P15': 0.86},  # households (consumi finali, in VALORE)
    'qD_intermediate': {'P1': 0.71, 'P2': 0.85, 'P3': 0.89, 'P4': 0.96, 'P5': 0.99, 'P6': 0.71, 'P7': 0.38, 'P8': 0.89, 'P9': 0.88, 'P10': 0.86, 'P11': 0.91, 'P12': 0.97, 'P13': 0.99, 'P14': 0.52, 'P15': 0.77},  # KAUs (input intermedi, in QUANTITÀ)
    'qD_gov': {'P1': 0.0, 'P2': 1.0, 'P3': 1.0, 'P4': 1.0, 'P5': 1.0, 'P6': 1.0, 'P7': 0.0, 'P8': 1.0, 'P9': 0.0, 'P10': 1.0, 'P11': 1.0, 'P12': 1.0, 'P13': 1.0, 'P14': 1.0, 'P15': 0.98}           # GOV
}

# property_shares famiglie (uguali alle quote di ricchezza)
group_shares   = np.array([0.0, 0.045, 0.107, 0.185, 0.663] , dtype=float)  # somma = 1
hh_per_group   = 400
n_groups       = len(group_shares)
assert n_households == hh_per_group * n_groups

per_hh = np.repeat(group_shares / hh_per_group, hh_per_group)   # (2000,)
prop_mat = np.tile(per_hh.reshape(-1, 1), (1, n_firms))         # (2000, 15)

# sanity check: ogni firm è interamente posseduta dalle HH
assert np.allclose(prop_mat.sum(axis=0), 1.0, atol=1e-12)

params['Households_var']['property_shares'] = prop_mat

# Banca
params['nBanks'] = 1
params['Banks_var']['reserves'] = [1000000000.0]
params['Banks_var']['CAR'] = [0.1]
params['Banks_var']['interest_rate'] = [0.01]
params['Banks_var']['threshold'] = [1]      # >0 => concede i prestiti
params['Banks_var']['repayment_time'] = [500]

# Governo
params['Gov_var']['liquidity'] = 0
params['Gov_var']['tax_rates'] = tax_rates
params['Gov_var']['consumption_shares'] = alpha_Gov
params['Gov_var']['average_wage'] = float(wages.mean())
params['Gov_var']['ub_fraction'] = ub_fraction
params['Gov_var']['transfer_fraction'] = transfer_fraction

# RoW (compratore dei beni domestici = export)
params['RoW_var']['liquidity'] = 0.0
params['RoW_var']['prices'] = {'P1': 1.0, 'P2': 1.0, 'P3': 1.0, 'P4': 1.0, 'P5': 1.0, 'P6': 1.0, 'P7': 1.0, 'P8': 1.0, 'P9': 1.0, 'P10': 1.0, 'P11': 1.0, 'P12': 1.0, 'P13': 1.0, 'P14': 1.0, 'P15': 1.0}
params['RoW_var']['GDP'] = Y_R
params['RoW_var']['consumption2GDP'] = c_R
params['RoW_var']['consumption_shares'] = {f'P{i+1}': float(alpha_R[i]) for i in range(n_sectors)}
params['RoW_var']['suppliers_weights'] = {f'P{i+1}': {i: 1.0} for i in range(n_sectors)}  # 1 KAU per prodotto


# Parte di codice dedicata al PNIEC, commentare da qua a poco prima di n_steps per la simulazione senza PNIEC
## --------- SHOCK PNIEC ----------- ##

# indici delle Special KAU
idx_wind = 2    # eolico
idx_solar = 3   # solare

# Overnight cost in milioni di euro/MW
OC_wind = 1.234    # eolico
OC_solar = 0.788   # solare

# Quote per KAU fornitrici
shares_wind = {
    0: 0.65,
    1: 0.15,
    4: 0.12,
    5: 0.013,
    6: 0.013,
    7: 0.013,
    8: 0.013,
    9: 0.013,
    10: 0.013,
}

shares_solar = {
    0: 0.45,
    1: 0.10,
    4: 0.195,
    5: 0.045,
    6: 0.025,
    7: 0.045,
    8: 0.025,
    9: 0.07,
    10: 0.045,
}

commodities = params['commodities_list'] 

# BOM: unità di capitale per installare 1MW di nuova capacità
bom_wind = {commodities[i]: OC_wind * share for i, share in shares_wind.items()}
bom_solar = {commodities[i]: OC_solar * share for i, share in shares_solar.items()}

# # MW da installare nel mese di shock (un solo step)
MW_wind_month = 15070.0 / 60.0   # ≈ 251.17 MW
MW_solar_month = 40151.0 / 60.0  # ≈ 669.18 MW

# step di inizio e durata dello shock (60 mesi)
first_shock = 1001
n_shock_steps = 60

params['shock_start'] = first_shock
params['shock_end']   = first_shock + n_shock_steps - 1

# profilo per l'eolico
sched_wind = np.full(n_shock_steps, MW_wind_month,  dtype=float)

# profilo per il solare (stesso schema)
sched_solar = np.full(n_shock_steps, MW_solar_month,  dtype=float)

params['special_kaus'] = {
    'indices': [idx_wind, idx_solar],
    'profiles_by_index': {
        idx_wind: {
            'bom_units_per_MW': bom_wind,
            'power_schedule_MW': sched_wind.tolist(),  # un solo mese
        },
        idx_solar: {
            'bom_units_per_MW': bom_solar,
            'power_schedule_MW': sched_solar.tolist(), # un solo mese
        },
    }
}

# --- Calibrazione priorità green coerente con shock PNIEC ---
# Inserire i dati di stazionarietà ottenuti con la simulazione senza shock PNIEC

# Dati di base in stato stazionario
Y3_base  = 131.793    # produzione KAU 3 (eolico)
Y4_base  = 155.74    # produzione KAU 4 (solare)
Y12_base = 4215.633    # produzione KAU 12 (altro elettrico)

K3_base = 3890.3966   # somma stock di capitale KAU 3
K4_base = 3314.78    # somma stock di capitale KAU 4

# Extra capitale PNIEC per step (solo quota PNIEC, non deprezzamento)
dK3_step = 309.3197873
dK4_step = 527.3164667

# Coefficienti di capitale "medi"
b3 = K3_base / Y3_base
b4 = K4_base / Y4_base

# Aumento di output potenziale per step dovuto SOLO all’extra PNIEC
dY3_step = dK3_step / b3
dY4_step = dK4_step / b4

Y_elec_base = Y3_base + Y4_base + Y12_base

# Aumento relativo di output elettrico per step e per 60 step
r_step = (dY3_step + dY4_step) / Y_elec_base
r_60   = r_step * n_shock_steps    # n_shock_steps = 60

# Ripartizione dell’extra tra eolico e solare
gamma_wind  = dY3_step / (dY3_step + dY4_step)
gamma_solar = dY4_step / (dY3_step + dY4_step)

# Parametri da passare al modello per la priorità green
params['green_priority'] = {
    'active': True,
    'shock_start': first_shock,
    'shock_end':   params['shock_end'],    # stesso orizzonte dello shock PNIEC
    'r_total_max': float(r_60),           # ~0.0467
    'gamma_wind':  float(gamma_wind),     # ~0.27
    'gamma_solar': float(gamma_solar),    # ~0.73
    'electricity_rows': ['P3', 'P4', 'P12'],
}

# 6) Run simulazione
# -----------------------------
n_steps = 50

results = exp.execute_single_scenario(params, n_steps, folder_path="Experiments/Calcolo_finale")

# -----------------------------
# 7) Controllo GDP
# -----------------------------
gdp = np.array(results.variables['MyModel']['GDP'])
gdp_last10_mean = float(gdp[-10:].mean()) if len(gdp) >= 10 else float(gdp.mean())

print("\n--- RISULTATI ---")
print("GDP (ultimi 10 periodi, media) ≈", round(gdp_last10_mean, 3))
print("GDP (serie completa)           =", np.round(gdp, 3))

import1 = np.array(results.variables['MyModel']['imports_value_total'])
imp_tot = np.array(results.variables['MyModel']['imports_value_total'])[-1]
imp_hh  = np.array(results.variables['MyModel']['imports_value_HH'])[-1]
imp_kau = np.array(results.variables['MyModel']['imports_value_KAU'])[-1]
imp_gov = np.array(results.variables['MyModel']['imports_value_GOV'])[-1]
print("Import totali (ultimo step):", imp_tot)
print("… di cui HH:", imp_hh, "— KAU:", imp_kau, "— GOV:", imp_gov)


# Script per controllare se ci sono razionamenti
import pandas as pd

def report_rationing_kau_all(results,
                             eps=1e-6,
                             start_t=0,
                             print_steps=True,
                             max_steps_shown=30):
    """
    Controlla razionamenti per tutte le KAU (normali + SpecialKAU).

    results : oggetto Results (es. results5)
    eps     : soglia numerica per considerare il gap > 0
    start_t : considera solo t > start_t (per ignorare transitori)
    """

    tables = []

    # 1) Prendo sia LocalKAU_price che SpecialKAU, se esistono
    for key in ('LocalKAU_price', 'SpecialKAU'):
        if key not in results.variables:
            continue

        # df ha MultiIndex (obj_id, t) -> lo porto a colonne
        df = pd.DataFrame(results.variables[key]).reset_index()

        need = {'obj_id', 't', 'previous_demand', 'sold_quantity'}
        if not need.issubset(df.columns):
            missing = need - set(df.columns)
            raise KeyError(
                f"Mancano colonne {missing} in {key}. "
                f"Colonne presenti: {list(df.columns)}"
            )

        df = df[['obj_id', 't', 'previous_demand', 'sold_quantity']].copy()
        df['kind'] = key   # solo per sapere da quale tabella viene
        tables.append(df)

    if not tables:
        print("Nessuna tabella KAU trovata (né LocalKAU_price né SpecialKAU).")
        return None

    # 2) Unisco e ordino per KAU e tempo
    df = pd.concat(tables, ignore_index=True)
    df.sort_values(['obj_id', 't'], inplace=True)

    # 3) Tolgo sempre la prima riga per ciascuna KAU (t=0)
    df['_row_in_kau'] = df.groupby('obj_id').cumcount()
    df = df[df['_row_in_kau'] > 0]

    # 4) Eventuale burn-in aggiuntivo
    if start_t is not None:
        df = df[df['t'] > start_t]

    if df.empty:
        print("Nessun dato dopo il burn-in / start_t.")
        return None

    # 5) Gap domanda-venduto
    df['gap'] = df['previous_demand'].astype(float) - df['sold_quantity'].astype(float)
    raz = df[df['gap'] > eps].copy()

    if raz.empty:
        print(f"✅ Nessun razionamento (gap > {eps}) per t > {start_t}.")
        return None

    # 6) Riepilogo per KAU
    summary = (
        raz.groupby('obj_id')
           .agg(first_t=('t', 'min'),
                last_t =('t', 'max'),
                n_steps=('t', 'nunique'),
                max_gap=('gap', 'max'),
                sum_gap=('gap', 'sum'))
           .reset_index()
    )

    print(f"⚠️ Rilevati razionamenti in {len(raz)} righe, "
          f"{raz['t'].nunique()} step distinti.")

    for _, r in summary.iterrows():
        k = int(r['obj_id'])
        print(
            f"• KAU obj_id={k}: {int(r['n_steps'])} step "
            f"(da t={int(r['first_t'])} a t={int(r['last_t'])}); "
            f"max_gap={r['max_gap']:.6g}, sum_gap={r['sum_gap']:.6g}"
        )
        if print_steps:
            steps = raz.loc[raz['obj_id'] == k, 't'].tolist()
            print(
                f"   steps: {steps[:max_steps_shown]}"
                f"{' ...' if len(steps) > max_steps_shown else ''}"
            )

    return summary


_ = report_rationing_kau_all(results, eps=1e-6, start_t=0)
