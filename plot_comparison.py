# -*- coding: utf-8 -*-
"""
Script per generare grafici comparativi dei due scenari:
- Scenario 1: CON AI Labor Shock
- Scenario 2: SENZA AI Labor Shock

Genera:
1. Grafici sovrapposti con due curve colorate diversamente
2. Salva i grafici nella cartella Experiments/Calcolo_finale/Comparison
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import pickle as pk
import pandas as pd

# Path delle simulazioni
path_with_labor = "Experiments/Calcolo_finale/Scenario_WITH_LaborShock"
path_without_labor = "Experiments/Calcolo_finale/Scenario_WITHOUT_LaborShock"
output_path = "Experiments/Calcolo_finale/Comparison"

# Colori per i due scenari
color_with = '#1f77b4'      # Blu (Labor Shock)
color_without = '#d62728'   # Rosso (No Labor Shock)
label_with = 'With Labor Shock'
label_without = 'Without Labor Shock'

# Crea cartella output se non esiste
if not os.path.isdir(output_path):
    os.makedirs(output_path)
    
# Crea cartella pyfig se non esiste
pyfig_path = output_path + '/pyfig'
if not os.path.isdir(pyfig_path):
    os.makedirs(pyfig_path)

# Carica i risultati dalle due simulazioni
print("Caricamento risultati dalla Scenario WITH Labor Shock...")
try:
    with open(path_with_labor + '/Data', 'rb') as f:
        results_with = pk.load(f)
except FileNotFoundError:
    print(f"❌ ERRORE: File non trovato in {path_with_labor}/Data")
    print(f"   Assicurati che script_simulazione.py sia stato eseguito.")
    exit(1)
except Exception as e:
    print(f"❌ ERRORE nel caricamento: {str(e)}")
    exit(1)
    
print("Caricamento risultati dalla Scenario WITHOUT Labor Shock...")
try:
    with open(path_without_labor + '/Data', 'rb') as f:
        results_without = pk.load(f)
except FileNotFoundError:
    print(f"❌ ERRORE: File non trovato in {path_without_labor}/Data")
    exit(1)
except Exception as e:
    print(f"❌ ERRORE nel caricamento: {str(e)}")
    exit(1)

print("\n✅ Risultati caricati correttamente")
print(f"   WITH Labor Shock: {path_with_labor}/Data")
print(f"   WITHOUT Labor Shock: {path_without_labor}/Data")
print("\nGenerazione grafici comparativi...\n")

# ============================================================================
# PARTE 1: Grafici per le variabili di MyModel (aggregati macro)
# ============================================================================

print("Processing MyModel variables...")
if 'MyModel' in results_with.variables and 'MyModel' in results_without.variables:
    
    # Crea cartella per MyModel
    mymodel_path = output_path + '/MyModel'
    if not os.path.isdir(mymodel_path):
        os.makedirs(mymodel_path)
    if not os.path.isdir(mymodel_path + '/pyfig'):
        os.makedirs(mymodel_path + '/pyfig')
    
    cols_with = results_with.variables['MyModel'].columns
    
    for col in cols_with:
        try:
            x_with = np.array(results_with.variables['MyModel'][col])
            x_without = np.array(results_without.variables['MyModel'][col])
            
            # Determina se plottare dal primo punto o da t=1
            skip_first = not ('wealth' in col or 'stock' in col)
            
            fig = plt.figure(figsize=(10, 6))
            
            if skip_first:
                plt.plot(x_with[1:], color=color_with, linewidth=2.5, 
                        label=label_with, marker='o', markersize=4, alpha=0.8)
                plt.plot(x_without[1:], color=color_without, linewidth=2.5, 
                        label=label_without, marker='s', markersize=4, alpha=0.8)
            else:
                plt.plot(x_with, color=color_with, linewidth=2.5, 
                        label=label_with, marker='o', markersize=4, alpha=0.8)
                plt.plot(x_without, color=color_without, linewidth=2.5, 
                        label=label_without, marker='s', markersize=4, alpha=0.8)
            
            plt.ylabel(col, fontsize=12, fontweight='bold')
            plt.xlabel('Time (steps)', fontsize=12, fontweight='bold')
            plt.legend(fontsize=11, loc='best')
            plt.grid(True, alpha=0.3)
            plt.title(f'Comparison: {col}', fontsize=13, fontweight='bold')
            plt.tight_layout()
            
            # Salva figura
            fig.savefig(f'{mymodel_path}/{col}_comparison.png', dpi=150, bbox_inches='tight')
            
            # Salva come pickle
            with open(f'{mymodel_path}/pyfig/{col}_comparison', 'wb') as pf:
                pk.dump(fig, pf)
            
            plt.close(fig)
            print(f"  ✓ {col}")
            
        except Exception as e:
            print(f"  ✗ Errore in {col}: {str(e)}")

# ============================================================================
# PARTE 2: Grafici per Firms (settori)
# ============================================================================

print("\nProcessing Firm variables...")
if 'Firm' in results_with.variables and 'Firm' in results_without.variables:
    
    firm_path = output_path + '/Firm'
    if not os.path.isdir(firm_path):
        os.makedirs(firm_path)
    if not os.path.isdir(firm_path + '/pyfig'):
        os.makedirs(firm_path + '/pyfig')
    
    # Prendi IDs delle firms
    ids = np.unique(results_with.variables['Firm'].index.get_level_values(0))
    cols = results_with.variables['Firm'].columns
    
    for firm_id in ids:
        for col in cols:
            try:
                x_with = np.array(results_with.variables['Firm'][col].loc[firm_id, :])
                x_without = np.array(results_without.variables['Firm'][col].loc[firm_id, :])
                
                skip_first = not ('wealth' in col or 'stock' in col)
                
                fig = plt.figure(figsize=(10, 6))
                
                if skip_first:
                    plt.plot(x_with[1:], color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without[1:], color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                else:
                    plt.plot(x_with, color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without, color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                
                plt.ylabel(col, fontsize=12, fontweight='bold')
                plt.xlabel('Time (steps)', fontsize=12, fontweight='bold')
                plt.legend(fontsize=11, loc='best')
                plt.grid(True, alpha=0.3)
                plt.title(f'Firm {firm_id} - {col} (Comparison)', fontsize=13, fontweight='bold')
                plt.tight_layout()
                
                fig.savefig(f'{firm_path}/Firm_{firm_id}_{col}_comparison.png', dpi=150, bbox_inches='tight')
                
                with open(f'{firm_path}/pyfig/Firm_{firm_id}_{col}_comparison', 'wb') as pf:
                    pk.dump(fig, pf)
                
                plt.close(fig)
                
            except Exception as e:
                pass  # Silenzio errori per singoli elementi
    
    print(f"  ✓ Completato {len(ids)} Firms x {len(cols)} variabili")

# ============================================================================
# PARTE 3: Grafici per LocalKAU_price (settori produttivi)
# ============================================================================

print("\nProcessing LocalKAU_price variables...")
if 'LocalKAU_price' in results_with.variables and 'LocalKAU_price' in results_without.variables:
    
    kau_path = output_path + '/LocalKAU_price'
    if not os.path.isdir(kau_path):
        os.makedirs(kau_path)
    if not os.path.isdir(kau_path + '/pyfig'):
        os.makedirs(kau_path + '/pyfig')
    
    ids = np.unique(results_with.variables['LocalKAU_price'].index.get_level_values(0))
    cols = results_with.variables['LocalKAU_price'].columns
    
    for kau_id in ids:
        for col in cols:
            try:
                x_with = np.array(results_with.variables['LocalKAU_price'][col].loc[kau_id, :])
                x_without = np.array(results_without.variables['LocalKAU_price'][col].loc[kau_id, :])
                
                skip_first = not ('wealth' in col or 'stock' in col)
                
                fig = plt.figure(figsize=(10, 6))
                
                if skip_first:
                    plt.plot(x_with[1:], color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without[1:], color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                else:
                    plt.plot(x_with, color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without, color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                
                plt.ylabel(col, fontsize=12, fontweight='bold')
                plt.xlabel('Time (steps)', fontsize=12, fontweight='bold')
                plt.legend(fontsize=11, loc='best')
                plt.grid(True, alpha=0.3)
                
                # Identifica nome commodity
                commodities_list = results_with.variables['LocalKAU_price'].index.get_level_values(0).unique()
                commodity_names = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 
                                  'P11', 'P12', 'P13', 'P14', 'P15']
                try:
                    commodity = commodity_names[kau_id] if kau_id < len(commodity_names) else f'KAU_{kau_id}'
                except:
                    commodity = f'KAU_{kau_id}'
                
                plt.title(f'{commodity} - {col} (Comparison)', fontsize=13, fontweight='bold')
                plt.tight_layout()
                
                fig.savefig(f'{kau_path}/KAU_{kau_id}_{col}_comparison.png', dpi=150, bbox_inches='tight')
                
                with open(f'{kau_path}/pyfig/KAU_{kau_id}_{col}_comparison', 'wb') as pf:
                    pk.dump(fig, pf)
                
                plt.close(fig)
                
            except Exception as e:
                pass
    
    print(f"  ✓ Completato {len(ids)} KAU x {len(cols)} variabili")

# ============================================================================
# PARTE 4: Grafici aggiunti Bank (se presente)
# ============================================================================

print("\nProcessing Bank variables...")
if 'Bank' in results_with.variables and 'Bank' in results_without.variables:
    
    bank_path = output_path + '/Bank'
    if not os.path.isdir(bank_path):
        os.makedirs(bank_path)
    if not os.path.isdir(bank_path + '/pyfig'):
        os.makedirs(bank_path + '/pyfig')
    
    ids = np.unique(results_with.variables['Bank'].index.get_level_values(0))
    cols = results_with.variables['Bank'].columns
    
    for bank_id in ids:
        for col in cols:
            try:
                x_with = np.array(results_with.variables['Bank'][col].loc[bank_id, :])
                x_without = np.array(results_without.variables['Bank'][col].loc[bank_id, :])
                
                skip_first = not ('wealth' in col or 'stock' in col)
                
                fig = plt.figure(figsize=(10, 6))
                
                if skip_first:
                    plt.plot(x_with[1:], color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without[1:], color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                else:
                    plt.plot(x_with, color=color_with, linewidth=2.5,
                            label=label_with, marker='o', markersize=4, alpha=0.8)
                    plt.plot(x_without, color=color_without, linewidth=2.5,
                            label=label_without, marker='s', markersize=4, alpha=0.8)
                
                plt.ylabel(col, fontsize=12, fontweight='bold')
                plt.xlabel('Time (steps)', fontsize=12, fontweight='bold')
                plt.legend(fontsize=11, loc='best')
                plt.grid(True, alpha=0.3)
                plt.title(f'Bank {bank_id} - {col} (Comparison)', fontsize=13, fontweight='bold')
                plt.tight_layout()
                
                fig.savefig(f'{bank_path}/Bank_{bank_id}_{col}_comparison.png', dpi=150, bbox_inches='tight')
                
                with open(f'{bank_path}/pyfig/Bank_{bank_id}_{col}_comparison', 'wb') as pf:
                    pk.dump(fig, pf)
                
                plt.close(fig)
                
            except Exception as e:
                pass
    
    print(f"  ✓ Completato {len(ids)} Banks")

# ============================================================================
# PARTE 5: Grafici aggregati confronto KEY METRICS
# ============================================================================

print("\nGenerating summary comparison graphics...")

fig = plt.figure(figsize=(15, 10))

# Estrai variabili chiave da MyModel
key_vars = ['GDP', 'total_output', 'unemployment_rate', 'average_wage']
my_data_with = results_with.variables['MyModel']
my_data_without = results_without.variables['MyModel']

n_plots = len([v for v in key_vars if v in my_data_with.columns])
plot_idx = 1

for var in key_vars:
    if var not in my_data_with.columns:
        continue
    
    ax = plt.subplot(2, 2, plot_idx)
    
    x_with = np.array(my_data_with[var])
    x_without = np.array(my_data_without[var])
    
    skip_first = not ('wealth' in var or 'stock' in var)
    
    if skip_first:
        ax.plot(x_with[1:], color=color_with, linewidth=2.5, 
               label=label_with, marker='o', markersize=5, alpha=0.8)
        ax.plot(x_without[1:], color=color_without, linewidth=2.5, 
               label=label_without, marker='s', markersize=5, alpha=0.8)
    else:
        ax.plot(x_with, color=color_with, linewidth=2.5, 
               label=label_with, marker='o', markersize=5, alpha=0.8)
        ax.plot(x_without, color=color_without, linewidth=2.5, 
               label=label_without, marker='s', markersize=5, alpha=0.8)
    
    ax.set_ylabel(var, fontsize=11, fontweight='bold')
    ax.set_xlabel('Time (steps)', fontsize=11, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'{var}', fontsize=12, fontweight='bold')
    
    plot_idx += 1

plt.suptitle('Key Metrics Comparison: With vs Without Labor Shock', 
            fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig(f'{output_path}/Summary_Comparison.png', dpi=150, bbox_inches='tight')
with open(f'{output_path}/pyfig_summary', 'wb') as pf:
    pk.dump(fig, pf)
plt.close(fig)

print("  ✓ Summary comparison completato")

print("\n" + "="*80)
print("✅ Generazione grafici comparativi completata!")
print(f"Tutti i grafici sono salvati in: {output_path}")
print("="*80)
