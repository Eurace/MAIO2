# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 17:23:21 2025

@author: frado
"""

import numpy as np
import agentpy as ap

import Firm as Fm
import Household as Hh
import LocalKAU_ordinato as lKAU
import Bank as Bk
import Government as Gov
import RoW as RoW

class MyModel(ap.Model):
    
    def setup(self):
        
        
        self.Firm_agents = ap.AgentList(self, self.p.nFirms, Fm.Firm)
        self.Household_agents = ap.AgentList(self, self.p.nHouseholds, Hh.Household)
        
        # fallback se il blocco params non è stato ancora passato nello script (lista vuota)
        if not hasattr(self.p, 'special_kaus') or 'indices' not in self.p.special_kaus:
            self.p.special_kaus = {'indices': [], 'profiles_by_index': {}}
            
        special_idx = set(self.p.special_kaus['indices'])   # converto la lista in set per controlli "i in special_idx" rapidi
        
        # se usiamo KAUtype == 'unitcost' lasciamo come nella versione precedente
        if self.p.KAUtype == 'unitcost':
            self.localKAU_agents = ap.AgentList(self, self.p.nKAUs, lKAU.LocalKAU_unitcost)
        else:
            # 'price' (o default): scegli la classe per ogni indice
            def _cls_for(i):
                return lKAU.SpecialKAU if i in special_idx else lKAU.LocalKAU_price
            
            # costruisco la lista mantenendo l'ordine delle KAU
            # non creo in blocco tutti gli agenti della stessa classe ma uno per volta concatenando
            self.localKAU_agents = ap.AgentList(self, 1, _cls_for(0))
            for i in range(1, self.p.nKAUs):
                self.localKAU_agents += ap.AgentList(self, 1, _cls_for(i))
                
        self._ELEC_GROUP = tuple(getattr(self.p, 'electricity_group', ()))
        
        self.Bank_agents = ap.AgentList(self, self.p.nBanks, Bk.Bank)
        
        self.Government = ap.AgentList(self, 1, Gov.Government)
        
        self.RoW = ap.AgentList(self, 1, RoW.RoW)
        
        
        self.buyer_agents = self.Household_agents + self.localKAU_agents + self.Government + self.RoW
        
        self.nBuyers = self.p.nKAUs + self.p.nHouseholds + 2
        
        self.seller_agents = self.localKAU_agents + self.RoW
        
        
        self.round_number = self.p.round_number
        
        for i,lk in enumerate(self.localKAU_agents):
            
            # assegnazione prodotti a KAU
            lk.my_activity = self.p.KAUactivity_list[i]
            lk.my_commodity = self.p.KAUcommodity_list[i]        
        
            # assegnazione KAU a firm
            owner = self.Firm_agents[self.p.KAUFirm_list[i]]
            owner.KAU_list.append(lk)
            lk.my_firm = owner
            
        self.initialize_firms()
        self.initialize_localKAUs()
        self.initialize_households()
        self.initialize_banks()
            
        self.Government[0].liquidity = self.p.Gov_var['liquidity']
        self.Government[0].tax_rates = self.p.Gov_var['tax_rates'].copy()
        self.Government[0].consumption_shares = self.p.Gov_var['consumption_shares'].copy()
        # AGGIUNGI:
        self.Government[0].average_wage = self.p.Gov_var.get('average_wage', 0.0)
        self.Government[0].ub_fraction = self.p.Gov_var.get('ub_fraction', 0.0)
        self.Government[0].transfer_fraction = self.p.Gov_var.get('transfer_fraction', 0.0)
        
        self.RoW[0].liquidity = self.p.RoW_var['liquidity']
        self.RoW[0].suppliers_weights = self.p.RoW_var['suppliers_weights'].copy()
        self.RoW[0].consumption_shares = self.p.RoW_var['consumption_shares'].copy()
        self.RoW[0].prices = self.p.RoW_var['prices'].copy()
        self.RoW[0].GDP = self.p.RoW_var.get('GDP', 0.0); self.RoW[0].consumption2GDP = self.p.RoW_var.get('consumption2GDP', 0.0)
        
        self.imports_value_HH = 0.0
        self.imports_value_KAU = 0.0
        self.imports_value_GOV = 0.0
        self.imports_value_total = 0.0
        self.monte_salari_t = 0.0
        self.monte_dividendi_t = 0.0
        self.y_w = 0.0
        self.params = self.p
        self.shocks_counter = 0
        self._init_green_priority()
        self._init_ai_labor_shock()       # FASE A: labor-augmenting AI
        
    def initialize_firms(self):
        
        for i,f in enumerate(self.Firm_agents):
            
            f.wealth = self.p.Firms_var['wealth'][i]
            f.set_cash_for_KAUs()
            f.create_dictionaries()
            selected = np.random.randint(0,high = self.p.nBanks)
            f.my_bank = self.Bank_agents[selected]
            f.loans_list = self.p.Firms_var['loans'][i].copy()
            for l in f.loans_list:
                print(l.remaining_amount)
                l.id_bank = f.my_bank.id
                l.id_firm = f.id
                if len(f.KAU_list) > 0:
                    w = 1 / len(f.KAU_list)
                    l.weighted_KAU_list = {lk.id: w for lk in f.KAU_list}
                else:
                    l.weighted_KAU_list = {}  # nessuna KAU da pesare

        
            
    def initialize_localKAUs(self):
        
        for i, lk in enumerate(self.localKAU_agents):
            
            lk.commodities_stock = self.p.localKAUs_var['commodities_stock'][i].copy()
            lk.capital_stocks = self.p.localKAUs_var['capital_stocks'][i].copy()
            
            lk.tech_coeff = self.p.localKAUs_var['tech_coeff'][i].copy()
            lk.capital_coeff = self.p.localKAUs_var['capital_coeff'][i].copy()
            lk.capital_depreciation = self.p.localKAUs_var['capital_depreciation'][i].copy()
            
            lk.prices = self.p.localKAUs_var['prices'].copy()
            lk.price = lk.prices[lk.my_commodity]
            
            
            lk.unit_cost = 0
            
            if(self.p.KAUtype == 'unitcost'):
                for k in lk.tech_coeff.keys():
                    if(k != lk.my_commodity):
                        lk.unit_cost += lk.tech_coeff[k]*lk.prices[k]
                        lk.commodities_stock_value[k] = lk.commodities_stock[k]*lk.prices[k]
                        
                lk.unit_cost = lk.unit_cost/(1-lk.tech_coeff[lk.my_commodity])
                lk.commodities_stock_value[lk.my_commodity] = lk.unit_cost*lk.commodities_stock[lk.my_commodity]
                
            else:
                for k in lk.tech_coeff.keys():
                    lk.unit_cost += lk.tech_coeff[k]*lk.prices[k]
                    lk.commodities_stock_value[k] = lk.commodities_stock[k]*lk.prices[k]
                    lk.capital_stocks_value[k] = lk.capital_stocks[k]*lk.prices[k]
            

            
            lk.my_commodity_stock_value_old = lk.commodities_stock_value[lk.my_commodity]
            
            lk.previous_demand = self.p.localKAUs_var['previous_demand'][i] #.copy()
            lk.expected_demand = lk.previous_demand
            #lk.demand_change = lk.previous_demand
            
            lk.markup = self.p.localKAUs_var['markup'][i]
            
            lk.independence_periods = self.p.localKAUs_var['independence_periods'][i]
            lk.target_capacity_utilization = self.p.localKAUs_var['target_capacity_utilization'][i]
            
            lk.target_speed = self.p.localKAUs_var['target_speed'][i]
            lk.markup_speed = self.p.localKAUs_var['markup_speed'][i]
            lk.earnings = self.p.localKAUs_var['earnings'][i]
            
            lk.my_seller = {}#self.p.localKAUs_var['my_seller'][i].copy()     
            # inizializza contenitori per liste e pesi venditori
            lk.sellers_list = {}
            lk.sellers_weights = {}

            
            for com in self.p.localKAUs_var['my_seller'][i].keys():
                
                index = int(self.p.localKAUs_var['my_seller'][i][com])
                lk.my_seller[com] = self.seller_agents[index]
            
            lk.rationing_threshold = self.p.localKAUs_var['rationing_threshold'][i]
            lk.field_of_view = self.p.localKAUs_var['field_of_view'][i]
            lk.memory_loss = self.p.localKAUs_var['memory_loss'][i]
            lk.opportunism_degree = self.p.localKAUs_var['opportunism_degree'][i]        
            
            for k in lk.tech_coeff.keys():
                # init contabilità input/capitale
                lk.inputs_consumption[k] = 0
                lk.demanded_quantity[k] = 0
                lk.total_expenditure[k] = 0

                lk.capital_purchase[k] = 0
                lk.capital_demanded_quantity[k] = 0
                lk.total_demanded_quantity[k] = 0

               # costruiamo la lista dei candidati seller locali per la commodity k
                cands = self.localKAU_agents.select(self.localKAU_agents.my_commodity == k)
                if len(cands) == 0:
                    list_seller = []  # nessun seller locale per k
                else:
                    n_seller = round(lk.field_of_view * len(cands))
                    n_seller = max(1, min(n_seller, len(cands)))
                    list_seller = cands.random(n_seller)

                lk.sellers_list[k] = [s for s in list_seller]
                # aggiungo sempre RoW come fallback per la commodity k
                lk.sellers_list[k].append(self.RoW[0])
                lk.qD_intermediate = self.p.import_policy.get('qD_intermediate', 1.0)  # float o dict per commodity


            lk.wage_offer = self.p.localKAUs_var['wage_offer'][i]
            lk.labor_tech_coeff = self.p.localKAUs_var['labor_tech_coeff'][i]
            
            # Aggiunta per SpecialKAU
            # Collego il profilo BOM e lo schedule_MW se l'agente è speciale
            if isinstance(lk, lKAU.SpecialKAU):
                prof = self.p.special_kaus['profiles_by_index'].get(i)
                if prof is None:
                    raise ValueError(f"Manca profiles_by_index per la KAU speciale indice {i}")
                lk.bom_units_per_MW = prof['bom_units_per_MW'].copy()
                lk.power_schedule_MW = list(prof['power_schedule_MW'])
                

                
    def initialize_households(self):
        
        for i,h in enumerate(self.Household_agents):
                        
            h.property_shares = dict(zip(self.Firm_agents.id ,self.p.Households_var['property_shares'][i].copy()))
            h.wealth = self.p.Households_var['wealth'][i]
            #h.dividends = self.p.Households_var['dividends'][i]
            h.wealth2income_target =  self.p.Households_var['wealth2income_target'][i]
            h.csi = self.p.Households_var['csi'][i]
            h.consumption_shares = self.p.Households_var['consumption_shares'][i].copy()
            
            h.my_seller = self.p.Households_var['my_seller'][i].copy()
            
            for com in self.p.Households_var['my_seller'][i].keys():
                
                index = int(self.p.Households_var['my_seller'][i][com])
                h.my_seller[com] = self.seller_agents[index]
                
            h.rationing_threshold = self.p.Households_var['rationing_threshold'][i]
            h.field_of_view = self.p.Households_var['field_of_view'][i]
            h.memory_loss = self.p.Households_var['memory_loss'][i]
            h.opportunism_degree = self.p.Households_var['opportunism_degree'][i]        

            
            for k in h.consumption_shares.keys():
                cands = self.localKAU_agents.select(self.localKAU_agents.my_commodity == k)
                if len(cands) == 0:
                    list_seller = []  # nessun seller locale per k
                else:
                    n_seller = round(h.field_of_view * len(cands))
                    n_seller = max(1, min(n_seller, len(cands)))
                    list_seller = cands.random(n_seller)

                h.sellers_list[k] = [s for s in list_seller]
                # aggiungo sempre RoW come fallback per la commodity k
                h.sellers_list[k].append(self.RoW[0])
                h.qD_final = self.p.import_policy.get('qD_final', 1.0)  # può essere float o dict per commodity

                #print([sell.id for sell in h.sellers_list[k]])
                
            selected = np.random.randint(0,high = self.p.nBanks)
            h.my_bank = self.Bank_agents[selected]
            
            employer_id = self.p.Households_var['employer'][i]
            
            if(employer_id >= 0):
                employer = self.localKAU_agents[self.p.Households_var['employer'][i]]
                h.employer_id = employer.id
                h.flag_employed = 1                
                employer.employees_list.append(h)

    def initialize_banks(self):
        
        for i,b in enumerate(self.Bank_agents):
            
            
            for f in self.Firm_agents:
                
                for ln in f.loans_list:
                    if(ln.id_bank == b.id):
                        b.loans.append(ln)
            
            b.reserves = self.p.Banks_var['reserves'][i] 
            
            for h in self.Household_agents.select(self.Household_agents.my_bank.id == b.id):
                b.deposits[h.id] = h.wealth
                
            for f in self.Firm_agents.select(self.Firm_agents.my_bank.id == b.id):
                b.deposits[f.id] = f.wealth                
            
            
            b.total_deposits = sum([b.deposits[ag] for ag in b.deposits.keys()])    
                
            loans_sum = sum([ln.remaining_amount for ln in b.loans])
            
            b.equity = loans_sum + b.reserves - b.total_deposits
            
            b.CAR = self.p.Banks_var['CAR'][i]
            b.interest_rate = self.p.Banks_var['interest_rate'][i]
            b.threshold = self.p.Banks_var['threshold'][i]
            b.repayment_time = self.p.Banks_var['repayment_time'][i]

    def _init_green_priority(self):
        """Prepara tutte le grandezze di base per la priorità green C+alpha."""

        gp = getattr(self.p, 'green_priority', None)
        if not gp or not gp.get('active', False):
            self._green = {'active': False}
            return

        # Copia "soft" dei parametri
        self._green = dict(gp)
        rows = gp.get('electricity_rows', ['P3', 'P4', 'P12'])
        self._green['rows'] = tuple(rows)

        # Orizzonte temporale dello shock PNIEC
        s0 = int(gp.get('shock_start', 0))
        s1 = int(gp.get('shock_end', s0))
        L  = max(1, s1 - s0 + 1)

        self._green['shock_start'] = s0
        self._green['shock_end']   = s1
        self._green['shock_len']   = L

        # Parametri di ampiezza massima del ribilanciamento
        r_tot = float(gp.get('r_total_max', 0.0))
        gamma_w = float(gp.get('gamma_wind', 0.5))
        gamma_s = float(gp.get('gamma_solar', 0.5))
        norm = max(1e-12, gamma_w + gamma_s)
        gamma_w /= norm
        gamma_s /= norm

        self._green['gamma_wind']  = gamma_w
        self._green['gamma_solar'] = gamma_s

        # Δ quote massime (alla fine dei 60 step)
        delta_s3_max  = gamma_w * r_tot
        delta_s4_max  = gamma_s * r_tot
        delta_s12_max = -(delta_s3_max + delta_s4_max)

        self._green['delta_s3_max']  = delta_s3_max
        self._green['delta_s4_max']  = delta_s4_max
        self._green['delta_s12_max'] = delta_s12_max

        # 1) Intensità elettrica di base per ogni colonna j della C (KAU)
        n = self.p.nKAUs
        C_elec_tot = np.zeros(n)
        s_base = {r: np.zeros(n) for r in rows}

        for j, lk in enumerate(self.localKAU_agents):
            tot = 0.0
            vals = {}
            for r in rows:
                v = float(lk.tech_coeff.get(r, 0.0))
                vals[r] = v
                tot += v
            C_elec_tot[j] = tot
            if tot > 0:
                for r in rows:
                    s_base[r][j] = vals[r] / tot

        self._green['C_elec_tot'] = C_elec_tot
        self._green['s_base'] = s_base

        # 2) Quote elettriche di base nella domanda finale (HH, GOV, RoW)
        def _extract_alpha_elec_from_dict(d):
            arr = np.array([float(d.get(r, 0.0)) for r in rows], dtype=float)
            tot = arr.sum()
            if tot <= 0:
                return 0.0, np.zeros_like(arr)
            return tot, arr / tot

        # Households: assumiamo che tutte le HH abbiano le stesse shares della prima
        if len(self.Household_agents) > 0:
            aH = self.Household_agents[0].consumption_shares
            totH, sH = _extract_alpha_elec_from_dict(aH)
        else:
            totH, sH = 0.0, np.zeros(len(rows))

        aG = self.Government[0].consumption_shares
        totG, sG = _extract_alpha_elec_from_dict(aG)

        aR = self.RoW[0].consumption_shares
        totR, sR = _extract_alpha_elec_from_dict(aR)

        self._green['alpha_elec'] = {
            'H': {'tot': totH, 's_base': sH},
            'G': {'tot': totG, 's_base': sG},
            'R': {'tot': totR, 's_base': sR},
        }

    def _update_green_priority(self):
        """Aggiorna a ogni step C (riga elettrica) e alpha (HH, GOV, RoW)
        in funzione del progresso dello shock PNIEC.
        """

        gp = getattr(self, '_green', None)
        if not gp or not gp.get('active', False):
            return

        t  = self.t
        s0 = gp['shock_start']
        s1 = gp['shock_end']
        L  = gp['shock_len']

        # Fattore di progresso f_t (0 prima, 1 dopo la fine dello shock)
        if t < s0:
            f = 0.0
        elif t >= s1 + 1:
            f = 1.0
        else:
            step_idx = (t - s0 + 1)    # t = s0 -> 1/L, ..., t = s1 -> L/L = 1
            f = max(0.0, min(1.0, step_idx / L))

        gp['f_t'] = f
        if f <= 0.0:
            return

        rows = gp['rows']
        r3, r4, r12 = rows  # ('P3','P4','P12')

        # Δ quote (alla data t) = f_t * Δ quote massime
        ds3 = gp['delta_s3_max']  * f
        ds4 = gp['delta_s4_max']  * f
        ds12 = gp['delta_s12_max'] * f

        # ---------- 1) Aggiorna C: tech_coeff delle KAU ----------

        C_elec_tot = gp['C_elec_tot']
        s_base = gp['s_base']

        for j, lk in enumerate(self.localKAU_agents):
            tot = C_elec_tot[j]
            if tot <= 0:
                continue

            s3_0  = s_base[r3][j]
            s4_0  = s_base[r4][j]
            s12_0 = s_base[r12][j]

            s3_t  = s3_0  + ds3
            s4_t  = s4_0  + ds4
            s12_t = s12_0 + ds12

            # clip su [0,1]
            s3_t  = max(0.0, min(1.0, s3_t))
            s4_t  = max(0.0, min(1.0, s4_t))
            s12_t = max(0.0, min(1.0, s12_t))

            S = s3_t + s4_t + s12_t
            if S <= 0:
                continue

            s3_t  /= S
            s4_t  /= S
            s12_t /= S

            # aggiorna i coefficienti tecnici della riga elettrica
            lk.tech_coeff[r3]  = tot * s3_t
            lk.tech_coeff[r4]  = tot * s4_t
            lk.tech_coeff[r12] = tot * s12_t

        # ---------- 2) Aggiorna alpha di HH, GOV, RoW ----------

        alpha_elec = gp['alpha_elec']

        def _apply_to_dict(d, key):
            info = alpha_elec[key]
            tot_elec = info['tot']
            if tot_elec <= 0:
                return

            s3_0, s4_0, s12_0 = info['s_base']

            s3_t  = s3_0  + ds3
            s4_t  = s4_0  + ds4
            s12_t = s12_0 + ds12

            s3_t  = max(0.0, min(1.0, s3_t))
            s4_t  = max(0.0, min(1.0, s4_t))
            s12_t = max(0.0, min(1.0, s12_t))

            S = s3_t + s4_t + s12_t
            if S <= 0:
                return

            s3_t  /= S
            s4_t  /= S
            s12_t /= S

            # Mantieni costante la quota elettrica totale, cambia solo il mix interno
            d[r3]  = tot_elec * s3_t
            d[r4]  = tot_elec * s4_t
            d[r12] = tot_elec * s12_t

        # Households: aggiorno tutte le HH allo stesso modo
        for h in self.Household_agents:
            _apply_to_dict(h.consumption_shares, 'H')

        # Governo
        _apply_to_dict(self.Government[0].consumption_shares, 'G')

        # RoW
        _apply_to_dict(self.RoW[0].consumption_shares, 'R')

    # ==================================================================
    #  FASE A — Labor-augmenting AI shock
    #  Riduzione progressiva e settoriale di labor_tech_coeff.
    #  Canale teorico: Acemoglu (2025) task-based automation.
    #  Pattern: analogo a _update_green_priority (shock graduale).
    # ==================================================================

    def _init_ai_labor_shock(self):
        """Prepara le grandezze di base per lo shock AI sul lavoro.

        Parametri attesi in self.p.ai_labor_shock (dict):
            active          : bool  — attiva/disattiva lo shock
            shock_start     : int   — step in cui inizia la riduzione
            shock_end       : int   — step in cui la riduzione raggiunge il massimo
            reduction       : array-like (nKAUs,) — riduzione MASSIMA relativa di
                              labor_tech_coeff per ciascuna KAU (es. 0.30 = −30 %)
            floor           : float (opzionale, default 0.0) — valore minimo
                              ammissibile di labor_tech_coeff (evita 0 esatto)
        """
        cfg = getattr(self.p, 'ai_labor_shock', None)
        if not cfg or not cfg.get('active', False):
            self._ai_labor = {'active': False}
            return

        n = self.p.nKAUs

        # Riduzione massima relativa per KAU (array numpy)
        red = np.array(cfg.get('reduction', np.zeros(n)), dtype=float)
        if red.shape[0] != n:
            raise ValueError(
                f"ai_labor_shock.reduction ha dimensione {red.shape[0]}, "
                f"atteso {n}"
            )

        # Orizzonte temporale
        s0 = int(cfg.get('shock_start', 0))
        s1 = int(cfg.get('shock_end', s0))
        L  = max(1, s1 - s0 + 1)

        # Salva i valori di base (pre-shock)
        baseline = np.array(
            [float(lk.labor_tech_coeff) for lk in self.localKAU_agents],
            dtype=float,
        )

        self._ai_labor = {
            'active':      True,
            'shock_start': s0,
            'shock_end':   s1,
            'shock_len':   L,
            'reduction':   red,           # array (nKAUs,) ∈ [0,1]
            'baseline':    baseline,       # array (nKAUs,) valori originali
            'floor':       float(cfg.get('floor', 0.0)),
        }

    def _update_ai_labor_shock(self):
        """Aggiorna labor_tech_coeff di ogni KAU in funzione del progresso
        dello shock AI.  Chiamata all'inizio di Model.step(), PRIMA di
        form_demand_expectation() e make_plans().

        Logica:
            labor_tech_coeff_j(t) = baseline_j * (1 − f_t * reduction_j)
        dove f_t ∈ [0,1] è il fattore di progresso lineare.
        """
        cfg = self._ai_labor
        if not cfg.get('active', False):
            return

        t  = self.t
        s0 = cfg['shock_start']
        s1 = cfg['shock_end']
        L  = cfg['shock_len']

        # Fattore di progresso (identico alla logica green priority)
        if t < s0:
            f = 0.0
        elif t >= s1 + 1:
            f = 1.0
        else:
            f = max(0.0, min(1.0, (t - s0 + 1) / L))

        cfg['f_t'] = f          # salva per eventuale recording

        baseline  = cfg['baseline']
        reduction = cfg['reduction']
        floor     = cfg['floor']

        for j, lk in enumerate(self.localKAU_agents):
            new_val = baseline[j] * (1.0 - f * reduction[j])
            lk.labor_tech_coeff = max(floor, new_val)

    def _agents_with_consumption_budgets(self):
        # Ritorna gli agenti che hanno un dict 'consumption_budgets'
        holders = []
        
        # Households
        for ag in self.Household_agents:
            if hasattr(ag, 'consumption_budgets'):
                holders.append(ag)
        
        # Government
        if hasattr(self.Government[0], 'consumption_budgets'):
            holders.append(self.Government[0])
            
        # RoW
        if hasattr(self.RoW[0], 'consumption_budgets'):
            holders.append(self.RoW[0])
            
        return holders

    def _pool_electricity_budgets(self):
        # Somma i budget elettrici sul 1° della tupla (priorità green)
        if not getattr(self, '_ELEC_GROUP', ()):
            return
        if len(self._ELEC_GROUP) < 2:
            return
        
        first = self._ELEC_GROUP[0]
        holders = self._agents_with_consumption_budgets()
        
        for ag in holders:
            # Sommo i budget delle commodity elettriche presenti
            total = 0.0
            for c in self._ELEC_GROUP:
                if c in ag.consumption_budgets:
                    total += ag.consumption_budgets[c]
            # Sposto tutta la somma sul primo e azzero le altre
            if first in ag.consumption_budgets:
                ag.consumption_budgets[first] = total
            else:
                # se non esiste già la chiave la creo
                ag.consumption_budgets[first] = total
            for c in self._ELEC_GROUP[1:]:
                if c in ag.consumption_budgets:
                    ag.consumption_budgets[c] = 0.0
       
    def _enforce_domestic_electricity_priority(self, commodity):
        """
        Applica la logica:
          - P4, P3: solo seller domestici (niente RoW)
          - P12   : domestici prima, RoW in coda
        per gli agenti con consumption_budgets
        (Households, Government, RoW buyer).
        """

        # Solo per famiglie + governo + RoW (gli stessi che usi per i budgets)
        holders = self._agents_with_consumption_budgets()

        for ag in holders:
            if not hasattr(ag, 'sellers_list'):
                continue
            if commodity not in ag.sellers_list:
                continue

            L = ag.sellers_list[commodity]

            # separo seller domestici e RoW
            dom_sellers = []
            row_sellers = []

            for s in L:
                # classe RoW è RoW.RoW (dal tuo import RoW_copia2 as RoW)
                if isinstance(s, RoW.RoW):
                    row_sellers.append(s)
                else:
                    dom_sellers.append(s)

            if commodity in ('P4', 'P3'):
                # solo domestici
                ag.sellers_list[commodity] = dom_sellers
            elif commodity == 'P12':
                # domestici + RoW in coda
                ag.sellers_list[commodity] = dom_sellers + row_sellers
            else:
                # altre commodity: non tocco nulla
                pass
    
    
    def _shift_residual_budget(self, from_comm, to_comm):
        # Trasferisce il budget residuo non speso da 'from_comm' a 'to_comm'
        holders = self._agents_with_consumption_budgets()
        for ag in holders:
            # Se l'agente non ha quella commodity in budgets, salta
            if from_comm not in ag.consumption_budgets:
                continue
            # Assumiamo che il residuo sia uguale al budget rimasto dopo il round su from_comm, perchè la spesa è scalata dai metodi buy_* durante il market
            residual = ag.consumption_budgets[from_comm]
            if residual <= 0:
                continue
            # Azzero la vecchia commodity e sposto il residuo su "to_comm"
            ag.consumption_budgets[from_comm] = 0.0
            ag.consumption_budgets[to_comm] = ag.consumption_budgets.get(to_comm, 0.0) + residual
            
    def _pool_electricity_demands_KAUs(self):
        # Sommo le domande elettriche delle KAU sul 1° della tupla (priorità green)
        if not getattr(self, '_ELEC_GROUP', ()):
            return
        if len(self._ELEC_GROUP) < 2:
            return
        
        first = self._ELEC_GROUP[0]
        for lk in self.localKAU_agents:
            if not hasattr(lk, 'demanded_quantity'):
                continue
            
            # Sommo le domande sulle commodity elettriche presenti
            total = 0.0
            for c in self._ELEC_GROUP:
                total += lk.demanded_quantity.get(c, 0.0)
                
            if total > 0.0:
                lk.demanded_quantity[first] = total
                # Azzero le altre del gruppo
                for c in self._ELEC_GROUP[1:]:
                    if c in lk.demanded_quantity:
                        lk.demanded_quantity[c] = 0.0
                        
                # Ricalcolo coerente di total_demanded_quantity e capital_quote
                if hasattr(lk, 'plan_total_demanded_quantities'):
                    lk.plan_total_demanded_quantities()
                        
    def _shift_residual_demand_KAUs(self, from_comm, to_comm):
        # Trasferisce la domanda residua non soddisfatta da "from_comm" a "to_comm"
        for lk in self.localKAU_agents:
            if not hasattr(lk, 'demanded_quantity'):
                continue
            residual = lk.demanded_quantity.get(from_comm, 0.0)
            if residual > 0.0:
                lk.demanded_quantity[from_comm] = 0.0
                lk.demanded_quantity[to_comm] = lk.demanded_quantity.get(to_comm, 0.0) + residual
                
        
    def step(self):
        
        
        
        if(self.p.shocks['active']):
            
            if(self.shocks_counter < self.p.shocks['number'] and np.mod(self.t-2, self.p.shocks['frequency']) == 0):                
                
                if(self.p.shocks['agents'] == 'Household'):               
                    
                    self.Household_agents.wealth += self.p.shocks['quantity']/self.p.nHouseholds
                    self.shocks_counter += 1
                    print(self.t, ' Shocks activated')
        
        # --- ADD all’inizio di MyModel.step() ---
        for f in self.Firm_agents:
            f.loans_received_step = 0.0
            f.repayments_step     = 0.0
            f.dividends_paid_step = 0.0
        # --- gruppi HH: 5 gruppi da 400 (2000 HH totali)
        hh_per_group = 400
        bounds = [(g*hh_per_group, (g+1)*hh_per_group) for g in range(5)]
        def _sum_group(attr_getter):
            vals = []
            for (a,b) in bounds:
                s = 0.0
                # self.Household_agents è indicizzabile; se non lo fosse, usa list(self.Household_agents)[a:b]
                for h in self.Household_agents[a:b]:
                    s += float(attr_getter(h))
                vals.append(s)
            return vals
    
        self._update_green_priority()
        self._update_ai_labor_shock()     # FASE A: aggiorna labor_tech_coeff
        
        self.localKAU_agents.form_demand_expectation()
        
        self.localKAU_agents.make_plans()
        
        #self._pool_electricity_demands_KAUs()
        
        self.localKAU_agents.compute_liquidity_needs()

        self.Firm_agents.send_credit_request()
        
        # Labor market round
        self.Household_agents.select(self.Household_agents.flag_employed ==0).search_job()
 
        # Tracking disoccupati
        unemployed = len(self.Household_agents.select(self.Household_agents.flag_employed == 0))
        self.record('unemployed', float(unemployed))
        self.record('unemployment_rate', unemployed / float(self.p.nHouseholds))

        self.Firm_agents.execute_financial_payments()
        
        # Aggregato per il grafico “totale dividendi firm” dello step
        tot_firm_divs = sum(max(0.0, getattr(f, 'dividends_paid_step', 0.0)) for f in self.Firm_agents)
        self.Firm_agents.record('Firms_dividends_total', float(tot_firm_divs))
        self.Government.record('Firms_dividends_total', float(tot_firm_divs))
        
        def _sum_firms_cash(model):
            tot = 0.0
            for f in model.Firm_agents:
                tot += float(getattr(f, 'cash', 0.0))
                tot += sum(float(v) for v in getattr(f, 'cash_for_KAU', {}).values())
            return tot

        hh_after_income = float(sum(h.wealth for h in self.Household_agents))
        gov_after_income = float(self.Government[0].liquidity)
        firms_after_income = _sum_firms_cash(self)
        self.record('HH_liq_after_income', hh_after_income)
        self.record('GOV_liq_after_income', gov_after_income)
        self.record('FIRMS_liq_after_income', firms_after_income)
        self.record('DOMESTIC_liq_after_income', hh_after_income + gov_after_income + firms_after_income)

        self.Bank_agents.distribute_dividends()
        
        self.localKAU_agents.produce()
        
        self.localKAU_agents.set_price()
        
        # --- MONTE SALARI / DIVIDENDI DEL PERIODO (prima che le HH azzerino wage/dividends)
        self.monte_salari_t    = sum(max(0.0, h.wage)      for h in self.Household_agents)
        self.monte_dividendi_t = sum(max(0.0, h.dividends) for h in self.Household_agents)
        self.record('monte_salari',    float(self.monte_salari_t))
        self.record('monte_dividendi', float(self.monte_dividendi_t))
        self.y_w = (self.monte_salari_t)/(sum(self.Household_agents.income))
        self.record('y_w', float(self.y_w))
        
        self.Government.record('wages_total', float(self.monte_salari_t))  # wages totali
        
        self.Household_agents.determine_consumption_budgets()
        
        # reddito netto pre transfers
        hh_net = sum(max(0.0, getattr(h, 'disposable_income', 0.0)) for h in self.Household_agents)
        self.record('Reddito netto HH', float(hh_net))
        self.Household_agents.record('disposable_income')
        # Reddito lordo: sommo h.income
        gross_by_g = _sum_group(lambda h: getattr(h, 'income', 0.0))
        # # # Reddito netto: sommo h.disposable_income (calcolato da determine_consumption_budgets)
        net_by_g   = _sum_group(lambda h: getattr(h, 'disposable_income', 0.0))
        
        for g in range(5):
            self.record(f'HH_G{g+1}_income_gross', float(gross_by_g[g]))
            self.record(f'HH_G{g+1}_income_net',   float(net_by_g[g]))

        # tassa lavoro
        labor_tax_total = sum(max(0.0, h.labor_tax) for h in self.Household_agents)
        self.Government.record('labor_tax', float(labor_tax_total))
        
        # tassa dividendi
        dividends_tax_total = sum(max(0.0, h.dividend_tax) for h in self.Household_agents)
        self.Government.record('dividends_tax', float(dividends_tax_total))
        
        self.localKAU_agents.adjust_demanded_quantity()
        
        self.localKAU_agents.depreciate_capital()
        
        self.localKAU_agents.commit_own_capital()
        
        self.Government[0].transfers_paid_step = 0.0
        self.Government[0].unemployment_paid_step = 0.0
        
        g = self.Government[0]
        self.record('Gov_liquidity_pre_transfers', float(g.liquidity))  # cash disponibile prima delle erogazioni
        

        self.Government[0].distribute_unemployment_benefits()
        
        self.Government[0].distribute_transfers()
        
        self.record('Gov_unemployment_paid', float(self.Government[0].unemployment_paid_step))  # 3) registra grafici
        self.record('Gov_transfers_paid',    float(self.Government[0].transfers_paid_step))
        
        self.record('Gov_transfers_total',
            float(self.Government[0].unemployment_paid_step + self.Government[0].transfers_paid_step))
        
        self.Government[0].determine_consumption_budgets()
        
        g = self.Government[0]
        self.record('gov_liquidity_for_spending', float(g.consumption_budget))
        
        self.RoW[0].determine_consumption_budgets()
        
        for h in self.Household_agents:
            h.spent_to_RoW_step = 0.0
            h.spent_to_RoW_by_comm_step = {}
        for lk in self.localKAU_agents:
            lk.spent_to_RoW_step = 0.0
            lk.spent_to_RoW_by_comm_step = {}
            lk.capital_purchase_by_KAU = {}
            
        # reset tracking import per il periodo
        self.Government[0].spent_to_RoW_step = 0.0
        self.Government[0].spent_to_RoW_by_comm_step = {}
    
        elec_group = tuple(getattr(self, '_ELEC_GROUP', ()))
       # elec_group   = tuple(getattr(self, '_ELEC_GROUP', ()))
        green_start  = getattr(self.p, 'green_start', 1)

        if len(elec_group) < 2 or self.t < green_start:
            # COMPORTAMENTO ORIGINALE: tutte le commodity trattate allo stesso modo
            for commodity in self.p.commodities_list:
                self.buyer_agents.reset_market_vars()
                self.buyer_agents.update_sellers_list(commodity)
                for n in range(self.round_number):
                    self.buyer_agents.random(self.nBuyers).buy(commodity)
        else:
            # 1) commodity NON elettriche
            for commodity in self.p.commodities_list:
                if commodity in elec_group:
                    continue
                self.buyer_agents.reset_market_vars()
                self.buyer_agents.update_sellers_list(commodity)
                for n in range(self.round_number):
                    self.buyer_agents.random(self.nBuyers).buy(commodity)

            # 2) gruppo elettrico con priorità green
            self._pool_electricity_budgets()
            for j, commodity in enumerate(elec_group):
                self.buyer_agents.reset_market_vars()
                self.buyer_agents.update_sellers_list(commodity)
                
                self._enforce_domestic_electricity_priority(commodity)
                
                for n in range(self.round_number):
                    self.buyer_agents.random(self.nBuyers).buy(commodity)
                    
                if j < len(elec_group) - 1:
                    nxt = elec_group[j+1]
                    self._shift_residual_budget(commodity, nxt)
                    #self._shift_residual_demand_KAUs(commodity, nxt)
    
        # # Gestiamo prima tutte le commodity non elettriche normalmente
        # for commodity in self.p.commodities_list:
        #     if commodity in elec_group:
        #         continue  # si fa dopo
        #     # Reset variabili di mercato per tutti i buyer
        #     self.buyer_agents.reset_market_vars()
        #     # Ogni buyer aggiorna la sua sellers_list per questa commodity
        #     self.buyer_agents.update_sellers_list(commodity)
        #     # round di matching come nella versione originale di step()
        #     for n in range(self.round_number):
        #         self.buyer_agents.random(self.nBuyers).buy(commodity)
                
        # # Ora gestisco il gruppo elettrico con priorità green
        # if len(elec_group) >= 2:
        #     # Accorpo tutti i budget elettrici sul primo della tupla (es. solare)
        #     self._pool_electricity_budgets()
                
        #     # Ciclo le commodity elettriche in ordine
        #     for j, commodity in enumerate(elec_group):
        #         # Market round per questa commodity elettrica
        #         self.buyer_agents.reset_market_vars()
        #         self.buyer_agents.update_sellers_list(commodity)
        #         for n in range(self.round_number):
        #             self.buyer_agents.random(self.nBuyers).buy(commodity)
                        
        #         # Se c'è una prossima commodity elettrica sposto il residuo
        #         if j < len(elec_group) - 1:
        #             nxt = elec_group[j + 1]
        #             self._shift_residual_budget(commodity, nxt)
        #             self._shift_residual_demand_KAUs(commodity, nxt)
        # ----------------------------   
        imp_HH  = sum(h.spent_to_RoW_step for h in self.Household_agents)
        imp_KAU = sum(lk.spent_to_RoW_step for lk in self.localKAU_agents)
        imp_GOV = self.Government[0].spent_to_RoW_step
        
        self.imports_value_HH     = imp_HH
        self.imports_value_KAU    = imp_KAU
        self.imports_value_GOV    = imp_GOV
        self.imports_value_total  = imp_HH + imp_KAU + imp_GOV
        
        # usa lo stesso meccanismo con cui registri GDP
        self.record('imports_value_HH', self.imports_value_HH)
        self.record('imports_value_KAU', self.imports_value_KAU)
        self.record('imports_value_GOV', self.imports_value_GOV)
        self.record('imports_value_total', self.imports_value_total)    

        # consumo domestico e totale del governo
        gov = self.Government[0]
        self.record('Gov_consumption_domestic', float(gov.spent_domestic_step))
        self.record('Gov_consumption_total',    float(gov.spent_domestic_step + gov.spent_to_RoW_step))
        exports_t = float(self.RoW[0].spent_domestic_step)
        self.record('exports_value_total', float(self.RoW[0].spent_domestic_step))
        net_foreign_flow_t = exports_t - self.imports_value_total
        if not hasattr(self, 'cum_net_foreign_flow'):
            self.cum_net_foreign_flow = 0.0
        self.cum_net_foreign_flow += net_foreign_flow_t
        self.record('net_foreign_flow', float(net_foreign_flow_t))
        self.record('cum_net_foreign_flow', float(self.cum_net_foreign_flow))
        
        # Consumo realizzato nello step (dopo il mercato)
        cons_by_g = _sum_group(lambda h: getattr(h, 'consumption', 0.0))
        for g in range(5):
            self.record(f'HH_G{g+1}_consumption', float(cons_by_g[g]))

        self.localKAU_agents.update_prices()
        
        self.localKAU_agents.compute_earnings() 
        
        # Ricavi lordi
        rev_tot = sum(max(0.0, lk.revenues) for lk in self.localKAU_agents)
        self.Government.record('KAU_revenues_total', float(rev_tot))
        
        
        # tassa VAT
        vat_total = sum(max(0.0, lk.VAT) for lk in self.localKAU_agents)
        self.Government.record('VAT_tax', float(vat_total))

        # tassa corporate e utili netti KAU
        net_total = float(sum(max(0.0, lk.net_earnings) for lk in self.localKAU_agents))
        corp_due  = float(sum(max(0.0, lk.income_tax)   for lk in self.localKAU_agents))

        self.Government.record('utili netti totali (KAU)', net_total)
        self.Government.record('corporate_tax',  corp_due)

        
        self.localKAU_agents.revaluate_inputs_stocks()
        
        self.Firm_agents.update_loans_age()
        
        self.Bank_agents.update_loans_list()
        
        # --- PRESTITI: registrazione per grafici (fine step) ---
        self.Firm_agents.record('loans_received_step')
        self.Firm_agents.record('repayments_step')

        tot_granted = sum(f.loans_received_step for f in self.Firm_agents)
        tot_repaid  = sum(f.repayments_step     for f in self.Firm_agents)
        self.Bank_agents.record('prestiti_concessi_aggregati', float(tot_granted))
        self.Bank_agents.record('prestiti_ripagati_aggregati',  float(tot_repaid))
        self.Bank_agents.record('Delta_prestiti', float(tot_granted) - float(tot_repaid))

        if not hasattr(self, 'cum_prestiti_concessi'):
            self.cum_prestiti_concessi = 0.0
            self.cum_prestiti_ripagati = 0.0
            self.cum_delta_prestiti    = 0.0

        self.cum_prestiti_concessi += float(tot_granted)
        self.cum_prestiti_ripagati += float(tot_repaid)
        self.cum_delta_prestiti    += float(tot_granted) - float(tot_repaid)
        self.Bank_agents.record('Prestiti_concessi_cumulati', float(self.cum_prestiti_concessi))
        self.Bank_agents.record('Prestiti_ripagati_cumulati', float(self.cum_prestiti_ripagati))
        self.Bank_agents.record('Delta_prestiti_cumulato',    float(self.cum_delta_prestiti))

    
        self.record('HH_liquidity_pre_tax',  float(sum(h.wealth for h in self.Household_agents)))
        
        hh_pre_taxes = float(sum(h.wealth for h in self.Household_agents))
        gov_pre_taxes = float(self.Government[0].liquidity)
        firms_pre_taxes = _sum_firms_cash(self)
        self.record('HH_liq_pre_taxes', hh_pre_taxes)
        self.record('GOV_liq_pre_taxes', gov_pre_taxes)
        self.record('FIRMS_liq_pre_taxes', firms_pre_taxes)
        self.record('DOMESTIC_liq_pre_taxes', hh_pre_taxes + gov_pre_taxes + firms_pre_taxes)

        # Ricchezza pre-tasse (dopo mercato, prima dei pagamenti fiscali)
        wealth_pre_by_g = _sum_group(lambda h: getattr(h, 'wealth', 0.0))
        for g in range(5):
            self.record(f'HH_G{g+1}_wealth_pre_tax', float(wealth_pre_by_g[g]))

        self.Household_agents.pay_taxes()
        
        self.localKAU_agents.pay_taxes()
        
        self.Government.record('taxes_collected', float(self.Government[0].taxes))
        
        self.Government[0].make_period_account()
        
        self.record('Reddito lordo HH', sum(self.Household_agents.income))
        
        hh_end = float(sum(h.wealth for h in self.Household_agents))
        gov_end = float(self.Government[0].liquidity)
        firms_end = _sum_firms_cash(self)
        self.record('HH_liq_end', hh_end)
        self.record('GOV_liq_end', gov_end)
        self.record('FIRMS_liq_end', firms_end)
        self.record('DOMESTIC_liq_end', hh_end + gov_end + firms_end)
        
        # Ricchezza post-tasse (fine step)
        wealth_end_by_g = _sum_group(lambda h: getattr(h, 'wealth', 0.0))
        for g in range(5):
            self.record(f'HH_G{g+1}_wealth_end', float(wealth_end_by_g[g]))

        # Tasse incassate
        self.Government.record('labor_collected', labor_tax_total)
        self.Government.record('dividends_collected', dividends_tax_total)
        self.Government.record('VAT_collected', vat_total)
        self.Government.record('corporate_collected', corp_due)
        
        
    def update(self):
        
        
        # MACRO VARIBLES
        self.record('Nominal Production', sum(self.localKAU_agents.production*self.localKAU_agents.price))
        self.record('Total Revenues', sum(self.localKAU_agents.revenues))
        #self.record('Intermediate consumption', sum(sum([self.localKAU_agents.inputs_consumption[k] for k in self.localKAU_agents.inputs_consumption.keys()])))
        self.record('Total costs', sum(self.localKAU_agents.total_costs))
        self.record('GDP', sum(self.Household_agents.income))
        self.record('Firms liquidity', sum(self.Firm_agents.wealth))
        self.record('Households liquidity', sum(self.Household_agents.wealth))
        self.record('Total liquidity',sum(self.Firm_agents.wealth) +  sum(self.Household_agents.wealth) + self.Government[0].liquidity)
        #@self.record('Integral', self.calculate_integral())
        self.record('Consumption', sum(self.Household_agents.consumption))
        
        # SECTORIAL VARIABLES
        for com in self.p.commodities_list:
            self.record('Real production of '+ com, sum(self.localKAU_agents.select(self.localKAU_agents.my_commodity == com).production))
            #self.record('Nominal production of'+ com, sum(self.localKAU_agents.select(self.localKAU_agents.my_commodity == com).production*self.localKAU_agents.select(self.localKAU_agents.my_commodity == com).price)            
        
        # FIRMS
        
        self.Firm_agents.record('wealth')
        self.Firm_agents.compute_total_debt()
        self.Firm_agents.record('debt',)
        total_firm_debt = float(sum(max(0.0, f.debt) for f in self.Firm_agents))
        self.Bank_agents.record('Firms_debt_aggregato', total_firm_debt)
        self.Firm_agents.compute_wealth_from_dep()
        self.Firm_agents.record('deposit')
        self.Firm_agents.record('dividends')
    
        # HOUSEHOLDS   
     
        self.Household_agents.record('consumption')
        self.Household_agents.record('wealth')
        self.Household_agents.record('income')
        self.Household_agents.record('consumption_budget')       
 
        # # LOCAL KAU VARIABLES
       
        self.localKAU_agents.record('production')
        self.localKAU_agents.record('price')
        self.localKAU_agents.record('markup')
        self.localKAU_agents.record('supply')
        self.localKAU_agents.record('previous_demand')
        self.localKAU_agents.record('earnings')
        # vendite per KAU (ci serve per la priorità green)
        self.localKAU_agents.record('sold_quantity')

        # Investimenti in beni capitali delle altre KAU (per commodity)
        for lk in self.localKAU_agents:
            for com in self.p.commodities_list:

                # trovo la KAU che produce questa commodity
                sellers = self.localKAU_agents.select(self.localKAU_agents.my_commodity == com)
                if len(sellers) == 0:
                    qty = 0.0
                else:
                    seller = sellers[0]   # 1:1 KAU-commodity
                    if seller.id == lk.id:
                        # non vogliamo contare l’investimento sul proprio bene
                        qty = 0.0
                    else:
                        # quanto capitale di quella KAU ho comprato in questo step
                        qty = float(lk.capital_purchase_by_KAU.get(seller.id, 0.0))

                # ✅ registriamo comunque un valore per TUTTE le KAU, SEMPRE
                lk.record(f'capinv_cap_{com}', qty)

                # metriche specifiche per le KAU speciali (solare/eolico)
        for lk in self.localKAU_agents:
            if isinstance(lk, lKAU.SpecialKAU):
                # MW equivalenti installati
                lk.record('installed_MW',      lk._installed_MW_this_period)
                lk.record('installed_MW_cum',  lk._installed_MW_cum)

                # domanda extra di capitale (solo shock PNIEC)
                lk.record('extra_capital_demand',  lk._extra_capital_demand_t)

                # flusso di investimenti in capitale nel periodo
                lk.record('capital_purchase_flow',  lk.capital_purchase_flow)

                # investimento cumulato da inizio simulazione
                lk.record('capital_purchase_total', lk.capital_purchase_cum)


        for lk in self.localKAU_agents:
            lk.record('no_employees', len(lk.employees_list))
        
        # --- FASE A: recording variabili AI labor-augmenting ---
        for lk in self.localKAU_agents:
            lk.record('labor_tech_coeff', lk.labor_tech_coeff)
        
        ai_cfg = getattr(self, '_ai_labor', {})
        if ai_cfg.get('active', False):
            self.record('ai_labor_f_t', float(ai_cfg.get('f_t', 0.0)))
            # labor_tech_coeff medio ponderato (pesato per produzione)
            tot_prod = sum(max(0.0, lk.production) for lk in self.localKAU_agents)
            if tot_prod > 0:
                avg_ltc = sum(
                    lk.labor_tech_coeff * max(0.0, lk.production)
                    for lk in self.localKAU_agents
                ) / tot_prod
            else:
                avg_ltc = float(np.mean([lk.labor_tech_coeff for lk in self.localKAU_agents]))
            self.record('avg_labor_tech_coeff', avg_ltc)
        # --- fine recording Fase A ---

        for lk in self.localKAU_agents:
            for com in self.p.commodities_list:
                lk.record(com+' stock', lk.commodities_stock[com])
        for lk in self.localKAU_agents:
            for com in self.p.commodities_list:
                lk.record(com+' cap_stock', lk.capital_stocks[com])
        int_cons = 0
        for lk in self.localKAU_agents:
            for com in self.p.commodities_list:
                lk.record( com + ' consumption', lk.inputs_consumption[com])
                int_cons += lk.inputs_consumption[com]
        self.record('Int_cons', int_cons)
        
        for f in self.Firm_agents:
            for lk in f.KAU_list:
                lk.record('wealth', f.cash_for_KAU[lk.id])
                
                
        ## BANK VARIABLES
        
        self.Bank_agents.record('dividends')
        self.Bank_agents.record('reserves')
        self.Bank_agents.compute_total_deposits()
        self.Bank_agents.record('total_deposits')
                
                
    def calculate_integral(self):
        
        integral = 0
        
        for com in self.p.commodities_list:
            for lk in self.localKAU_agents:
                integral += lk.inputs_consumption[com]
            
        integral += sum(self.Household_agents.consumption_budget)
        integral += sum(self.Household_agents.wealth)
        
        return integral
       
        
    def end(self):
        
        self.Household_agents.record('wealth')
        self.Household_agents.record('income')        
        
        return
        