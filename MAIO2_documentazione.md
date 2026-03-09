# Documentazione del Modello MAIO2

> **Modello Agent-Based Input-Output** — Economia italiana a 15 settori
> Framework: [agentpy](https://agentpy.readthedocs.io/) · Python 3.11 · Calibrato sul PIL italiano mensile

---

## Indice

1. [Struttura generale del modello](#1-struttura-generale-del-modello)
2. [Ruolo di ogni file e classe](#2-ruolo-di-ogni-file-e-classe)
3. [Flusso di esecuzione: `step()` passo per passo](#3-flusso-di-esecuzione-step-passo-per-passo)
4. [Principali flussi economici](#4-principali-flussi-economici)

---

## 1. Struttura Generale del Modello

### 1.1 Panoramica

MAIO2 è un modello **macroeconomico agent-based** di tipo **input-output** che simula
un'economia aperta con settori produttivi espliciti, famiglie eterogenee, credito bancario,
settore pubblico e commercio estero. L'economia di riferimento è quella **italiana** con
calibrazione mensile.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MODELLO MAIO2                                   │
│                                                                         │
│   Calibrazione: PIL italiano ≈ €137.8 mld/mese                         │
│   Settori: 15  │  KAU: 15  │  Firm: 15  │  Household: 2000             │
│   Bank: 1      │  Government: 1          │  RoW: 1                     │
│   Framework: agentpy  │  Step temporale: 1 mese                        │
│                                                                         │
│   Shock simulato: PNIEC (Piano Nazionale Integrato Energia e Clima)     │
│   → Investimenti eolico (KAU 3) + fotovoltaico (KAU 4)                 │
│   → 251 MW/mese eolico + 669 MW/mese solare per 60 mesi                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Architettura degli Agenti

```
                        ┌─────────────────┐
                        │   MyModel       │  ← orchestratore centrale
                        │  (Model.py)     │     (ap.Model)
                        └────────┬────────┘
                                 │ crea e coordina
         ┌───────────────────────┼────────────────────────────┐
         │           │           │           │        │        │
    ┌────┴────┐ ┌────┴────┐ ┌───┴────┐ ┌───┴───┐ ┌──┴──┐ ┌──┴──┐
    │Household│ │  Firm   │ │LocalKAU│ │  Bank │ │ Gov │ │ RoW │
    │ ×2000   │ │  ×15   │ │  ×15  │ │  ×1  │ │ ×1 │ │ ×1 │
    └─────────┘ └────┬────┘ └───────┘ └───────┘ └─────┘ └─────┘
                     │ possiede
                     └──→ KAU_list (1 KAU per Firm)
                              │
                         usa Loan
                         (non-agent)
```

### 1.3 Struttura Settoriale

I 15 settori (P1–P15) seguono la classificazione NACE/ATECO italiana:

```
P1  Agricoltura e silvicoltura
P2  Estrazione di minerali
P3  Energia elettrica da fonti eoliche        ← SpecialKAU (shock PNIEC)
P4  Energia elettrica da fonti solari         ← SpecialKAU (shock PNIEC)
P5  Industrie alimentari e bevande
P6  Industrie chimiche e farmaceutiche
P7  Metallurgia e prodotti in metallo
P8  Macchinari e apparecchiature
P9  Costruzioni
P10 Commercio all'ingrosso e al dettaglio
P11 Trasporti e logistica
P12 Immobiliare (attività residenziale)       ← quota import bassa (0.98 dom.)
P13 Istruzione e formazione
P14 Sanità e assistenza sociale
P15 Servizi alle imprese e altri servizi      ← settore dominante (67% consumi HH)
```

### 1.4 Matrice Tecnica Input-Output

Il cuore del modello è la **matrice dei coefficienti tecnici C** (15×15) dove `C[i,j]`
rappresenta la quantità di bene `i` necessaria per produrre un'unità di bene `j`:

```
       P1    P2    P3    P4    P5    P6    P7    P8    P9   P10   P11   P12   P13   P14   P15
P1  [0.056 0.039 0.003 0.003 0.003 0.001  0     ...                               0.002]
P5  [0.003 0.004 0.005 0.006 0.153 0.004 0.001  ...                               0.005]
P6  [0.009 0.008 0.009 0.010 0.009 0.083 0.137  ...                               0.013]
P15 [0.277 0.266 0.107 0.117 0.163 0.029 0.009  ...                               0.247]
     ↑ i servizi alle imprese (P15) sono input in TUTTI i settori (0.03–0.28)
```

Il **moltiplicatore di Leontief** `L = (I − C)⁻¹` viene usato nella calibrazione per
determinare la domanda indiretta associata alla domanda finale.

### 1.5 Parametri Chiave della Simulazione

| Parametro | Valore | Descrizione |
|---|---|---|
| `n_sectors` | 15 | numero di settori produttivi |
| `n_KAUs` | 15 | unità produttive (1 per settore) |
| `n_firms` | 15 | holding finanziarie (1 per settore) |
| `n_households` | 2000 | famiglie (5 gruppi di reddito × 400) |
| `Y_scale` | €137,798 mln/mese | PIL italiano mensile target |
| `seed` | 32 | seme casuale |
| `interest_rate` | 1% | tasso di interesse banca |
| `repayment_time` | 500 | durata prestiti (periodi) |
| `labor_tax` | 25% | aliquota IRPEF (su reddito da lavoro) |
| `dividends_tax` | 20% | aliquota su dividendi |
| `transfer_fraction` | 0.0 | trasferimenti governativi (scenario base) |
| `u*` | 0.75 | tasso di utilizzo della capacità target |
| `n_steps` | 50 | passi della simulazione |

---

## 2. Ruolo di Ogni File e Classe

### 2.1 Mappa dei File

```
MAIO2/
├── script_simulazione.py   ← PUNTO DI INGRESSO: parametri + esecuzione
├── NewExperimenter.py      ← motore di simulazione + calibrazione + grafici
├── Model.py                ← MyModel: orchestratore del ciclo temporale
├── LocalKAU_ordinato.py    ← unità produttive (4 classi)
├── Firm.py                 ← holding finanziaria (credito + dividendi)
├── Household.py            ← famiglie (consumo + lavoro + risparmio)
├── Bank.py                 ← banca (credito + riserve)
├── Government.py           ← governo (tasse + spesa + trasferimenti)
├── RoW.py                  ← resto del mondo (import + export)
├── Loan.py                 ← contratto di prestito (non è un agente)
└── schema_agenti.py        ← script per generare lo schema visivo
```

### 2.2 `script_simulazione.py` — Punto di Ingresso

**Ruolo**: configura tutti i parametri e lancia la simulazione.

**Sequenza logica**:
```
1. Definisce struttura (15 settori, 2000 HH, ecc.)
2. Carica matrice C (coefficienti tecnici 15×15)
3. Definisce alpha_H (quote consumo HH), alpha_R (RoW), alpha_Gov
4. Definisce salari, tasse, trasferimenti
5. Chiama Experimenter.create_initcond_Baseline(...)
   → calcola prezzi e quantità di equilibrio iniziale
6. Sovrascrive parametri specifici (capital_coeff, B_cap, D_cap)
7. Configura shock PNIEC (eolico+solare, 60 mesi da t=1001)
8. Chiama Experimenter.execute_single_scenario(params, n_steps=50)
9. Stampa risultati GDP + import breakdown
10. Chiama report_rationing_kau_all() per controllo razionamenti
```

### 2.3 `NewExperimenter.py` — Classe `Experimenter`

**Ruolo**: calibrazione del punto fisso + esecuzione + output.

| Metodo | Descrizione |
|---|---|
| `create_initcond_Baseline(...)` | Calcola condizioni iniziali di equilibrio. Risolve il sistema I-O per trovare prezzi e quantità coerenti con il PIL target `Y`. |
| `find_fixedpoint_baseline(params)` | Itera il modello fino a convergenza (punto fisso). Usa aggiornamento iterativo delle variabili KAU. |
| `execute_single_scenario(params, n_steps, folder_path)` | Esegue una singola simulazione di `n_steps` passi. Salva risultati in Excel e genera grafici. |
| `run_single_realization(params, n_steps)` | Esegue il modello agentpy e restituisce l'oggetto `Results`. |
| `figures_single_sim(results, folder_path)` | Genera ~80 grafici (produzione, prezzi, GDP, import, ecc.) e li salva come PNG + pickle. |
| `run_multiple_scenarios(...)` | Confronto tra scenari multipli (es. con/senza shock). |

**Calibrazione iniziale** (`create_initcond_Baseline`):
```
Input:  Y (PIL target), C (matrice tecnica), wages, alpha (quote consumo)
        n_households, lambdaT (wealth target), csi (propensione al consumo)

Passo 1: q* = L·f   dove L=(I-C)⁻¹, f = domanda finale (da Y e alpha)
Passo 2: p* = 1 (prezzi normalizzati a 1 nel punto fisso)
Passo 3: KAU_workers[j] = q*[j] * labor_tech_coeff[j] / wages[j]
Passo 4: Alloca HH a KAU in base a KAU_workers
Passo 5: Distribuisce ricchezza iniziale per gruppi (5 gruppi × 400 HH)
Output: params dict con tutte le variabili inizializzate
```

### 2.4 `Model.py` — Classe `MyModel(ap.Model)`

**Ruolo**: orchestratore. Crea tutti gli agenti, li inizializza e coordina il ciclo temporale.

```python
class MyModel(ap.Model):
    def setup(self)    # crea agenti, li collega, inizializza variabili
    def step(self)     # ← UN PASSO TEMPORALE COMPLETO (vedi sezione 3)
    def update(self)   # registra variabili aggregate per ogni t
    def end(self)      # registrazione finale
```

**Liste di agenti**:
```python
self.Firm_agents       = AgentList(self, nFirms,      Firm)         # 15
self.Household_agents  = AgentList(self, nHouseholds, Household)    # 2000
self.localKAU_agents   = AgentList(self, nKAUs,       LocalKAU_price/SpecialKAU)  # 15
self.Bank_agents       = AgentList(self, nBanks,       Bank)         # 1
self.Government        = AgentList(self, 1,            Government)   # 1
self.RoW               = AgentList(self, 1,            RoW)          # 1
self.buyer_agents      = localKAU + Household + Government + RoW   # tutti i compratori
```

**Metodi ausiliari**:
```
_init_green_priority()          → legge parametri PNIEC dal params dict
_update_green_priority()        → aggiorna quote elettricità ogni step (durante shock)
_pool_electricity_budgets()     → unifica budget elettrico (eolico+solare) durante shock
_enforce_domestic_electricity_priority() → forza acquisti green prima dei convenzionali
_agents_with_consumption_budgets()       → lista agenti con budget > 0 per commodity
```

### 2.5 `LocalKAU_ordinato.py` — Gerarchia di Classi

Il file contiene **4 classi** con ereditarietà a tre livelli:

```
ap.Agent
    └── LocalKAU                 ← classe base (attributi + metodi condivisi)
            ├── LocalKAU_price   ← prezzo determinato da markup sul costo (scenario base)
            ├── LocalKAU_unitcost ← prezzo = unit cost (variante alternativa)
            └── SpecialKAU       ← override per P3 (eolico) e P4 (solare)
                                    gestisce lo shock PNIEC
```

**Ciclo di vita di una KAU** (metodi principali in ordine di chiamata):

```
form_demand_expectation()   → stima domanda futura da domanda passata + adattamento
make_plans()                → chiama:
    set_stock_targets()         → target scorte intermedie = alpha * domanda attesa
    set_capital_targets()       → target capitale = beta * domanda attesa / u*
    plan_production()           → produzione pianificata = max(domanda, target scorte)
    plan_demanded_quantities()  → quantità di input intermedie necessarie
    plan_demanded_capital_quantities() → input di capitale necessari
    plan_total_demanded_quantities()   → somma input correnti + capitale
    plan_labor_demand()         → fabbisogno di lavoro = coeff_lavoro * produzione
compute_liquidity_needs()   → fabbisogno credito = costo totale - cassa disponibile
hire(ag)                    → assume una Household disoccupata
pay_wages()                 → paga i salari agli employees (via Firm)
produce()                   → produzione effettiva (limitata da input disponibili)
self_invest_own_capital()   → usa propria produzione come capitale fisso
set_supply()                → supply = stock + produzione attesa
set_price()                 → prezzo base = unit_cost * (1 + markup)
buy(commodity)              → acquisto input intermedi (dom. + RoW con quota qD)
sell(demand)                → vende beni ai compratori
compute_earnings()          → ricavi - costi = utili lordi → netti (dopo corporate tax)
update_prices()             → aggiusta markup su base domanda/offerta
update_my_stock()           → aggiorna scorte fisiche post-mercato
revaluate_inputs_stocks()   → rivaluta scorte al prezzo corrente
depreciate_capital()        → riduce stock di capitale (ammortamento)
pay_taxes()                 → versa VAT + corporate tax al Governo
```

**`SpecialKAU`** (P3 eolico, P4 solare):
- Sovrascrive `make_plans()` per includere la **domanda extra di capitale** del PNIEC
- Registra `installed_MW`, `installed_MW_cum`, `capital_purchase_flow`
- Riceve ogni mese `MW_wind_month` o `MW_solar_month` di nuova capacità da installare
- Calcola la domanda di beni capitali usando la **Bill of Materials (BOM)** per MW

### 2.6 `Firm.py` — Classe `Firm(ap.Agent)`

**Ruolo**: holding finanziaria che possiede un insieme di KAU.
Gestisce il **credito bancario** e la distribuzione dei **dividendi** agli azionisti.

```
Firm
 ├── KAU_list[]              → lista delle KAU di proprietà
 ├── wealth / deposit        → cassa disponibile
 ├── cash_for_KAU{}          → allocazione di cassa per KAU
 ├── loans_list[]            → prestiti bancari attivi
 └── KAU_dividends{}         → utili netti ricevuti dalle KAU
```

**Flusso finanziario interno**:
```
KAU.net_earnings
      ↓ (ogni step)
Firm.KAU_dividends[kau_id]
      ↓ send_credit_request()
      ├── Se fabbisogno > cassa: richiede prestito a Bank
      │       Bank.evaluate_request() → nuovo Loan
      │       Firm.update_cash_for_KAU(+amount)
      └── execute_financial_payments():
              ├── rimborsa prestiti in scadenza → Bank.receive_payment()
              ├── pay_wages() → KAU.pay_wages() → HH.receive_wage()
              └── distribute_dividends() → HH.receive_dividends()
```

### 2.7 `Household.py` — Classe `Household(ap.Agent)`

**Ruolo**: famiglia consumatrice, lavoratrice, risparmiatrice e azionista.
2000 HH suddivise in **5 gruppi di reddito** (400 per gruppo):

```
Gruppo 1: λ = 0.00 → patrimo target = 0   (nessun risparmio)
Gruppo 2: λ = 2.39 → patrimo target = 2.39 × reddito
Gruppo 3: λ = 4.01
Gruppo 4: λ = 4.92
Gruppo 5: λ = 9.92 → (benestanti, alto risparmio)
```

Quote di proprietà delle Firm: il gruppo 5 detiene il **66.3%** della ricchezza totale.

**Ciclo di vita HH**:
```
receive_wage(w)                        → wealth += w
receive_dividends(d)                   → wealth += d
receive_unemployment_benefit(ub)       → wealth += ub (se disoccupato)
receive_transfer(t)                    → wealth += t  (trasferimento gov)
determine_disposable_income()          → calcola tasse IRPEF + reddito disponibile
determine_consumption_budgets()        → budget = disp_income + csi*(W - λ*disp_income)
                                          budget per commodity = budget * alpha[k]
buy(commodity)                         → acquisto da KAU domestica (quota qD)
                                          + da RoW (quota 1-qD)
pay_taxes()                            → wealth -= (labor_tax + dividend_tax)
                                          Government.taxes += totale
```

**Formula del budget di consumo**:
```
budget = disposable_income + csi × (wealth - income - λ × disposable_income)
       ↑ reddito disponibile      ↑ aggiustamento patrimoniale
```

### 2.8 `Bank.py` — Classe `Bank(ap.Agent)`

**Ruolo**: unica banca del sistema, fornisce credito alle Firm.

```
Bank
 ├── reserves          → riserve liquide
 ├── loans[]           → portafoglio prestiti attivi
 ├── deposits{}        → conti correnti (HH + Firm)
 ├── CAR = 0.10        → Capital Adequacy Ratio (non attivamente vincolante)
 ├── interest_rate     → tasso di interesse mensile (1%)
 ├── threshold = 1     → soglia per concessione (>0 → concede sempre)
 └── repayment_time    → durata standard dei prestiti (500 periodi)
```

**Logica di concessione**: se `threshold > 0`, la banca concede **sempre** il credito
richiesto (no credit rationing nell'implementazione corrente).

**Distribuzione dividendi**:
Gli interessi incassati (`interests_payment`) vengono distribuiti in parti uguali a
tutte le 2000 Household ad ogni passo.

### 2.9 `Government.py` — Classe `Government(ap.Agent)`

**Ruolo**: settore pubblico. Raccoglie tasse, eroga sussidi/trasferimenti, acquista beni.

```
ENTRATE:                          USCITE:
  ├── IRPEF (labor_tax)             ├── sussidi disoccupazione
  ├── IRPEF dividendi               ├── trasferimenti alle famiglie
  ├── VAT (da KAU)                  ├── spesa pubblica (acquisto beni da KAU)
  └── Corporate tax (da KAU)        └── import governativo (da RoW)
```

**Nota**: nel parametro base `transfer_fraction = 0.0` e `ub_fraction = 0.0`,
quindi nel run di 50 step i trasferimenti sono nulli.

### 2.10 `RoW.py` — Classe `RoW(ap.Agent)`

**Ruolo**: resto del mondo. Funge da **venditore** (esportatore verso l'economia domestica)
e da **compratore** (importatore di beni domestici = export domestico).

```
RoW come venditore (IMPORT per l'economia domestica):
  → offerta infinita (supply = inf)
  → prezzi fissi = 1.0 per tutte le commodity
  → HH, KAU, Gov pagano RoW per beni importati

RoW come compratore (EXPORT dall'economia domestica):
  → GDP_RoW = €178,809 mln/mese (PIL estero)
  → c_R = 0.10 (propensione al consumo verso l'economia italiana)
  → alpha_R = vettore delle quote settoriali
  → acquista da KAU domestiche con pesi suppliers_weights
```

Quote domestiche (`qD`) per commodity (HH, KAU, GOV):
```
  HH:  P1=64%, P3=87%, P6=100%, P7=100%, P12=98%, P15=86%
  KAU: P6=71%, P7=38%, P8=89%, P14=52%, P15=77%
  GOV: P1=0%,  P7=0%,  P9=0%,  P15=98%
```

### 2.11 `Loan.py` — Classe `Loan` (non-agent)

**Ruolo**: contratto di prestito a tasso fisso con ammortamento alla francese.

```
Loan(granted_amount, remaining_amount, interest_rate,
     id_bank, id_firm, remaining_time, weighted_KAU_list)

Metodi:
  determine_payment()          → rata = r/(1-(1+r)^-n) × remaining_amount
  determine_interest_payment() → interessi = r × remaining_amount
  determine_capital_payment()  → rata - interessi
  execute_payment()            → remaining_amount = (1+r)×old - rata
```

---

## 3. Flusso di Esecuzione: `step()` Passo per Passo

### 3.1 Schema Generale

Ogni passo temporale (1 mese) esegue **6 fasi** in sequenza:

```
╔══════════════════════════════════════════════════════════════════╗
║  FASE 1 — PRODUZIONE E CREDITO          (lato offerta)          ║
╠══════════════════════════════════════════════════════════════════╣
║  FASE 2 — MERCATO DEL LAVORO            (allocazione lavoro)    ║
╠══════════════════════════════════════════════════════════════════╣
║  FASE 3 — PAGAMENTI E REDDITI           (distribuzione)         ║
╠══════════════════════════════════════════════════════════════════╣
║  FASE 4 — MERCATO DEI BENI              (lato domanda)          ║
╠══════════════════════════════════════════════════════════════════╣
║  FASE 5 — CONTABILITÀ E TASSE           (chiusura dei conti)    ║
╠══════════════════════════════════════════════════════════════════╣
║  update() — REGISTRAZIONE VARIABILI AGGREGATE                   ║
╚══════════════════════════════════════════════════════════════════╝
```

### 3.2 Dettaglio Passo per Passo

```
step(t)
│
├─ [0] SHOCK CHECK
│       if shocks.active and t % frequency == 0:
│           HH.wealth += shocks.quantity / nHouseholds
│
├─ [1] RESET CONTATORI FIRMA
│       for f in Firm_agents:
│           f.loans_received_step = 0
│           f.repayments_step     = 0
│           f.dividends_paid_step = 0
│
│   ═══ FASE 1: PRODUZIONE E CREDITO ══════════════════════════════
│
├─ [2] _update_green_priority()
│       Se shock PNIEC attivo: aggiorna quote alpha per P3/P4
│       (ridirige domanda finale da P12 verso P3+P4)
│
├─ [3] KAU.form_demand_expectation()  [per ogni KAU]
│       previous_demand_new = (1-speed)*previous_demand + speed*sold_t-1
│       expectation_error   = |sold - expected| / expected
│
├─ [4] KAU.make_plans()  [per ogni KAU]
│       ├── set_stock_targets()      → target scorte = alpha * E[domanda]
│       ├── set_capital_targets()    → target K = beta * E[domanda] / u*
│       ├── plan_production()        → q_plan = max(E[domanda], scorte_target - scorte)
│       ├── plan_demanded_quantities()  → per ogni input i: d_i = C[i,j] * q_plan
│       ├── plan_demanded_capital_quantities() → per ogni capital i: d_K_i = B[i,j]*q_plan
│       └── plan_labor_demand()      → L_d = coeff_lavoro * q_plan
│           → crea vacancy se L_d > #dipendenti attuali
│
├─ [5] KAU.compute_liquidity_needs()  [per ogni KAU]
│       liquidity_need = costo_totale_previsto - cassa_disponibile
│       → comunica fabbisogno alla propria Firm
│
├─ [6] Firm.send_credit_request()  [per ogni Firm]
│       ├── somma fabbisogni di tutte le KAU
│       ├── calcola rimborsi dovuti su prestiti esistenti
│       ├── calcola interessi dovuti
│       ├── se richiesta > 0: Bank.evaluate_request(firm, amount)
│       │       → crea nuovo Loan se threshold > 0
│       │       → Firm.update_cash_for_KAU(+granted_amount)
│       └── reset money_requests
│
│   ═══ FASE 2: MERCATO DEL LAVORO ═══════════════════════════════
│
├─ [7] HH.search_job()  [per ogni HH disoccupata]
│       cerca un'impresa con flag_vacancies = 1
│       → KAU.hire(hh): hh.flag_employed = 1, hh.employer_id = kau.id
│
├─ [8] RECORDING: disoccupazione e tasso di disoccupazione
│
│   ═══ FASE 3: PAGAMENTI E REDDITI ══════════════════════════════
│
├─ [9] Firm.execute_financial_payments()  [per ogni Firm]
│       ├── update_cash_for_KAU(-KAU_debt_payment)  → cassa diminuisce
│       ├── per ogni loan in scadenza:
│       │       Bank.receive_payment(payment, interest_payment)
│       │       loan.execute_payment()  → aggiorna remaining_amount
│       ├── pay_wages()
│       │       → KAU.pay_wages()
│       │           → per ogni dipendente: HH.receive_wage(w)
│       │               HH.wealth += w; Bank.deposits[hh] += w
│       └── distribute_dividends()
│               → per ogni HH (proporzionale a property_shares):
│                   HH.receive_dividends(div * share)
│
├─ [10] Bank.distribute_dividends()
│        dividends = interests_payment_cumulati
│        per ogni HH: HH.receive_dividends(dividends / nHH)
│
├─ [11] KAU.produce()  [per ogni KAU]
│        produzione effettiva = min(q_plan, vincoli da input disponibili)
│        labor_demand viene soddisfatta se lavoratori disponibili
│        calcola total_costs = wage_bill + costo_input + ammortamento
│
├─ [12] KAU.set_price()  [per ogni KAU]
│        price_base = unit_cost * (1 + markup)
│
├─ [13] RECORDING: monte salari, monte dividendi, y_w (wage share)
│
├─ [14] HH.determine_consumption_budgets()  [per ogni HH]
│        ├── determine_disposable_income():
│        │       income = wage + dividendi + gov_transfer
│        │       labor_tax    = wage * IRPEF_rate
│        │       dividend_tax = dividendi * tax_rate_div
│        │       disposable_income = income - labor_tax - dividend_tax
│        └── consumption_budget = disposable + csi*(W - income - λ*disposable)
│            per ogni commodity k:
│                consumption_budgets[k] = budget * alpha[k]
│
├─ [15] KAU.adjust_demanded_quantity()  → aggiusta domanda input
├─ [16] KAU.depreciate_capital()        → K_stock *= (1 - delta)
├─ [17] KAU.commit_own_capital()        → la KAU usa la propria produzione come K
│
├─ [18] Gov.distribute_unemployment_benefits()
│        UB = avg_wage * ub_fraction per ogni HH disoccupata
│        → HH.receive_unemployment_benefit(ub)
│
├─ [19] Gov.distribute_transfers()
│        transfer = avg_wage * transfer_fraction per ogni HH
│        → HH.receive_transfer(amount)
│
├─ [20] Gov.determine_consumption_budgets()
│        consumption_budget = max(0, liquidity)
│        per commodity: budget[k] = liquidity * alpha_Gov[k]
│
├─ [21] RoW.determine_consumption_budgets()
│        consumption_budget = c_R * GDP_RoW
│        per commodity: budget[k] = alpha_R[k] * consumption_budget
│
│   ═══ FASE 4: MERCATO DEI BENI ═════════════════════════════════
│
├─ [22] PER OGNI COMMODITY k ∈ {P1, P2, ..., P15}:
│       │
│       ├─ buyer_agents.reset_market_vars()   → attempt_number = 0
│       ├─ buyer_agents.update_sellers_list(k)
│       │   → ordina sellers per prezzo; aggiorna lista con memory_loss
│       │
│       └─ PER n IN range(round_number):       ← N round di incontro
│               buyer_agents.random(nBuyers).buy(k)
│               │
│               └─ HH.buy(k):
│                   1) quota domestica: alloca qD*budget al seller KAU
│                      KAU.sell(q_dom) → HH.wealth -= spesa_dom
│                                         Bank.deposits[hh] -= spesa_dom
│                   2) quota estera: alloca (1-qD)*budget a RoW
│                      RoW.sell(k, q_row) → HH.spent_to_RoW_step += spesa_row
│
│               └─ KAU.buy(k):  (acquisto input intermedi)
│                   quota qD_intermediate domestica → altra KAU
│                   quota estera → RoW
│
│               └─ Gov.buy(k):
│                   quota qD_gov domestica → KAU
│                   quota estera → RoW
│
│               └─ RoW.buy(k):  (export domestico)
│                   acquisto da KAU con pesi suppliers_weights
│
│       [Se shock PNIEC attivo: gestione speciale del gruppo elettrico P3+P4+P12
│        con pooling dei budget e priorità verso fonti rinnovabili]
│
├─ [23] RECORDING: import (HH + KAU + GOV + totale), export, net_foreign_flow
│
│   ═══ FASE 5: CONTABILITÀ E TASSE ══════════════════════════════
│
├─ [24] KAU.update_prices()   → aggiusta markup in base a supply/demand gap
├─ [25] KAU.compute_earnings()
│        revenues  = prezzo * sold_quantity
│        earnings  = revenues - total_costs
│        VAT       = revenues * VAT_rate
│        income_tax= max(0, earnings) * corporate_rate
│        net_earnings = earnings - VAT - income_tax
│        → Firm.KAU_dividends[kau] += net_earnings (per distribuire alle HH)
│
├─ [26] KAU.revaluate_inputs_stocks()  → scorte rivalutate a prezzi correnti
│
├─ [27] Firm.update_loans_age()   → remaining_time -= 1 per ogni loan
│        Bank.update_loans_list() → rimuove loan con remaining_time <= 0
│
├─ [28] RECORDING: prestiti concessi, rimborsati, delta prestiti (cumulati)
│
├─ [29] HH.pay_taxes()
│        wealth -= (labor_tax + dividend_tax)
│        Bank.deposits[hh] -= totale
│        Government.taxes += totale
│
├─ [30] KAU.pay_taxes()
│        Firm.wealth -= (VAT + income_tax)
│        Government.taxes += totale
│
├─ [31] Government.make_period_account()
│        Government.liquidity += taxes
│        taxes = 0  (reset per prossimo step)
│
└─ [32] RECORDING fine step: ricchezze, liquidità per settore
```

### 3.3 `update()` — Registrazione Variabili Aggregate

Chiamato automaticamente da agentpy **dopo ogni** `step()`:

```
GDP          = sum(HH.income)               ← definizione reddito aggregato
Consumption  = sum(HH.consumption)
Nominal Prod = sum(KAU.production * KAU.price)
Firms liq    = sum(Firm.wealth)
HH liq       = sum(HH.wealth)
Total liq    = Firm + HH + Gov

Per ogni settore k:
    Real production of Pk = sum(KAU[my_commodity==k].production)

Per ogni KAU:
    production, price, markup, supply, previous_demand,
    earnings, sold_quantity, stock per commodity,
    capital_stock per commodity, inputs_consumption per commodity

Per ogni Firm:
    wealth, debt, deposit, dividends

Per ogni HH:
    consumption, wealth, income, consumption_budget

Per ogni Bank:
    dividends, reserves, total_deposits, Firms_debt_aggregato
```

---

## 4. Principali Flussi Economici

### 4.1 Schema Completo dei Flussi

```
                         ╔═══════════╗
            ┌────────────║ HOUSEHOLD ║◄────────────────────┐
            │ tasse      ╚═══════════╝  sussidi+trasf.     │
            │ (IRPEF)         │                            │
            │                 │ consumo beni dom.          │ dividendi
            ▼                 ▼                            │ (bank)
    ╔════════════╗       ╔══════════╗         ╔════════════╗
    ║ GOVERNMENT ║◄──────║ LocalKAU ║────────►║    BANK    ║
    ║            ║  VAT  ╚══════════╝ rimb+int║            ║
    ║            ║  corp      │  ▲            ╚════════════╝
    ╚════════════╝            │  │ input          │  ▲
          │                   │  │ intermedi      │  │ prestiti
          │ spesa             ▼  │                │  │ rimborsi
          │ pubblica    ╔══════════╗         ╔════╧══════╗
          └────────────►│ LocalKAU │         ║   FIRM    ║
                         ╚══════════╝         ║           ║
                               ▲              ╚═══════════╝
                               │ export            │
                               │ (RoW acquista)    │ salari
                         ╔═══════╗                 │ dividendi
                         ║  RoW  ║                 ▼
                         ╚═══════╝          ╔═══════════╗
                               │            ║ HOUSEHOLD ║
                               │ import     ╚═══════════╝
                               └──────────►(beni esteri)
```

### 4.2 Flusso del Lavoro

```
MERCATO DEL LAVORO (ogni step):

HH disoccupata ──search_job()──► KAU con flag_vacancies=1
                                       │
                                   KAU.hire(hh)
                                       │
                               hh.flag_employed = 1
                               hh.employer_id   = kau.id
                               kau.employees_list.append(hh)

PAGAMENTO SALARI:
KAU.pay_wages()
    per ogni hh in employees_list:
        Firm.update_cash_for_KAU(kau_id, -wage)
        hh.receive_wage(wage)
            → hh.wealth         += wage
            → Bank.deposits[hh] += wage

DISOCCUPAZIONE (se applicabile, ub_fraction > 0):
Gov.distribute_unemployment_benefits()
    per ogni hh con flag_employed = 0:
        hh.receive_unemployment_benefit(avg_wage * ub_fraction)
```

### 4.3 Flusso del Credito

```
CICLO DEL CREDITO (ogni step):

1. KAU calcola fabbisogno liquidità
   liquidity_need = costi_previsti - cassa_disponibile

2. Firm aggrega fabbisogni + calcola rimborsi dovuti:
   total_request = Σ(KAU_needs) + Σ(capital_repayments)
                 - cassa_disponibile

3. Se total_request > 0:
   Firm ──► Bank.evaluate_request(firm, total_request)
                │
                ▼
           threshold > 0?
                │ Sì
                ▼
           Loan(granted=total_request,
                interest_rate=0.01,
                remaining_time=500)
                │
                ▼
           Firm.update_cash_for_KAU(+granted_amount)

4. Alla scadenza (remaining_time <= repayment_time):
   Firm ──► Bank.receive_payment(payment, interest)
   Loan.execute_payment() → remaining_amount aggiornato

5. Bank.distribute_dividends() (ogni step):
   dividends = interests_payment_cumulati
   per ogni HH: HH.receive_dividends(dividends / 2000)

AMMORTAMENTO PRESTITO (formula francese):
   rata_t  = r / (1-(1+r)^-n) × remaining_amount
   interessi_t = r × remaining_amount
   capitale_t  = rata_t - interessi_t
   remaining_t+1 = (1+r) × remaining_t - rata_t
```

### 4.4 Flusso del Consumo e dei Beni

```
DETERMINAZIONE BUDGET CONSUMO (HH):

income = wage + dividendi + gov_transfer
IRPEF  = wage × tax_rate(income)       ← aliquota marginale al 25%
div_tax = dividendi × 0.20
disposable = income - IRPEF - div_tax

target_wealth = λ × disposable         (λ = wealth-to-income target)
gap_wealth    = wealth - income - target_wealth

budget = disposable + csi × gap_wealth  (csi = 0.02)
         ↑ reddito       ↑ correzione patrimoniale (se ricco → consuma di più)

Per commodity k: budget_k = budget × alpha_k

MERCATO BENI (per commodity k):
    Acquisto domestico (qD_k):
        alloc_dom = qD_k × budget_k
        KAU.sell(alloc_dom / price) → qty venduta
        HH.wealth -= spesa_dom
        Bank.deposits[HH] -= spesa_dom

    Acquisto estero (1-qD_k):
        alloc_row = (1-qD_k) × budget_k + shortfall_dom
        RoW.sell(k, alloc_row / price_row)
        HH.spent_to_RoW_step += spesa_row
```

### 4.5 Flusso delle Tasse

```
TASSE RACCOLTE DAL GOVERNO (ogni step):

Da Household:
    ├── IRPEF (labor):   wage × aliquota  → HH.pay_taxes()
    └── Tassa dividendi: div × 0.20       → HH.pay_taxes()

Da KAU (via LocalKAU.pay_taxes()):
    ├── VAT:             revenues × VAT_rate     (= 0 nel parametro base)
    └── Corporate:       net_earnings × corp_rate (= 0 nel parametro base)

Contabilità Governo:
    Government.taxes += totale_step
    Government.liquidity += taxes   (in make_period_account())
    Government.taxes = 0            (reset)

SPESA PUBBLICA:
    Gov.buy(commodity):
        budget_k = consumption_shares[k] × liquidity
        acquista da KAU domestiche (quota qD_gov)
        acquista da RoW (quota 1-qD_gov)
        Gov.liquidity -= spesa_totale
```

### 4.6 Flusso del Commercio Estero

```
IMPORT (spesa verso RoW):

┌─────────────────────────────────────────────────────────┐
│ Fonte         │ Commodity  │ % domestica (qD)           │
├─────────────────────────────────────────────────────────┤
│ HH            │ P1         │ 64%  → 36% da RoW          │
│ HH            │ P15        │ 86%  → 14% da RoW          │
│ KAU (input)   │ P6         │ 71%  → 29% da RoW          │
│ KAU (input)   │ P7         │ 38%  → 62% da RoW (massimo)│
│ Gov           │ P1, P7, P9 │  0%  → 100% da RoW         │
└─────────────────────────────────────────────────────────┘

EXPORT (RoW acquista beni domestici):
    RoW.consumption_budget = c_R × GDP_RoW = 0.10 × €178,809 mln
    Per commodity k: RoW.buy(k) → KAU.sell(demand)
    RoW.spent_domestic_step = export totale del periodo

BILANCIA COMMERCIALE:
    net_foreign_flow = exports - (import_HH + import_KAU + import_GOV)
    (registrata ogni step e cumulata)
```

### 4.7 Identità Contabile del Modello (GDP)

Nel modello, il PIL viene calcolato come **somma dei redditi delle famiglie**:

```
GDP = Σ HH.income = Σ (wage_i + dividendi_i + trasferimenti_i)

Dal lato della spesa:
    GDP ≈ C (consumo HH) + G (spesa gov) + I (investimenti KAU) + NX (export-import)

Dal lato della produzione:
    GDP ≈ Σ KAU.revenues - Σ costi_intermedi
        = Σ KAU.net_earnings + Σ KAU.total_wage_bill + Σ ammortamenti
```

---

## Appendice: Dipendenze tra Moduli

```
script_simulazione.py
    └── NewExperimenter  (Experimenter)
            └── Model  (MyModel)
                    ├── Firm       ────────────── Loan
                    ├── Household
                    ├── LocalKAU_ordinato
                    │       ├── LocalKAU        (base)
                    │       ├── LocalKAU_price  (default)
                    │       ├── LocalKAU_unitcost
                    │       └── SpecialKAU      (P3 eolico, P4 solare)
                    ├── Bank
                    ├── Government
                    └── RoW
```

## Appendice: Variabili Registrate (output della simulazione)

| Categoria | Variabile | Descrizione |
|---|---|---|
| Macro | `GDP` | somma redditi HH |
| Macro | `Nominal Production` | Σ KAU.production × KAU.price |
| Macro | `Consumption` | Σ HH.consumption |
| Macro | `monte_salari` | totale salari pagati |
| Macro | `monte_dividendi` | totale dividendi distribuiti |
| Macro | `y_w` | wage share (salari / PIL) |
| Commercio | `imports_value_total` | import HH + KAU + GOV |
| Commercio | `exports_value_total` | export (RoW.spent_domestic) |
| Commercio | `net_foreign_flow` | export - import |
| Lavoro | `unemployed` | numero HH disoccupate |
| Lavoro | `unemployment_rate` | tasso disoccupazione |
| Fiscale | `Gov_liquidity_*` | liquidità gov (vari punti del ciclo) |
| Fiscale | `labor_tax`, `dividends_tax`, `VAT_tax`, `corporate_tax` | gettiti fiscali |
| Credito | `prestiti_concessi_aggregati` | nuovi prestiti nello step |
| Credito | `Firms_debt_aggregato` | debito totale delle imprese |
| Settoriale | `Real production of Pk` | produzione reale settore k |
| Settoriale | `Pk stock` | scorte intermedie KAU |
| Settoriale | `Pk cap_stock` | stock di capitale KAU |
| PNIEC | `installed_MW`, `installed_MW_cum` | capacità verde installata |

---

*Documento generato automaticamente dall'analisi del codice sorgente MAIO2.*
