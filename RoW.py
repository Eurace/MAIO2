# -*- coding: utf-8 -*-
"""
Created on Mon Jan 8 18:50:20 2024

@author: marce
"""

import agentpy as ap

class RoW(ap.Agent):
    
    def setup(self):
        
        # Consumo RoW (da GDP)
        self.consumption_budget = 0.0
        self.consumption_budgets = {}    # {commodity: budget}
        self.consumption_shares = {}     # {commodity: share}
        self.consumptions = {}           # {commodity: spesa effettiva}
        self.sails = {}                  # {commodity: vendite RoW -> verso domestico}
        self.net_exports = 0.0
        
        # Pesi fornitori quando RoW compra beni domestici
        # atteso: {commodity: {seller_index_or_agent: weight}}
        self.suppliers_weights = {}
        self.attempt_number = 0
        
        self.spent_domestic_step = 0.0                 # export totali del periodo (spesa RoW verso KAU domestiche)
        self.spent_domestic_by_comm_step = {}          # export per commodity del periodo

        # Bilancio estero sintetico
        self.liquidity = 0.0
        self.GDP = 0.0
        self.consumption2GDP = 0.0
        self.growth_rate = 0.0
        self.is_RoW = True
        # Prezzi di esportazione (RoW come venditore) per commodity
        self.prices = {}                 # {commodity: price}
        
        # IMPORTANT: per essere selezionabile come venditore
        self.supply = float('inf')       # offerta "illimitata" (venditore of-last-resort)

    # ------------------------
    # RoW come COMPRATORE
    # ------------------------
    # def determine_consumption_budgets(self):
    #     sm = getattr(self.model, "params", {}).get("stationary_mode", None)
    #     if sm and sm.get("active", False):
    #         self.consumption_budget = sum(sm['RoW_budgets'].values())
    #         self.consumption_budgets = {k: float(v) for k, v in sm['RoW_budgets'].items()}
    #         self.attempt_number = 0
    #         return

    #     self.consumption_budget = self.consumption2GDP * self.GDP
    #     for comm, share in self.consumption_shares.items():
    #         self.consumption_budgets[comm] = share * self.consumption_budget
    #         self.consumptions.setdefault(comm, 0.0)
    #         self.sails.setdefault(comm, 0.0)
    #     self.attempt_number = 0

    # def determine_consumption_budgets(self):
    #     self.consumption_budget = self.consumption2GDP * self.GDP
    #     for comm, share in self.consumption_shares.items():
    #         self.consumption_budgets[comm] = share * self.consumption_budget
    #         self.consumptions.setdefault(comm, 0.0)
    #         self.sails.setdefault(comm, 0.0)
    #     # compriamo un solo "giro" per commodity
    #     # --- NOVITÀ: attempt_number per commodity ---
    #     if not isinstance(self.attempt_number, dict):
    #         self.attempt_number = {}
    #     # reset per-commodity a inizio periodo
    #     for comm in self.consumption_shares.keys():
    #         self.attempt_number = 0
    
    def determine_consumption_budgets(self):
        self.spent_domestic_step = 0.0
        self.spent_domestic_by_comm_step = {}

        self.consumption_budget = self.consumption2GDP * self.GDP
        for comm, share in self.consumption_shares.items():
            self.consumption_budgets[comm] = share * self.consumption_budget
            self.consumptions.setdefault(comm, 0.0)
            self.sails.setdefault(comm, 0.0)
        # attempt per-commodity (1 solo giro d’acquisto per commodity)
        if not isinstance(self.attempt_number, dict):
            self.attempt_number = {}
        for comm in self.consumption_shares.keys():
            self.attempt_number[comm] = 0

    # def buy(self, commodity):
    #     # --- NOVITÀ: usa attempt per-commodity ---
    #     if not isinstance(self.attempt_number, dict):
    #         self.attempt_number = {}
    #     # compra solo al primo tentativo per commodity
    #     if self.attempt_number != 0:
    #         return

    #     budget = self.consumption_budgets.get(commodity, 0.0)
    #     if budget <= 0:
    #         self.attempt_number += 1
    #         return

    #     sellers_map = self.suppliers_weights.get(commodity, {})
    #     if not sellers_map:
    #         self.attempt_number += 1
    #         return

    #     # Normalizza chiavi: se sono indici -> agenti
    #     norm_items = []
    #     for key, w in sellers_map.items():
    #         ag = key
    #         if not isinstance(ag, ap.Agent):
    #             try:
    #                 ag = self.model.seller_agents[int(key)]
    #             except Exception:
    #                 ag = None
    #         if ag is not None and w > 0:
    #             norm_items.append((ag, float(w)))

    #     if not norm_items:
    #         self.attempt_number += 1
    #         return

    #     # Se i pesi non sommano a 1, li rinormalizzo
    #     tot_w = sum(w for _, w in norm_items)
    #     if tot_w > 0:
    #         norm_items = [(ag, w / tot_w) for ag, w in norm_items]

    #     # Spendo secondo i pesi
    #     resid = budget
    #     for ag, w in norm_items:
    #         if resid <= 0:
    #             break

    #         # prezzo robusto per commodity
    #         price = 0.0
    #         if hasattr(ag, "get_price"):
    #             try:
    #                 price = ag.get_price(commodity)  # se supporta argomento
    #             except TypeError:
    #                 try:
    #                     price = ag.get_price()
    #                 except TypeError:
    #                     price = 0.0
    #         if price <= 0:
    #             # fallback: prova mappa prezzi per commodity o attributo "price"
    #             price = getattr(ag, "prices", {}).get(commodity, getattr(ag, "price", 0.0))
    #         if price <= 0:
    #             continue

    #         planned_exp = min(resid, w * budget)
    #         demand = planned_exp / price if price > 0 else 0.0
    #         if demand <= 0:
    #             continue

    #         # venditore domestico vende la Q al RoW (entrata per domestico)
    #         bought_quantity = 0.0
    #         if hasattr(ag, "sell"):
    #             try:
    #                 # se accetta (commodity, q)
    #                 bought_quantity = ag.sell(commodity, demand)
    #             except TypeError:
    #                 # firma (q) classica
    #                 bought_quantity = ag.sell(demand)

    #         expenditure = bought_quantity * price
    #         if expenditure > 0:
    #             self.consumptions[commodity] += expenditure
    #             self.consumption_budgets[commodity] -= expenditure
    #             resid -= expenditure
    #             self.liquidity -= expenditure   # uscita di cassa dal RoW verso domestico

    #     self.attempt_number += 1

    def buy(self, commodity):
        if not isinstance(self.attempt_number, dict):
            self.attempt_number = {}
        # compra solo al primo tentativo per questa commodity
        if self.attempt_number.get(commodity, 0) != 0:
            return

        budget = self.consumption_budgets.get(commodity, 0.0)
        if budget <= 0:
            self.attempt_number[commodity] = 1
            return

        sellers_map = self.suppliers_weights.get(commodity, {})
        if not sellers_map:
            self.attempt_number[commodity] = 1
            return

        norm_items = []
        for key, w in sellers_map.items():
            ag = key
            if not isinstance(ag, ap.Agent):
                try:
                    ag = self.model.seller_agents[int(key)]
                except Exception:
                    ag = None
            if ag is not None and w > 0:
                norm_items.append((ag, float(w)))

        if not norm_items:
            self.attempt_number[commodity] = 1
            return

        tot_w = sum(w for _, w in norm_items)
        if tot_w > 0:
            norm_items = [(ag, w / tot_w) for ag, w in norm_items]

        resid = budget
        for ag, w in norm_items:
            if resid <= 0:
                break
            price = 0.0
            if hasattr(ag, "get_price"):
                try:
                    price = ag.get_price(commodity)
                except TypeError:
                    try:
                        price = ag.get_price()
                    except TypeError:
                        price = 0.0
            if price <= 0:
                price = getattr(ag, "prices", {}).get(commodity, getattr(ag, "price", 0.0))
            if price <= 0:
                continue

            planned_exp = min(resid, w * budget)
            demand = planned_exp / price if price > 0 else 0.0
            if demand <= 0:
                continue

            bought_quantity = 0.0
            if hasattr(ag, "sell"):
                try:
                    bought_quantity = ag.sell(commodity, demand)
                except TypeError:
                    bought_quantity = ag.sell(demand)

            expenditure = bought_quantity * price
            if expenditure > 0:
                self.consumptions[commodity] += expenditure
                self.consumption_budgets[commodity] -= expenditure
                resid -= expenditure
                self.liquidity -= expenditure
                
                self.spent_domestic_step += expenditure
                self.spent_domestic_by_comm_step[commodity] = \
                self.spent_domestic_by_comm_step.get(commodity, 0.0) + expenditure
        
        self.attempt_number[commodity] = 1

    # ------------------------
    # RoW come VENDITORE
    # ------------------------
    def get_price(self, commodity=None):
        """Prezzo di esportazione RoW per una data commodity.
        Compatibile con chiamate senza argomento (ritorna 0.0)."""
        if commodity is None:
            return 0.0
        return self.prices.get(commodity, 0.0)

    def sell(self, *args):
        """Supporta sia sell(q) sia sell(commodity, q)."""
        if len(args) == 1:
            # firma "legacy" (senza commodity): non sappiamo quale bene -> niente vendita
            q = float(args[0])
            return max(0.0, q) * 0.0  # 0 vendite perché manca la commodity
        elif len(args) == 2:
            commodity, demand = args
            q = max(0.0, float(demand))
            self.sails.setdefault(commodity, 0.0)
            self.sails[commodity] += q
            price = self.prices.get(commodity, 0.0)
            self.liquidity += price * q  # entrata in cassa RoW (export verso domestico)
            return q
        else:
            return 0.0

    # ------------------------
    # Altre routine
    # ------------------------
    def update_GDP(self):
        self.GDP *= (1 + self.growth_rate)
        for comm in self.consumption_shares.keys():
            self.sails[comm] = 0.0
            self.consumptions[comm] = 0.0
        
    # def reset_market_vars(self):
    #     self.attempt_number = 0
    
    def reset_market_vars(self):
    # no-op per preservare i contatori per-commodity
        if not isinstance(self.attempt_number, dict):
            self.attempt_number = {}

    def update_sellers_list(self, commodity):
        # Non usata per RoW (compriamo direttamente con pesi), tenuta per compatibilità
        pass
