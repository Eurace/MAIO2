# -*- coding: utf-8 -*-
"""
Created on Tue May  2 19:29:49 2023

@author: marce
"""
import random as random
import agentpy as ap
import numpy as np

class Household(ap.Agent):
    
    def setup(self):
        # STOCKS
        self.wealth = 0
        self.property_shares = {}
        
        # FLOWS
        self.income = 0
        self.wage = 0
        self.dividends = 0
        self.consumption = 0
        self.labor_tax = 0
        self.dividend_tax = 0
        
        # PARAMETERS AND OTHER VARIABLES
        self.consumption_budget = 0
        self.wealth2income_target = 0 
        self.csi = 0
        self.consumption_budgets = {}
        self.consumption_shares = {}
        self.consumptions_qt = {}
        
        self.my_seller = {}
        self.attempt_number = 0
        self.rationing_level = 0
        self.rationing_threshold = 0
        self.sellers_list = {}
        self.field_of_view = 0
        self.memory_loss = 0
        self.opportunism_degree = 0
        
        self.employer_id = -1
        self.flag_employed = 0
        self.gov_transfer = 0
        self.spent_to_RoW_step = 0.0
        self.spent_to_RoW_by_comm_step = {}

        self.my_bank = None
        
    # def determine_consumption_budgets(self):
    #     # --- override steady-state, se attivo ---
    #     sm = getattr(self.model, "params", {}).get("stationary_mode", None)
    #     if sm and sm.get("active", False):
    #         # b è il dizionario {commodity: budget} per questa household
    #         b = sm['HH_budgets'][self.id] if self.id < len(sm['HH_budgets']) else None
    #         if b is not None:
    #             # azzero contatori/flussi come nel tuo metodo
    #             self.consumption = 0
    #             self.dividends = 0
    #             self.wage = 0
    #             self.gov_transfer = 0

    #             # budget totale fissato dal PDF
    #             self.consumption_budget = sum(b.values())

    #             # budget per commodity
    #             for k in self.consumption_shares.keys():
    #                 self.consumptions_qt[k] = 0
    #                 self.consumption_budgets[k] = float(b.get(k, 0.0))
    #             self.income = float(self.consumption_budget)
    #             self.disposable_income = self.income
    #             self.wage = self.income
    #             return
    #     # --- fine override SS ---

    #     # tua logica originale (dinamica endogena)
    #     self.determine_disposable_income()
    #     self.consumption = 0
    #     self.dividends = 0
    #     self.wage = 0
    #     self.gov_transfer = 0
    #     self.consumption_budget = (
    #         self.disposable_income
    #         + self.csi * (self.wealth - self.disposable_income - self.wealth2income_target * self.disposable_income)
    #     )
    #     if self.consumption_budget < 0:
    #         self.consumption_budget = 0

    #     for k in self.consumption_shares.keys():
    #         self.consumptions_qt[k] = 0
    #         self.consumption_budgets[k] = self.consumption_budget * self.consumption_shares[k]
     
    def determine_consumption_budgets(self):
        
        self.determine_disposable_income()
        
        self.consumption = 0
        #self.income = self.dividends + self.wage
        self.dividends = 0
        self.wage = 0
        self.gov_transfer = 0
        self.consumption_budget = self.disposable_income + self.csi*(self.wealth - self.income - self.wealth2income_target*self.disposable_income)
        if(self.consumption_budget<0):
            self.consumption_budget = 0
        
        for k in self.consumption_shares.keys():
            
            self.consumptions_qt[k] = 0
            self.consumption_budgets[k] = self.consumption_budget*self.consumption_shares[k]

    
    def update_sellers_list(self, commodity):
        if commodity not in self.sellers_list:
            self.sellers_list[commodity] = []
        L = self.sellers_list[commodity]
        n_removed_max = round(len(L) * self.memory_loss)
        if n_removed_max > 0:
            for _ in range(n_removed_max):
                if L: L.pop()
            n_added = 0
            for new_s in self.model.localKAU_agents.random(len(self.model.localKAU_agents)):
                if new_s not in L:
                    L.append(new_s); n_added += 1
                    if n_added == n_removed_max: break
        # Ordina su prezzo effettivo

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


        
    def change_my_seller(self, commodity):
        L = self.sellers_list.get(commodity, [])
        if not L: return
        new_seller = L[0]
        if len(L) > 1 and self.my_seller.get(commodity) and (new_seller.id == self.my_seller[commodity].id):
            self.my_seller[commodity] = L[1]
        else:
            if self.my_seller.get(commodity) is not None:
                try: L.remove(new_seller)
                except ValueError: pass
                L.append(self.my_seller[commodity])
            self.my_seller[commodity] = new_seller      


    def reset_market_vars(self):
        
        self.attempt_number = 0
        self.rationing_level = 0

    # def buy(self, commodity):
    #     # budget residuo per questa commodity
    #     B = self.consumption_budgets.get(commodity, 0.0)
    #     if B <= 0.0:
    #         return

    #     sellers = self.sellers_list.get(commodity, [])
    #     if not sellers:
    #         return

    #     # pesi da sellers_weights (se non ci sono → uniforme)
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

    #     # un po' di "opportunismo": randomizza l'ordine di visita
    #     if np.random.random() < self.opportunism_degree:
    #         perm = np.random.permutation(len(sellers))
    #         sellers = [sellers[i] for i in perm]
    #         weights = [weights[i] for i in perm]

    #     # ripartisci il budget B in base ai pesi
    #     leftover_pool = 0.0
    #     base_B = B

    #     for idx, s in enumerate(sellers):
    #         # quota assegnata; l'ultimo prende tutto quello che resta
    #         if idx < len(sellers) - 1:
    #             alloc = base_B * weights[idx]
    #         else:
    #             alloc = base_B - leftover_pool

    #         if alloc <= 0.0:
    #             continue

    #         # usa alloc come budget temporaneo per questo seller
    #         prev = self.consumption_budgets.get(commodity, 0.0)
    #         self.consumption_budgets[commodity] = alloc

    #         self.buy_from_seller(s, commodity, True)

    #         after = self.consumption_budgets.get(commodity, 0.0)
    #         spent = max(0.0, alloc - after)
    #         leftover_pool += max(0.0, alloc - spent)

    #     # rimetti in consumo_budgets l'eventuale residuo non speso
    #     self.consumption_budgets[commodity] = max(0.0, leftover_pool)

    #     # mantengo la semantica originale
    #     self.attempt_number += 1



    # def buy(self, commodity):
        
            
        
    #     if(self.attempt_number == 0):
            
    #         # Fallback sicuro se non ho un my_seller
    #         if commodity not in self.my_seller or self.my_seller[commodity] is None:
    #             L = self.sellers_list.get(commodity, [])
    #             if L:
    #                 self.my_seller[commodity] = L[0]
    #             else:
    #                 return  # nessun seller disponibile: esco silenziosamente
            
    #         r = np.random.random()
            
    #         if(r< self.opportunism_degree):
                
    #             self.change_my_seller(commodity)
                        
    #         self.buy_from_seller(self.my_seller[commodity], commodity, True)

        
    #     elif(self.attempt_number == 1):
                                                
    #         if(self.rationing_level > self.rationing_threshold):
    #             print(self.id, 'I am rationed')
    #             self.change_my_seller(commodity)
                
    #             self.buy_from_seller(self.my_seller[commodity], commodity, True)
                
    #         else:                    
                
    #             self.buy_from_sellers_list(commodity)
                
    #     else:
             
    #           self.buy_from_sellers_list(commodity)
             
    #     self.attempt_number +=1
                 
    def buy(self, commodity):
        # Un solo acquisto per periodo/commodity come nel modello base
        if self.attempt_number != 0:
            return

        # Budget residuo per questa commodity
        B = float(self.consumption_budgets.get(commodity, 0.0))
        if B <= 0.0:
            self.attempt_number += 1
            return

        # Trova un seller domestico (primo in lista che NON è RoW)
        dom = None
        for s in self.sellers_list.get(commodity, []):
            if not getattr(s, 'is_RoW', False):
                dom = s
                break
        # RoW seller
        row = self.model.RoW[0] if len(self.model.RoW) > 0 else None

        # quota domestica per questa commodity: accetta sia float sia dict
        qD_cfg = getattr(self, 'qD_final', 1.0)
        if isinstance(qD_cfg, dict):
            qD = float(qD_cfg.get(commodity, 1.0))
        else:
            qD = float(qD_cfg)
        qD = min(1.0, max(0.0, qD))
        qR = 1.0 - qD

        # Helper robusto prezzo
        def _price(s, comm):
            if s is None:
                return 0.0
            p = 0.0
            if hasattr(s, "get_price"):
                try:
                    p = s.get_price(comm)
                except TypeError:
                    try:
                        p = s.get_price()
                    except TypeError:
                        p = 0.0
            if not p:
                p = getattr(s, "prices", {}).get(comm, getattr(s, "price", 0.0))
            try:
                return float(p)
            except Exception:
                return 0.0

        p_dom = _price(dom, commodity)
        p_row = _price(row, commodity)

        # 1) acquisto DOMESTICO su quota-valore target
        spent_dom = 0.0
        if dom is not None and p_dom > 0.0 and qD > 0.0:
            alloc_dom = min(B, qD * B)
            # imposto temporaneamente il budget a alloc_dom
            prev_budget = self.consumption_budgets[commodity]
            self.consumption_budgets[commodity] = alloc_dom
            self.buy_from_seller(dom, commodity, True)  # aggiorna consumo/budget/conti
            spent_dom = max(0.0, alloc_dom - self.consumption_budgets.get(commodity, 0.0))
            # ripristino il budget residuo totale (non lasciamo budget "nascosto")
            self.consumption_budgets[commodity] = max(0.0, B - spent_dom)
            
            # 2) acquisto al RoW: quota estera + eventuale shortfall domestico
            shortfall_dom = max(0.0, qD * B - spent_dom)
            spent_row = 0.0
            if row is not None and p_row > 0.0 and (qR > 0.0 or shortfall_dom > 0.0):
                B_left = float(self.consumption_budgets.get(commodity, 0.0))
                alloc_row = min(B_left, qR * B + shortfall_dom)
                prev_budget = self.consumption_budgets[commodity]
                self.consumption_budgets[commodity] = alloc_row
                # is_my_seller=False: qui non vogliamo aggiornare il rationing sul "mio" seller
                self.buy_from_seller(row, commodity, False)
                spent_row = max(0.0, alloc_row - self.consumption_budgets.get(commodity, 0.0))
                self.consumption_budgets[commodity] = max(0.0, B - spent_dom - spent_row)
                
                # termina come nel modello base
            self.attempt_number += 1
              

    def buy_from_sellers_list(self, commodity):

        for seller in self.sellers_list.get(commodity, []):
            
            if getattr(seller, "supply", float("inf")) > 0:
                self.buy_from_seller(seller, commodity, False)
                break 



    def buy_from_seller(self, seller, commodity, is_my_seller):
        # Prezzo robusto (prima prova get_price(commodity), poi fallback)
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
            return  # niente acquisto se non ho un prezzo valido

        budget_left = self.consumption_budgets.get(commodity, 0.0)
        if budget_left <= 0:
            return

        demanded_quantity = budget_left / price
        if demanded_quantity <= 0:
            return

        # Vendita: prova la firma (commodity, q), fallback a (q)
        try:
            bought_quantity = seller.sell(commodity, demanded_quantity)
        except TypeError:
            bought_quantity = seller.sell(demanded_quantity)

        if is_my_seller and demanded_quantity > 0:
            self.rationing_level = 1 - bought_quantity / demanded_quantity

        consumption = bought_quantity * price
        if getattr(seller, 'is_RoW', False):
            self.spent_to_RoW_step += consumption
            self.spent_to_RoW_by_comm_step[commodity] = \
                self.spent_to_RoW_by_comm_step.get(commodity, 0.0) + consumption

        if consumption <= 0:
            return

        self.consumptions_qt[commodity] = self.consumptions_qt.get(commodity, 0.0) + bought_quantity
        self.consumption += consumption
        self.wealth -= consumption
        self.my_bank.deposits[self.id] -= consumption
        self.consumption_budgets[commodity] = max(0.0, budget_left - consumption)
        
   
        
    def receive_dividends(self, dividends):
        
        self.dividends += dividends
        self.wealth += dividends
        self.my_bank.deposits[self.id] += dividends

        
    def receive_wage(self, wage):
        
        self.wage = wage
        self.wealth += wage
        self.my_bank.deposits[self.id] += wage
        
    def receive_unemployment_benefit(self, ub):
        
        self.wage = ub
        self.wealth += ub
        self.my_bank.deposits[self.id] += ub  
        
    def receive_transfer(self, transfer_amount):
        
        self.gov_transfer = transfer_amount
        self.wealth += transfer_amount
        self.my_bank.deposits[self.id] += transfer_amount       
         
        
    def search_job(self):
                
        employers = self.model.localKAU_agents.select(self.model.localKAU_agents.flag_vacancies == 1)
        if employers:
            employer = employers.random()
            employer.hire(self)
            self.flag_employed = 1
            self.employer_id = employer.id

        
    def update_employement_status(self):
        
        self.flag_employed = 0
        self.employer_id = -1
        
    # def determine_disposable_income(self):
    #     # reset periodale
    #     self.labor_tax = 0.0
    #     self.dividend_tax = 0.0

    #     gov = self.model.Government[0] if hasattr(self.model, "Government") else None

    #     labor_rate = 0.0
    #     div_rate = 0.0
    #     if gov and hasattr(gov, "tax_rates"):
    #         # 'labor' può essere float o dict → prendi un flat rate se presente
    #         lr = gov.tax_rates.get('labor', 0.0)
    #         if isinstance(lr, dict):
    #             # primo valore o 0.0
    #             labor_rate = float(next(iter(lr.values()), 0.0))
    #         else:
    #             labor_rate = float(lr)
    #         div_rate = float(gov.tax_rates.get('dividends', 0.0) or 0.0)

    #     # calcolo imposte
    #     self.labor_tax = labor_rate * max(0.0, self.wage)
    #     self.dividend_tax = div_rate * max(0.0, self.dividends)

    #     # reddito disponibile
    #     self.disposable_income = (
    #         (self.wage - self.labor_tax) +
    #         (self.dividends - self.dividend_tax) +
    #         self.gov_transfer
    #     )

    #     # opzionale: accredita le tasse al Governo (se vuoi tenerne traccia)
    #     if gov:
    #         gov.receive_taxes(self.labor_tax + self.dividend_tax)
    
    # def determine_disposable_income(self):
        
    #     self.income = self.dividends + self.wage + self.gov_transfer
        
    #     rates = self.model.Government[0].tax_rates['labor']
    #     my_income_rate = 0
        
    #     for i, inc_class in enumerate(rates.key()):
            
    #         if(self.income < inc_class):
                
    #             my_income_rate = rates[inc_class]
    #             break
                
    #     self.labor_tax = self.wage*my_income_rate        
        
    #     self.dividend_tax = self.dividends*self.model.Government.tax_rates['dividends']
        
    #     self.disposable_income = self.income - self.labor_tax - self.dividend_tax
        
    def determine_disposable_income(self):
        self.income = self.dividends + self.wage + self.gov_transfer
        gov = self.model.Government[0]
        rates = gov.tax_rates.get('labor', {})  # {soglia: aliquota}
        brackets = sorted(rates.items())
        my_income_rate = brackets[-1][1] if brackets else 0.0
        for threshold, rate in brackets:
            if self.income < threshold:
                my_income_rate = rate
                break
        self.labor_tax = self.wage * my_income_rate
        self.dividend_tax = self.dividends * gov.tax_rates.get('dividends', 0.0)
        self.disposable_income = self.income - self.labor_tax - self.dividend_tax

    # def determine_disposable_income(self):
    #     # reset periodale
    #     self.labor_tax = 0.0
    #     self.dividend_tax = 0.0

    #     gov = self.model.Government[0] if hasattr(self.model, "Government") else None

    #     labor_rate = 0.0
    #     div_rate = 0.0
    #     if gov and hasattr(gov, "tax_rates"):
    #         lr = gov.tax_rates.get('labor', 0.0)
    #         if isinstance(lr, dict):
    #             labor_rate = float(next(iter(lr.values()), 0.0))  # semplice flat da dict
    #         else:
    #             labor_rate = float(lr)
    #         div_rate = float(gov.tax_rates.get('dividends', 0.0) or 0.0)

    #     # 👉 FIX: imposta SEMPRE il reddito lordo (usato per il GDP in update)
    #     self.income = max(0.0, self.wage) + max(0.0, self.dividends) + max(0.0, self.gov_transfer)

    #     # imposte
    #     self.labor_tax = labor_rate * max(0.0, self.wage)
    #     self.dividend_tax = div_rate * max(0.0, self.dividends)

    #     # reddito disponibile
    #     self.disposable_income = self.income - self.labor_tax - self.dividend_tax
        
    #     # (facoltativo) accredita le tasse al Governo
    #     if gov:
    #         gov.receive_taxes(self.labor_tax + self.dividend_tax)
        
    def pay_taxes(self):
        
        
        self.wealth -= self.labor_tax
        self.my_bank.deposits[self.id] -= self.labor_tax
        
        self.wealth -= self.dividend_tax
        self.my_bank.deposits[self.id] -= self.dividend_tax
        total = self.labor_tax + self.dividend_tax
        if hasattr(self.model.Government[0], "receive_taxes"):
            self.model.Government[0].receive_taxes(total)
        