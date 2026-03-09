# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 15:48:50 2025

@author: frado
"""


import numpy as np
import agentpy as ap
import random as random

import math as math

class LocalKAU(ap.Agent):
    
    def setup(self):
        
        #STOCKS      
        self.commodities_stock = {}
        self.commodities_stock_value = {}

        
        #FLOWS
        self.previous_demand = 0
        self.production_planned = 0
        self.supply = 0        
        self.production = 0  
        self.total_costs = 0
        self.revenues = 0
        self.earnings = 0
        self.net_earnings = 0
        self.sold_quantity = 0 
        self.inputs_consumption = {}
        self.total_expenditure = {}
        self.demanded_quantity = {}


        #PRICES
        self.prices = {}  
        self.price = 0        
        self.my_commodity_stock_value_old = 0
        self.unit_cost = 0        
        self.markup = 0
        
        # PARAMETERS
        self.tech_coeff = {}      

        
        self.my_activity = ''
        self.my_commodity = ''
        self.owner_id = -1
       
        self.my_seller = {}
        self.attempt_number = 0
        self.rationing_level = 0
        self.rationing_threshold = 0
        self.sellers_list = {}
        self.field_of_view = 0
        self.memory_loss = 0
        self.opportunism_degree = 0
        
        self.expected_demand = 0
        self.independence_periods = 0
        self.target_speed = 0
        self.expectation_error = 0        
        self.target_stock = {}
        
        # CAPITAL
        self.capital_coeff = {}
        self.capital_depreciation = {}     
        self.target_capital = {}
        self.capital_purchase = {}
        self.capital_demanded_quantity =  {}
        self.capital_stocks = {}
        self.capital_stocks_value = {}
        self.target_capacity_utilization = 0
        self.capital_quote = {}
        self.total_demanded_quantity = {}
        self.cap_adjust_speed = 0.7  # 0..1: velocità con cui colmiamo il gap di capitale
        self.own_capital_buffer = {}
        
        self.my_firm = None
        self.spent_to_RoW_step = 0.0
        self.spent_to_RoW_by_comm_step = {}
        self.depreciation_expense = 0.0
        
        # Labor
        self.flag_vacancies = 0
        self.wage_offer = 0
        self.labor_demand = 0
        self.employees_list = []
        self.labor_tech_coeff = 0
        self.max_straordinari = 0.3
        self.total_wage_payment = 0.0

        self.capital_purchase_by_KAU = {}
        
##############################
# DEMAND EXPECTATIONS FORMATION
##############################
 
    def form_demand_expectation(self):
        
        self.expectation_error = self.previous_demand - self.expected_demand
        if(self.previous_demand == 0):
            if(self.expected_demand == 0):
                self.expectation_error = 0 
            else:
                self.expectation_error = -1
        else:
            self.expectation_error = self.expectation_error/self.previous_demand
        
        self.expected_demand = self.previous_demand
        
        self.previous_demand = 0
        

##############################
# PLANS METHODS
##############################

    def set_stock_targets(self):
    
        for comm in self.commodities_stock.keys():
        
            self.target_stock[comm] = self.independence_periods*self.tech_coeff[comm]*self.expected_demand/(1-self.tech_coeff[self.my_commodity])
 
    def set_capital_targets(self):
        
        for comm in self.capital_stocks.keys():
            #den = self.target_capacity_utilization
            den = (1 - self.tech_coeff[self.my_commodity]) * self.target_capacity_utilization
            self.target_capital[comm] = self.capital_coeff[comm] * self.expected_demand / den if den > 0 else 0.0

    # def plan_production(self):
        
    #     # --- (A) eventuale aggiustamento stock IO della propria commodity ---
    #     # Se vuoi replicare il comportamento "vecchio" che ti dava lo pseudo-stazionario,
    #     # puoi tranquillamente mettere delta_stock = 0.0
    #     # così la produzione NON cerca di portare lo stock IO della propria commodity al target.
    #     delta_stock = 0.0
    #     # Se in futuro vuoi riattivarlo, basta scommentare le due righe successive:
    #     # delta_stock = self.target_speed * (self.target_stock[self.my_commodity] - self.commodities_stock[self.my_commodity])

    #     # --- (B) componente per capitale sulla PROPRIA commodity ---
    #     self.delta_capital_stock_own = 0.0  # salvo per usarla dopo in produce()
        
    #     if self.capital_coeff.get(self.my_commodity, 0.0) > 0.0:
    #         K      = self.capital_stocks.get(self.my_commodity, 0.0)
    #         deltaK = self.capital_depreciation.get(self.my_commodity, 0.0)
    #         K_star = self.target_capital.get(self.my_commodity, 0.0)

    #         # rimpiazzo del deprezzamento + aggiustamento verso K*
    #         invest_raw = K * deltaK + self.target_speed * (K_star - K)
    #         self.delta_capital_stock_own = max(0.0, invest_raw)

    #     # --- (C) produzione "Leontief" per domanda + scorte IO + capitale proprio ---
    #     denom = (1.0 - self.tech_coeff[self.my_commodity])
    #     num   = self.expected_demand + delta_stock + self.delta_capital_stock_own

    #     if denom > 0.0:
    #         self.production_planned = max(0.0, num / denom)
    #     else:
    #         # fallback prudente, se mai capitasse denom<=0
    #         self.production_planned = 0.0

    #     # --- (D) vincoli da input intermedi e capitale esistente ---
    #     Prod_max = min([
    #         self.commodities_stock[k] / self.tech_coeff[k] if self.tech_coeff[k] != 0 else math.inf
    #         for k in self.commodities_stock.keys()
    #     ]) if self.commodities_stock else math.inf

    #     cap_keys = list(self.capital_stocks.keys())
    #     Prod_max_capital = (
    #         min([
    #             self.capital_stocks[k] / self.capital_coeff[k]
    #             if self.capital_coeff.get(k, 0) != 0 else math.inf
    #             for k in cap_keys
    #         ]) if cap_keys else math.inf
    #     )

    #     self.production_planned = min(Prod_max, Prod_max_capital, self.production_planned)

    # def plan_production(self):
    #     comm = self.my_commodity        
    #     delta_stock = self.target_speed*(self.target_stock[self.my_commodity] - self.commodities_stock[self.my_commodity])
        
    #     need_own = float(self.capital_demanded_quantity.get(comm, 0.0))
        
    #     delta_capital_stock = 0
    #     if(self.capital_coeff[self.my_commodity]>0):
    #         delta_capital_stock = self.target_speed*(self.target_capital[self.my_commodity] - self.capital_stocks[self.my_commodity])
        
    #     self.production_planned = (self.expected_demand + delta_stock + need_own + delta_capital_stock)/(1-self.tech_coeff[self.my_commodity])
    #     self.production_planned = max(self.production_planned, 0)

    #     Prod_max = min([self.commodities_stock[k]/self.tech_coeff[k] if self.tech_coeff[k]!=0 else math.inf for k in self.commodities_stock.keys()])    #updated 3 Jun 24 
    #     cap_keys = list(self.capital_stocks.keys())
    #     Prod_max_capital = (
    #         min([self.capital_stocks[k]/self.capital_coeff[k] if self.capital_coeff.get(k,0)!=0 else math.inf for k in cap_keys])
    #         if cap_keys else math.inf
    #     )
 
    #     self.production_planned = min(Prod_max, Prod_max_capital, self.production_planned)

    def plan_production(self):
        comm = self.my_commodity        
        need_own = float(self.capital_demanded_quantity.get(comm, 0.0))
        
        self.production_planned = (self.expected_demand + need_own)/(1-self.tech_coeff[self.my_commodity])
        self.production_planned = max(self.production_planned, 0)

        Prod_max = min([self.commodities_stock[k]/self.tech_coeff[k] if self.tech_coeff[k]!=0 else math.inf for k in self.commodities_stock.keys()])    #updated 3 Jun 24 
        cap_keys = list(self.capital_stocks.keys())
        Prod_max_capital = (
            min([self.capital_stocks[k]/self.capital_coeff[k] if self.capital_coeff.get(k,0)!=0 else math.inf for k in cap_keys])
            if cap_keys else math.inf
        )
 
        self.production_planned = min(Prod_max, Prod_max_capital, self.production_planned)
                
        
    def plan_demanded_quantities(self):
        for comm in self.commodities_stock.keys():
            if comm == self.my_commodity:
                self.demanded_quantity[comm] = 0.0  # azzera per sicurezza
                continue
            self.demanded_quantity[comm] = self.plan_demanded_quantity(comm)
        
    def plan_demanded_quantity(self, commodity):
        
        demanded_quantity = self.production_planned*self.tech_coeff[commodity] + self.target_speed*(self.target_stock[commodity] - self.commodities_stock[commodity])
        
        demanded_quantity = max(0,demanded_quantity)
        
        return demanded_quantity
    
    def plan_demanded_capital_quantities(self):
        for comm in self.capital_stocks.keys():
            self.capital_demanded_quantity[comm] = self.plan_demanded_capital_quantity(comm)

    def plan_demanded_capital_quantity(self, commodity):
        # (i) rimpiazzo del deprezzamento
        base = self.capital_stocks[commodity] * self.capital_depreciation[commodity]

        # (ii) fabbisogno minimo per sostenere la domanda attesa a u*
        # K_req = b_ij * E[Y] / ((1 - a_jj) * u*)
        u = max(1e-12, float(self.target_capacity_utilization))
        den = (1.0 - self.tech_coeff.get(self.my_commodity, 0.0)) * u
        K_req = (self.capital_coeff.get(commodity, 0.0) * self.expected_demand / den) if den > 0 else 0.0
        # gap  = max(0.0, K_req - self.capital_stocks.get(commodity, 0.0))
        gap  = K_req - self.capital_stocks.get(commodity, 0.0)
        # (iii) regola: chiedi almeno il rimpiazzo, e in più colma il gap "on-demand"
        adj_speed = getattr(self, 'cap_adjust_speed', 1.0)  # 0..1
        demanded_quantity = base + adj_speed * gap
        
        return max(0.0, demanded_quantity)
    
    # def plan_demanded_capital_quantity(self, commodity):
        
    #     demanded_quantity = self.capital_stocks[commodity]*self.capital_depreciation[commodity] + self.target_speed*(self.target_capital[commodity] - self.capital_stocks[commodity])
        
    #     demanded_quantity = max(0,demanded_quantity)
        
    #     return demanded_quantity
    
    def plan_total_demanded_quantities(self):
        keys = (set(self.demanded_quantity.keys()) | set(self.capital_demanded_quantity.keys())) - {self.my_commodity}
        # azzera eventuali residui da step precedenti
        self.total_demanded_quantity[self.my_commodity] = 0.0
        self.capital_quote[self.my_commodity] = 0.0
        for comm in keys:
            dq  = self.demanded_quantity.get(comm, 0.0)
            cdq = self.capital_demanded_quantity.get(comm, 0.0)
            tot = dq + cdq
            self.total_demanded_quantity[comm] = tot
            self.capital_quote[comm] = (cdq / tot) if tot > 0 else 0.0


    def plan_labor_demand(self):
        
        no_employees = len(self.employees_list)
        
        no_employees_needed = self.production_planned*self.labor_tech_coeff
        
        no_employees_gap = no_employees_needed - no_employees
        
        print('Test KAU ',self.id, no_employees,no_employees_needed, no_employees_gap)
        if(no_employees_gap<0):
            no_firings = int(-no_employees_gap)
            
            for i in range(no_firings):
                
                removed = self.employees_list.pop(np.random.randint(0, len(self.employees_list)))
                removed.update_employement_status()
        
            self.labor_demand = 0
            self.flag_vacancies = 0
            
        else:
            self.labor_demand = int(no_employees_gap) + 1
            self.flag_vacancies = 1        


    def make_plans(self):
    
        self.set_stock_targets()
        self.set_capital_targets()
        self.plan_demanded_capital_quantities()
        self.plan_production()
        self.plan_demanded_quantities()
        #self.plan_demanded_capital_quantities()
        self.plan_total_demanded_quantities()
        self.plan_labor_demand()
        
        
##############################
# LIQUIDITY NEEDS
##############################        


    def compute_liquidity_needs(self):
        
        # liquidity for expanding the input-output stock
        liquidity_needs = self.price*self.target_speed*(self.target_stock[self.my_commodity] - self.commodities_stock[self.my_commodity])        
        liquidity_needs = max(0, liquidity_needs)
        
        
        #liquidity for inputs purchases
        for comm in self.commodities_stock.keys():
            
            if(comm != self.my_commodity):                
                
                liquidity_needs += self.prices[comm]*self.total_demanded_quantity[comm]
        
        # liquidity 4 labor payment
        
        liquidity_needs += self.wage_offer*self.production_planned*self.labor_tech_coeff
                
        
        
        self.my_firm.gather_KAU_request(self.id, liquidity_needs)
        
      
##############################
# HIRINGS AND WAGE PAYMENTS
##############################     

    def hire(self, ag):
        
        self.employees_list.append(ag)
        
        self.labor_demand -= 1
        
        if(self.labor_demand == 0):
            
            self.flag_vacancies = 0
        
        
      
    def pay_wages(self):
        self.total_wage_payment = self.wage_offer * self.production_planned * self.labor_tech_coeff
        n = len(self.employees_list)
        if n <= 0 or self.total_wage_payment <= 0:
            self.total_wage_payment = 0.0
            return
        wage4worker = self.total_wage_payment / n
        for wk in self.employees_list:
            wk.receive_wage(wage4worker)
        if self.total_wage_payment > 0:           # AGGIUNTO DOPO -------
            self.my_firm.update_cash_for_KAU(self.id, -self.total_wage_payment)
        # self.my_firm.update_cash_for_KAU(self.id, - self.total_wage_payment)
        # print('wage payment', wage4worker)  # tieni o rimuovi se è rumore

        #ATTENZIONE: NECESSARIO METTERE UN CONTROLLO SU STOCK MONETA        
      
##############################
# PRODUCTION METHODS
##############################
        
    def produce(self):
                        
        # il calcolo di prod max non è necessario perchè l'ho già calcolato col piano produttivo
        if(self.labor_tech_coeff >0):
            self.production = min(self.production_planned, (1+ self.max_straordinari)*len(self.employees_list)/self.labor_tech_coeff)
        else:
            self.production = self.production_planned
        
        self.sold_quantity = 0
        self.revenues = 0
        self.total_costs = 0


        self.total_costs += self.total_wage_payment
        
        for k in self.commodities_stock.keys():
            
            self.commodities_stock[k] -= self.production*self.tech_coeff[k]
            if(k != self.my_commodity):
                self.total_costs += self.prices[k]*self.production*self.tech_coeff[k]
                self.commodities_stock_value[k] -= self.prices[k]*self.production*self.tech_coeff[k]
                
        self.commodities_stock[self.my_commodity] += self.production    
        # # if(self.capital_coeff[self.my_commodity]>0):
        # #     delta_capital_stock = self.target_speed*(self.target_capital[self.my_commodity] - self.capital_stocks[self.my_commodity])   
        # #     self.commodities_stock[self.my_commodity] += (self.production - delta_capital_stock)
        # #     self.capital_stocks[self.my_commodity] += max(0, delta_capital_stock)
        
        self.self_invest_own_capital()
        # self.set_supply()
        # Aggiungo tutta la produzione allo stock IO della mia commodity
        # self.commodities_stock[self.my_commodity] += self.production    

        # # --- NUOVO: auto-investimento sulla propria commodity ---
        # need_cap = getattr(self, "delta_capital_stock_own", 0.0)
        # if need_cap > 0.0 and self.capital_coeff.get(self.my_commodity, 0.0) > 0.0:
        #     # quanto posso effettivamente spostare? non più di quello che ho in scorta IO
        #     avail = max(0.0, self.commodities_stock.get(self.my_commodity, 0.0))
        #     take  = min(need_cap, avail)
        #     if take > 0.0:
        #         # sposta dallo stock IO allo stock di capitale
        #         self.commodities_stock[self.my_commodity] -= take
        #         # metto nel buffer
        #         self.own_capital_buffer[self.my_commodity] = \
        #             self.own_capital_buffer.get(self.my_commodity, 0.0) + take
        #         # self.capital_stocks[self.my_commodity] = \
        #         #     self.capital_stocks.get(self.my_commodity, 0.0) + take
        #         # lo segniamo anche come "capital_purchase" per coerenza con le metriche
        #         self.capital_purchase[self.my_commodity] = \
        #             self.capital_purchase.get(self.my_commodity, 0.0) + take

        # ora calcolo la supply tenendo conto che una parte dell'output è stata "messa da parte" come capitale
        self.set_supply()

        
        
        for k in self.inputs_consumption.keys():
            self.inputs_consumption[k] = 0
            self.total_expenditure[k] = 0

    def self_invest_own_capital(self):
        """Trasferisce output proprio verso capitale, fino al fabbisogno pianificato
        (deprezzamento + eventuale gap per sostenere la domanda attesa a u*)."""
        comm = self.my_commodity
        need = float(self.capital_demanded_quantity.get(comm, 0.0))
        if need <= 0.0:
            return

        # stesso buffer logico usato nel modello per non intaccare scorte IO minime
        denom = max(1e-12, 1.0 - self.tech_coeff.get(comm, 0.0))
        buffer = self.independence_periods * self.tech_coeff.get(comm, 0.0) * self.expected_demand / denom
        avail = max(0.0, self.commodities_stock.get(comm, 0.0) - buffer)

        take = min(need, avail)
        if take <= 0.0:
            return

        # giro interno: niente cassa/IVA
        self.commodities_stock[comm] = self.commodities_stock.get(comm, 0.0) - take
        self.own_capital_buffer[self.my_commodity] = self.own_capital_buffer.get(self.my_commodity, 0.0) + take
        # self.capital_stocks[comm]    = self.capital_stocks.get(comm, 0.0) + take
        self.capital_purchase[comm]  = self.capital_purchase.get(comm, 0.0) + take

        # segna come soddisfatta (in tutto o in parte) la domanda di capitale "proprio"
        self.capital_demanded_quantity[comm] = max(0.0, need - take)
        
    # def set_supply(self):
    #     denom = (1 - self.tech_coeff.get(self.my_commodity, 0.0))
    #     if denom <= 0:
    #         self.supply = max(0.0, self.commodities_stock.get(self.my_commodity, 0.0))
    #         return
    #     buffer = (self.independence_periods *
    #               self.tech_coeff[self.my_commodity] *
    #               self.expected_demand / denom)   # <-- stesso buffer del PDF
    #     stock = self.commodities_stock.get(self.my_commodity, 0.0)
    #     self.supply = max(0.0, stock - buffer)
      
    def set_supply(self):
        
        if(self.commodities_stock[self.my_commodity] > self.tech_coeff[self.my_commodity]*self.expected_demand/(1-self.tech_coeff[self.my_commodity])):
            self.supply = self.commodities_stock[self.my_commodity] - self.tech_coeff[self.my_commodity]*self.expected_demand/(1-self.tech_coeff[self.my_commodity])
        else:
            self.supply = self.commodities_stock[self.my_commodity] - 0.5*self.tech_coeff[self.my_commodity]*self.expected_demand/(1-self.tech_coeff[self.my_commodity])
        
        if(self.supply < 0):
            self.supply = 0
     
    
    def commit_own_capital(self):
        """Trasferisce il capitale nel buffer allo stock di capitale, da chiamare dopo il deprezzamento."""
        comm = self.my_commodity
        qty = self.own_capital_buffer.get(comm, 0.0)
        if qty <= 0.0:
            return
        self.capital_stocks[comm] = self.capital_stocks.get(comm, 0.0) + qty
        self.own_capital_buffer[comm] = 0.0

    # def set_supply(self):
    #     denom = (1 - self.tech_coeff.get(self.my_commodity, 0.0))
    #     if denom <= 0:
    #         # fallback prudente
    #         self.supply = max(0.0, self.commodities_stock.get(self.my_commodity, 0.0))
    #         return

    #     thresh = self.tech_coeff[self.my_commodity] * self.expected_demand / denom
    #     stock = self.commodities_stock.get(self.my_commodity, 0.0)
    #     if stock > thresh:
    #         self.supply = stock - thresh
    #     else:
    #         self.supply = stock - 0.5 * thresh
    #     if self.supply < 0:
    #         self.supply = 0.0





##############################
# PRICE SETTING METHODS #
##############################
       
    def set_price(self):
        
        pass
        
        
##############


##############################
# INTERMEDIATE GOODS DEMAND METHODS
##############################
    def adjust_demanded_quantity(self):
        total_planned_expenditure = 0.0
        for comm in self.total_demanded_quantity.keys():
            total_planned_expenditure += self.prices[comm] * self.total_demanded_quantity[comm]

        # Evita fattori negativi: la cassa disponibile non scende sotto zero
        avail = max(0.0, self.my_firm.cash_for_KAU.get(self.id, 0.0))

        if total_planned_expenditure > 0.0 and total_planned_expenditure > avail:
            factor = avail / total_planned_expenditure  # ∈ [0,1)
            for comm in self.total_demanded_quantity.keys():
                self.total_demanded_quantity[comm] *= factor

    # def adjust_demanded_quantity(self):
        
    #     total_planned_expenditure = 0
        
    #     for comm in self.total_demanded_quantity.keys():
            
    #         total_planned_expenditure += self.prices[comm]*self.total_demanded_quantity[comm]
             
    #     if(total_planned_expenditure> self.my_firm.cash_for_KAU[self.id]):
            
    #         factor = self.my_firm.cash_for_KAU[self.id]/total_planned_expenditure
            
    #         for comm in self.total_demanded_quantity.keys():
                
    #             self.total_demanded_quantity[comm] *= factor


##############################
# GOODS MARKET METHODS
##############################
        
    def sell(self, demand):
        
        sold_quantity = 0
        if(demand>0):
            sold_quantity = min(self.supply, demand)
        
        self.supply -= sold_quantity
        self.commodities_stock[self.my_commodity] -= sold_quantity

        self.previous_demand += demand
        
        self.sold_quantity += sold_quantity
        self.revenues += self.price*sold_quantity

        self.my_firm.update_cash_for_KAU(self.id, self.price*sold_quantity)
        
        return sold_quantity


    def reset_market_vars(self):
        
        self.attempt_number = 0
        self.rationing_level = 0                  
    
    ## SELLERS LIST EVOLUTION
    
    def update_sellers_list(self, commodity):
        # se la KAU non compra questa commodity → esci
        if commodity not in self.sellers_list:
            return

        L = self.sellers_list[commodity]
        n_removed_max = round(len(L) * self.memory_loss)

        if n_removed_max > 0 and L:
            # rimuovi fino a n_removed_max dalla coda, senza andare sotto zero
            to_remove = min(n_removed_max, len(L))
            for _ in range(to_remove):
                L.pop()

            # aggiungi nuovi seller pertinenti (stessa commodity)
            cands = self.model.localKAU_agents.select(self.model.localKAU_agents.my_commodity == commodity)
            n_added = 0
            # prova ad aggiungerne fino a to_remove senza duplicati
            for new_s in cands.random(len(cands)) if len(cands) > 0 else []:
                if new_s not in L:
                    L.append(new_s)
                    n_added += 1
                    if n_added == to_remove:
                        break

        # ordina per prezzo effettivo (usa get_price se esiste)
        # sostituisci il sort esistente
        def _eff_price(s, comm):
            # 1) prova get_price(comm)
            if hasattr(s, "get_price"):
                try:
                    p = s.get_price(comm)
                    if p and p > 0: 
                        return p
                except TypeError:
                    try:
                        p = s.get_price()
                        if p and p > 0:
                            return p
                    except TypeError:
                        pass
            # 2) fallback: mappa prezzi per commodity o attributo 'price'
            return getattr(s, "prices", {}).get(comm, getattr(s, "price", float("inf")))

        L.sort(key=lambda s: _eff_price(s, commodity))

    # def _weighted_split(self, commodity, sellers, total_budget):
    #     # Proporziona il budget ai pesi self.sellers_weights[commodity]
    #     try:
    #         wmap = getattr(self, 'sellers_weights', {}).get(commodity, {})
    #         weights = [max(0.0, float(wmap.get(s.id, 0.0))) for s in sellers]
    #         ssum = sum(weights)
    #         if ssum <= 0:
    #             # fallback: split uniforme
    #             return [total_budget / len(sellers)] * len(sellers)
    #         weights = [w/ssum for w in weights]
    #         return [total_budget * w for w in weights]
    #     except Exception:
    #         # fallback super-sicuro
    #         return [total_budget / len(sellers)] * len(sellers)

    # def buy(self, commodity):
    #     # Non compra il proprio output
    #     if commodity == self.my_commodity:
    #         return

    #     # Domanda residua per questa commodity
    #     # Preferiamo 'total_demanded_quantity' se presente, altrimenti 'demanded_quantity'
    #     need = self.total_demanded_quantity.get(commodity, None)
    #     if need is None:
    #         need = self.demanded_quantity.get(commodity, 0.0)
    #     if need <= 0.0:
    #         return

    #     sellers = self.sellers_list.get(commodity, [])
    #     if not sellers:
    #         return

    #     # Pesi: se definiti, li usiamo; altrimenti uniforme
    #     w_map = getattr(self, 'sellers_weights', {}).get(commodity, {})
    #     weights = []
    #     for s in sellers:
    #         w = float(w_map.get(s.id, 0.0))
    #         weights.append(max(0.0, w))
    #     wsum = sum(weights)
    #     if wsum <= 0.0:
    #         weights = [1.0 / len(sellers)] * len(sellers)
    #     else:
    #         weights = [w / wsum for w in weights]

    #     # Opportunismo: piccolo shuffle dell’ordine dei seller
    #     if np.random.random() < self.opportunism_degree:
    #         perm = np.random.permutation(len(weights))
    #         sellers = [sellers[i] for i in perm]
    #         weights = [weights[i] for i in perm]

    #     # Ripartizione pesata della domanda: per ogni seller assegno una quota,
    #     # imposto 'demanded_quantity[commodity] = quota' e compro.
    #     remaining = need
    #     for idx, s in enumerate(sellers):
    #         if remaining <= 0.0:
    #             break

    #         quota = need * weights[idx]
    #         if idx == len(sellers) - 1:  # ultimo prende tutto il residuo
    #             quota = remaining
    #         if quota <= 0.0:
    #             continue

    #         # Salva lo stato precedente
    #         prev_q = self.demanded_quantity.get(commodity, 0.0)
    #         prev_tot = self.total_demanded_quantity.get(commodity, remaining)

    #         # Imposta domanda temporanea = quota
    #         self.demanded_quantity[commodity] = quota
            
    #         # Acquisto
    #         self.buy_from_seller(s, commodity, True)
            
    #         # Domanda rimasta dopo l'acquisto da 's'
    #         after_q = self.demanded_quantity.get(commodity, 0.0)
    #         served = max(0.0, quota - after_q)
            
    #         # Ripristina demanded_quantity come residuo (per coerenza con il resto del modello)
    #         remaining = max(0.0, remaining - served)
    #         self.demanded_quantity[commodity] = remaining
    #         self.total_demanded_quantity[commodity] = remaining
            
    #         # Aggiorna attempt_number come in origine
    #     self.attempt_number += 1

    # def buy(self, commodity):
    #     if commodity == self.my_commodity:
    #         return  # non compra il proprio output
    #     if commodity not in self.total_demanded_quantity or self.total_demanded_quantity.get(commodity, 0.0) <= 0.0:
    #         return  # niente domanda per questa commodity
    #     if commodity not in self.sellers_list:
    #         return  # nessun seller noto

    #     if self.attempt_number == 0:
    #         # fallback se non ho un my_seller
    #         if commodity not in self.my_seller or self.my_seller[commodity] is None:
    #             L = self.sellers_list.get(commodity, [])
    #             if not L:
    #                 return
    #             self.my_seller[commodity] = L[0]

    #         r = np.random.random()
    #         if r < self.opportunism_degree:
    #             self.change_my_seller(commodity)

    #         self.buy_from_seller(self.my_seller[commodity], commodity, True)

    #     elif self.attempt_number == 1:
    #         if self.rationing_level > self.rationing_threshold:
    #             self.change_my_seller(commodity)
    #             self.buy_from_seller(self.my_seller[commodity], commodity, True)
    #         else:
    #             self.buy_from_sellers_list(commodity)
    #     else:
    #         self.buy_from_sellers_list(commodity)

    #     self.attempt_number += 1

    def buy(self, commodity):
        # non compra il proprio output
        if commodity == self.my_commodity:
            return
        # domanda residua pianificata (intermedi+capitale)
        need = float(self.total_demanded_quantity.get(commodity, 0.0))
        if need <= 0.0:
            return
        # evitiamo doppi acquisti nello stesso periodo
        if self.attempt_number != 0:
            return

        # seller domestico (primo non-RoW) e RoW
        dom = None
        for s in self.sellers_list.get(commodity, []):
            if not getattr(s, 'is_RoW', False):
                dom = s
                break
        row = self.model.RoW[0] if len(self.model.RoW) > 0 else None

        # quota domestica per QUANTITÀ
        qD_cfg = getattr(self, 'qD_intermediate', 1.0)
        if isinstance(qD_cfg, dict):
            qD = float(qD_cfg.get(commodity, 1.0))
        else:
            qD = float(qD_cfg)
        qD = min(1.0, max(0.0, qD))
        qR = 1.0 - qD

        bought_dom = 0.0

        # 1) DOMESTICO su quantità target (limitato da cassa)
        if dom is not None and qD > 0.0:
            ask_dom_Q = qD * need
            # imposto temporaneamente la domanda a ask_dom_Q
            prev_need = self.total_demanded_quantity.get(commodity, 0.0)
            self.total_demanded_quantity[commodity] = ask_dom_Q
            self.buy_from_seller(dom, commodity, False)  # rispetta supply e cassa
            after = self.total_demanded_quantity.get(commodity, 0.0)
            served_dom = max(0.0, ask_dom_Q - after)
            bought_dom = served_dom
            # ripristino il residuo pieno (servirà per la quota RoW)
            self.total_demanded_quantity[commodity] = max(0.0, need - served_dom)

        # 2) RoW: quota estera + shortfall domestico
        shortfall_dom = max(0.0, qD * need - bought_dom)
        if row is not None and (qR > 0.0 or shortfall_dom > 0.0):
            ask_row_Q = qR * need + shortfall_dom
            prev_need = self.total_demanded_quantity.get(commodity, 0.0)
            self.total_demanded_quantity[commodity] = ask_row_Q
            # il RoW accetta la firma sell(commodity, q)
            try:
                self.buy_from_seller(row, commodity, False)
            except TypeError:
                # in caso la firma non accetti la commodity
                q_b = row.sell(ask_row_Q)
                # emula la parte di buy_from_seller (aggiornamenti minimi)
                price = getattr(row, "prices", {}).get(commodity, getattr(row, "price", 0.0))
                expenditure = q_b * float(price)
                self.total_demanded_quantity[commodity] = max(0.0, ask_row_Q - q_b)
                if hasattr(self.my_firm, "update_cash_for_KAU"):
                    self.my_firm.update_cash_for_KAU(self.id, -expenditure)

            after = self.total_demanded_quantity.get(commodity, 0.0)
            served_row = max(0.0, ask_row_Q - after)
            # chiudo con il residuo "vero"
            self.total_demanded_quantity[commodity] = max(0.0, need - bought_dom - served_row)

        self.attempt_number += 1

            
    def change_my_seller(self, commodity):
        L = self.sellers_list.get(commodity, [])
        if not L:
            return
        new_seller = L[0]
        cur = self.my_seller.get(commodity)
        if len(L) > 1 and cur is not None and new_seller.id == cur.id:
            self.my_seller[commodity] = L[1]
        else:
            if cur is not None:
                try:
                    L.remove(new_seller)
                except ValueError:
                    pass
                L.append(cur)
            self.my_seller[commodity] = new_seller

    def buy_from_sellers_list(self, commodity):
        for seller in self.sellers_list.get(commodity, []):
            if getattr(seller, "supply", 0) > 0:
                self.buy_from_seller(seller, commodity, False)
                break
               
                    
    
    def buy_from_seller(self, seller, commodity, is_my_seller):
        # 1) prezzo robusto
        price = 0.0
        if hasattr(seller, "get_price"):
            try:
                price = seller.get_price(commodity)
            except TypeError:
                try:
                    price = seller.get_price()
                except TypeError:
                    price = 0.0
        if price <= 0:
            price = getattr(seller, "prices", {}).get(commodity, getattr(seller, "price", 0.0))
        if price <= 0:
            return

        # 2) vincoli di cassa e domanda residua
        cash = self.my_firm.cash_for_KAU.get(self.id, 0.0) if hasattr(self.my_firm, "cash_for_KAU") else 0.0
        demand_left = self.total_demanded_quantity.get(commodity, 0.0)
        if demand_left <= 0 or cash <= 0:
            return

        demanded_quantity = min(cash / price, demand_left)
        if demanded_quantity <= 0:
            return

        # 3) vendita robusta (prova sell(commodity, q) poi sell(q))
        try:
            bought_quantity = seller.sell(commodity, demanded_quantity)
        except TypeError:
            bought_quantity = seller.sell(demanded_quantity)

        if is_my_seller and demanded_quantity > 0:
            self.rationing_level = 1 - bought_quantity / demanded_quantity

        cap_q = self.capital_quote.get(commodity, 0.0)
        cap_q = min(max(cap_q, 0.0), 1.0)
        capital_bought_quantity = cap_q * bought_quantity
        inputs_bought_quantity = bought_quantity - capital_bought_quantity
        
        self.commodities_stock[commodity] = self.commodities_stock.get(commodity, 0.0) + inputs_bought_quantity
        self.inputs_consumption[commodity] = self.inputs_consumption.get(commodity, 0.0) + inputs_bought_quantity

        self.capital_stocks[commodity] = self.capital_stocks.get(commodity, 0.0) + capital_bought_quantity
        self.capital_purchase[commodity] = self.capital_purchase.get(commodity, 0.0) + capital_bought_quantity

        # 📌 NUOVO: traccia investimenti in capitale da altre KAU (esclude RoW e auto-investimento)
        if capital_bought_quantity > 0.0 and not getattr(seller, 'is_RoW', False):
            sid = getattr(seller, 'id', None)
            if sid is not None:
                self.capital_purchase_by_KAU[sid] = \
                    self.capital_purchase_by_KAU.get(sid, 0.0) + capital_bought_quantity

        self.total_demanded_quantity[commodity] = max(0.0, demand_left - bought_quantity)
        expenditure = bought_quantity * price
        if getattr(seller, 'is_RoW', False):
            self.spent_to_RoW_step += expenditure
            self.spent_to_RoW_by_comm_step[commodity] = \
                self.spent_to_RoW_by_comm_step.get(commodity, 0.0) + expenditure
        
        self.total_expenditure[commodity] = self.total_expenditure.get(commodity, 0.0) + expenditure

        if hasattr(self.my_firm, "update_cash_for_KAU"):
            self.my_firm.update_cash_for_KAU(self.id, -expenditure)


        
        


##############################
# UPDATE PRICES 
##############################
            
    def update_prices(self):
        pass
        # for commodity in self.commodities_stock.keys():
            
        #     if(self.inputs_consumption[commodity]>0):
                
        #         self.prices[commodity] = self.total_expenditure[commodity]/self.inputs_consumption[commodity]
        #         #print(self.prices[commodity])
            

##############################
# EARNINGS COMPUTATION
##############################
        
    def compute_earnings(self):
        self.my_commodity_stock_value_old = self.commodities_stock_value[self.my_commodity]
        self.update_my_stock()

        delta_stock = self.commodities_stock_value[self.my_commodity] - self.my_commodity_stock_value_old

        # --- (2) Delta capitale sul proprio bene capitale (incluso quello auto-prodotto) ---
        # Valore di capitale "proprio" al passo precedente
        # K_old_val = self.capital_stocks_value.get(
        #     self.my_commodity,
        #     self.capital_stocks.get(self.my_commodity, 0.0) * self.price
        # )

        # Valore di capitale "proprio" alla fine dello step (dopo deprezzamento + commit_own_capital)
        # K_new_qty = self.capital_stocks.get(self.my_commodity, 0.0)
        # K_new_val = K_new_qty * self.price
        # self.capital_stocks_value[self.my_commodity] = K_new_val

        # delta_K_own = K_new_val - K_old_val        
    
        # aliquote
        gov = self.model.Government[0] if hasattr(self.model, "Government") else None
        vat_dict = getattr(gov, "tax_rates", {}).get('VAT', {}) if gov else {}
        corp_rate = getattr(gov, "tax_rates", {}).get('corporate', 0.0) if gov else 0.0

        vat_rate = vat_dict.get(self.my_commodity, 0.0)
        self.VAT = vat_rate / (1 + vat_rate) * self.revenues if vat_rate > 0 else 0.0
        
        dep = getattr(self, 'depreciation_expense', 0.0)
        
        self.earnings = max(0.0, self.revenues - self.total_costs + delta_stock - dep)
        self.net_earnings = max(0.0, self.revenues - self.VAT - self.total_costs + delta_stock - dep)
        
        self.income_tax = self.net_earnings * corp_rate


##############################
# REVALUATIONS METHODS
##############################


    def update_my_stock(self):
        
        pass
       
    
    def revaluate_inputs_stocks(self):
                
        for k in self.commodities_stock.keys():
            
            if(k!=self.my_commodity):
                self.commodities_stock_value[k] = self.prices[k]*self.commodities_stock[k]


    def depreciate_capital(self):
        self.depreciation_expense = 0.0
        
        for comm in self.capital_stocks.keys():
            # azzero il costo di deprezzamento del periodo
            #self.depreciation_expense = 0.0

            K_old = self.capital_stocks[comm]
            rate = self.capital_depreciation.get(comm, 0.0)

            if rate > 0.0 and K_old > 0.0:
                # quantità che si consuma in questo step
                dep_qty = K_old * rate
                
                # prezzo del bene capitale (se manca, fallback al prezzo della KAU)
                p_cap = self.prices.get(comm, self.price)
            
                # valore del deprezzamento di questa commodity
                dep_val = dep_qty * p_cap
                if comm != self.my_commodity:
                    self.depreciation_expense += dep_val
                # accumulo sul costo di periodo
                # self.depreciation_expense += dep_val
                
            self.capital_stocks[comm] *= (1-self.capital_depreciation[comm])
##############################
#  ACCESSORY METHODS
##############################

    def get_price(self, commodity=None):
        # se mi chiedono una commodity diversa dal mio output,
        # prova a restituire il prezzo da self.prices
        if commodity is not None and commodity != self.my_commodity:
            return self.prices.get(commodity, self.price)
        return self.price

    


class LocalKAU_price(LocalKAU):
    
    def setup(self):
        
        LocalKAU.setup(self)
        
        
    def compute_unit_cost(self):
        
        self.unit_cost = 0
        for k in self.commodities_stock.keys():
            self.unit_cost += self.prices[k]*self.tech_coeff[k]
            
        self.unit_cost += self.wage_offer*self.labor_tech_coeff
         
        
    def update_my_stock(self):
        
        self.commodities_stock_value[self.my_commodity] = self.commodities_stock[self.my_commodity]*self.price
        #print(self.commodities_stock_value[self.my_commodity], self.commodities_stock[self.my_commodity])
        
    def pay_taxes(self):
        
        expenditure = self.VAT + self.income_tax
        
        self.my_firm.update_cash_for_KAU(self.id, -expenditure)        
        
        self.model.Government[0].receive_taxes(expenditure)
        

## DEFINIZIONE DELLA CLASSE SpecialKAU
class SpecialKAU(LocalKAU_price):
    
    # KAU speciali che aggiungono gli investimenti PNIEC come domanda extra di beni capitali alle 9 KAU fornitrici
    # Inherit da LocalKAU_price per riusare:
    # - piani standard (stock, produzione, input, capitale endogeno, lavoro)
    # - mercato dei beni (buy/sell), split acquisti in input e capitale
    # - contabilità (costi, ricavi, IVA)  e agggiornamento prezzi input
        
    def setup(self):
        # inizializzo tutto come una KAU price-based
        super().setup()
        
        # PARAMETRI SPECIFICI (li popoliamo in initialize_LocalKAUs)
        # BOM --> quante unità fisiche del bene capitale k servono per installare 1 MW di potenza
        # Esempio: {'P1': u1, ..., 'P9': u9}
        self.bom_units_per_MW = {}
        
        # Profilo temporale --> MW da installare ad ogni periodo (lista lunga quanto gli step della simulazione)
        self.power_schedule_MW = []
        
        # Metriche
        self._MW_target_cum = 0.0
        self._installed_MW_this_period = 0.0
        self._installed_MW_cum = 0.0
        
        # capital_quote viene gestito come un dizionario in buy_from_seller
        self.capital_quote = {}
        self._extra_capital_demand_t = 0.0
        self.capital_purchase_flow = 0.0
        self.capital_purchase_cum = 0.0
        
    # override leggero del metodo che effettua le pianificazioni
    def make_plans(self):
        # 1) Piani standard della KAU
        # 2) Iniezione della domanda extra di capitale (BOM x MW da installare)
        # 3) Ricalcolo di total_demanded_quantities  capital_quote per commodity
        super().make_plans()
        shock_start = getattr(self.model.p, 'shock_start', None)
        shock_end   = getattr(self.model.p, 'shock_end', None)
        t = getattr(self.model, 't', 0)

        active = (
            shock_start is not None and
            shock_end   is not None and
            shock_start <= t <= shock_end
        )

        if not active:
            # fuori shock: SpecialKAU è dinamicamente identica a LocalKAU_price
            self._extra_capital_demand_t = 0.0
            return
        
        self.inject_extra_capital_demand()
        self.plan_total_demanded_quantities()
        

    def inject_extra_capital_demand(self):
        # finestra di shock
        shock_start = getattr(self.model.p, 'shock_start', None)
        shock_end   = getattr(self.model.p, 'shock_end', None)

        t = getattr(self.model, 't', 1)
        if t < shock_start or t > shock_end:
            # fuori dalla finestra: nessuna domanda extra
            self._extra_capital_demand_t = 0.0
            return

        if not self.power_schedule_MW:
            self._extra_capital_demand_t = 0.0
            return

        idx = t - shock_start
        if idx < 0 or idx >= len(self.power_schedule_MW):
            self._extra_capital_demand_t = 0.0
            return

        MW_t = self.power_schedule_MW[idx]
        self._MW_target_cum += MW_t

        total_extra = 0.0
        for comm, units_per_MW in self.bom_units_per_MW.items():
            extra = units_per_MW * MW_t
            if extra <= 0.0:
                continue
            self.capital_demanded_quantity[comm] = \
                self.capital_demanded_quantity.get(comm, 0.0) + extra
            total_extra += extra

        self._extra_capital_demand_t = total_extra

    # aggiunta al metodo update_prices del calcolo delle metriche sui MW installati nel periodo
    def update_prices(self):
        # 1) logica base (al momento è pass, ma la lascio per futura compatibilità)
        super().update_prices()

        # 2) MW equivalenti installati nel periodo
        ratios = []
        for comm, units_per_MW in self.bom_units_per_MW.items():
            if units_per_MW > 0:
                purchased_units = self.capital_purchase.get(comm, 0.0)
                ratios.append(purchased_units / units_per_MW)

        self._installed_MW_this_period = min(ratios) if ratios else 0.0
        self._installed_MW_cum += self._installed_MW_this_period

        # 3) flusso di acquisti di capitale nel periodo (tutti i beni capitali)
        self.capital_purchase_flow = sum(self.capital_purchase.values())
        self.capital_purchase_cum += self.capital_purchase_flow

        # 4) azzero i contatori di acquisti capitale del periodo
        for comm in list(self.capital_purchase.keys()):
            self.capital_purchase[comm] = 0.0

            
            