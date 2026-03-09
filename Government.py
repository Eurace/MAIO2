# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 12:17:03 2024

@author: marce
"""


import agentpy as ap


class Government(ap.Agent):
    
    def setup(self):
        
        #STOCKS
        self.liquidity = 0
        
        #FLOWS
        self.consumption_budget = 0
        self.unemployment_benefits = 0
        self.taxes = 0
        
        #PARAMS
        self.tax_rates = {}
        self.average_wage = 0
        self.ub_fraction = 0
        self.transfer_fraction = 0
        
        self.consumptions = {}
        self.consumption_budgets = {}
        self.consumption_shares = {}
        
        # breakdown per grafici
        self.consumptions_domestic = {}   # spesa verso KAU domestici
        self.consumptions_row = {}        # spesa verso RoW (import)
        self.spent_to_RoW_step = 0.0      # import del periodo (totale)
        self.spent_to_RoW_by_comm_step = {}  # import per commodity nel periodo

        self.consumptions = {}               # spesa totale per commodity (D+RoW) del SOLO step
        self.spent_domestic_step = 0.0       # spesa domestica del SOLO step
        self.spent_to_RoW_step = 0.0         # spesa verso RoW del SOLO step
        self.spent_to_RoW_by_comm_step = {}  # (opzionale, breakdown per commodity)

        self.transfers_paid_step = 0.0
        self.unemployment_paid_step = 0.0


    def make_period_account(self):
        
        self.liquidity += self.taxes
        
        self.taxes = 0
        


    def distribute_transfers(self):
        
        transfers = self.average_wage*self.transfer_fraction*len(self.model.Household_agents)
        
        transfers_h = self.average_wage*self.transfer_fraction
        
        n = len(self.model.Household_agents)
        
        if(self.liquidity < transfers):
            
            transfers_h = self.liquidity/n if n > 0 else 0

        paid = 0.0
        
        for h in self.model.Household_agents:
            
            h.receive_transfer(transfers_h)
            self.liquidity -= transfers_h
            paid += transfers_h
            
        self.transfers_paid_step = paid  # ← quanto ha davvero speso in trasferimenti nello step
        
        
    def distribute_unemployment_benefits(self):
        
        unemployed_list = self.model.Household_agents.select(self.model.Household_agents.flag_employed == 0)
        
        if(len(unemployed_list)>0):
            
            self.unemployment_benefits = len(unemployed_list)*self.average_wage*self.ub_fraction
    
            if(self.liquidity > self.unemployment_benefits):
                
                ub = self.average_wage*self.ub_fraction
            
            else:
                
                ub = max(0,self.liquidity/len(unemployed_list))
            
            paid = 0.0
            
            for h in unemployed_list:
                
                h.receive_unemployment_benefit(ub)
                self.liquidity -= ub
                paid += ub
                
            self.unemployment_paid_step = paid
            
        else:
              
            self.unemployment_benefits = 0
            self.unemployment_paid_step = 0.0    

    # def determine_consumption_budgets(self):
    #     # --- override steady-state, se attivo ---
    #     self.consumptions = {c: 0.0 for c in self.consumption_shares.keys()}
    #     sm = getattr(self.model, "params", {}).get("stationary_mode", {})
    #     if sm.get("active"):
    #         gb = sm.get("Gov_budgets")         # <<< usa la chiave corretta
    #         if isinstance(gb, dict) and gb:
    #             # budget totale e per-commodity fissati dal PDF
    #             self.consumption_budgets = {k: float(v) for k, v in gb.items()}
    #             self.consumption_budget = float(sum(self.consumption_budgets.values()))
    #             return  # esci: non usare la logica standard

    #     # --- logica standard (fallback) ---
    #     self.consumption_budget = max(0, self.liquidity)
    #     for comm in self.consumption_shares.keys():
    #         self.consumption_budgets[comm] = self.consumption_shares[comm] * self.consumption_budget

    def determine_consumption_budgets(self):
       
        self.consumption_budget = max(0, self.liquidity)
        
        self.consumptions = {comm: 0.0 for comm in self.consumption_shares.keys()}
        self.consumptions_domestic = {comm: 0.0 for comm in self.consumption_shares.keys()}  # <—
        self.consumptions_row = {comm: 0.0 for comm in self.consumption_shares.keys()}       # <—
        self.spent_domestic_step = 0.0
        self.spent_to_RoW_step = 0.0
        self.spent_to_RoW_by_comm_step = {}
        
        for comm in self.consumption_shares.keys():
            
            self.consumption_budgets[comm] = self.consumption_shares[comm]*self.consumption_budget
            
         
    def buy(self, commodity):
        # budget allocato a questa commodity
        budget = float(self.consumption_budgets.get(commodity, 0.0))
        if budget <= 0.0 or self.liquidity <= 0.0:
            return

        # quota domestica del Governo (può essere scalare o dict per commodity)
        pol = getattr(self.model.p, 'import_policy', {})
        qD_gov = pol.get('qD_gov', 1.0)
        if isinstance(qD_gov, dict):
            qD = float(qD_gov.get(commodity, 1.0))
        else:
            qD = float(qD_gov)
        qD = max(0.0, min(1.0, qD))
        qR = 1.0 - qD

        # target di spesa (in valore) per domestico e RoW
        dom_target = qD * budget
        row_target = qR * budget

        # --- helper per prezzo robusto
        def _price(s, comm=None):
            if s is None:
                return 0.0
            if hasattr(s, "get_price"):
                try:
                    return float(s.get_price(comm))
                except TypeError:
                    try:
                        return float(s.get_price())
                    except TypeError:
                        return 0.0
            return float(getattr(s, "prices", {}).get(comm, getattr(s, "price", 0.0)) or 0.0)

        # --- 1) DOMESTICO: compra dalle KAU locali della commodity
        sellers_iter = self.model.localKAU_agents.select(self.model.localKAU_agents.my_commodity == commodity)
        sellers_iter = sellers_iter.select(sellers_iter.supply > 0)
        sellers = list(sellers_iter)

        # ripartizione semplice: quote uguali tra i seller disponibili
        remaining_dom = min(dom_target, self.liquidity, self.consumption_budgets.get(commodity, 0.0))
        n = len(sellers)
        if n > 0 and remaining_dom > 0.0:
            for idx, s in enumerate(sellers):
                # quota di spesa su questo seller (l’ultimo prende tutto il residuo)
                if idx < n - 1:
                    share = remaining_dom / (n - idx)
                else:
                    share = remaining_dom

                p = _price(s, commodity)
                if p <= 0.0 or self.liquidity <= 0.0 or self.consumption_budgets.get(commodity, 0.0) <= 0.0:
                    break

                plan = min(share, self.liquidity, self.consumption_budgets[commodity])
                q_demand = plan / p if p > 0 else 0.0
                if q_demand <= 0.0:
                    continue

                # LocalKAU.sell(demand) → firma a un argomento
                try:
                    q_bought = s.sell(q_demand)
                except TypeError:
                    # fallback nel caso in cui il tuo sell accetti (commodity, q)
                    q_bought = s.sell(commodity, q_demand)
                spent = q_bought * p
                if spent <= 0.0:
                    continue

                # aggiorna contabilità
                self.consumptions[commodity] = self.consumptions.get(commodity, 0.0) + spent
                self.consumptions_domestic[commodity] = self.consumptions_domestic.get(commodity, 0.0) + spent
                self.spent_domestic_step += spent
                self.consumption_budgets[commodity] -= spent
                self.liquidity -= spent
                remaining_dom = max(0.0, remaining_dom - spent)

        # --- 2) RoW: quota estera + eventuale shortfall domestico
        shortfall = max(0.0, dom_target - (qD * budget - remaining_dom))
        plan_row = min(row_target + shortfall,
                       self.liquidity,
                       self.consumption_budgets.get(commodity, 0.0))

        row = self.model.RoW[0] if len(self.model.RoW) > 0 else None
        p_row = _price(row, commodity)
        if row is not None and p_row > 0.0 and plan_row > 0.0:
            q_row = plan_row / p_row
            # RoW.sell(commodity, q) → di solito firma a due argomenti
            try:
                q_bought_row = row.sell(commodity, q_row)
            except TypeError:
                q_bought_row = row.sell(q_row)
            spent_row = q_bought_row * p_row
            if spent_row > 0.0:
                self.consumptions[commodity] = self.consumptions.get(commodity, 0.0) + spent_row
                self.consumptions_row[commodity] = self.consumptions_row.get(commodity, 0.0) + spent_row
                self.spent_to_RoW_step += spent_row
                self.spent_to_RoW_by_comm_step[commodity] = \
                    self.spent_to_RoW_by_comm_step.get(commodity, 0.0) + spent_row
                self.consumption_budgets[commodity] -= spent_row
                self.liquidity -= spent_row
        
        
    # def buy(self, commodity):
    #     budget = self.consumption_budgets.get(commodity, 0.0)
    #     if budget <= 0 or self.liquidity <= 0:
    #         return

    #     # 1) filtra per commodity
    #     sellers_iter = self.model.localKAU_agents.select(
    #         self.model.localKAU_agents.my_commodity == commodity
    #     )
    #     # 2) poi filtra per supply > 0
    #     sellers_iter = sellers_iter.select(sellers_iter.supply > 0)

    #     sellers_list = list(sellers_iter)

    #     sellers_list = list(sellers_iter)
    #     n_sellers = len(sellers_list)
    #     if n_sellers == 0:
    #         return

    #     # quota uguale per seller; aggiorniamo budget residuo ogni volta
    #     share = budget / n_sellers
    #     for s in sellers_list:
    #         # prezzo robusto
    #         price = s.get_price() if hasattr(s, "get_price") else getattr(s, "price", 0.0)
    #         if price <= 0:
    #             continue

    #         # se il budget residuo è finito, stop
    #         if self.consumption_budgets.get(commodity, 0.0) <= 0 or self.liquidity <= 0:
    #             break

    #         demand_share = min(share, self.consumption_budgets[commodity], self.liquidity)
    #         demanded_quantity = demand_share / price if price > 0 else 0.0
    #         if demanded_quantity <= 0:
    #             continue

    #         bought_quantity = s.sell(demanded_quantity)
    #         expenditure = bought_quantity * price
            
    #         self.consumptions[commodity] = self.consumptions.get(commodity, 0.0) + expenditure
    #         # scala budget e liquidità in base all’effettivo comprato
    #         self.consumption_budgets[commodity] -= expenditure
    #         self.liquidity -= expenditure
           

                    
    def reset_market_vars(self):
        
        pass
    
    def update_sellers_list(self, commodity):
        
        pass
       

    def receive_taxes(self, amount):
        
        self.taxes += amount
        
        

        
        

        
    

        
        
        
    
    
    