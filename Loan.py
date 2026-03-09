# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 09:04:52 2023

@author: marce
"""


class Loan(object):
    
    def __init__(self, granted_amount, remaining_amount, interest_rate, id_bank, id_firm, remaining_time, weighted_KAU_list):
        
        self.granted_amount = granted_amount
        self.remaining_amount = remaining_amount
        self.interest_rate = interest_rate
        self.id_bank = id_bank
        self.id_firm = id_firm
        self.remaining_time = remaining_time
        self.weighted_KAU_list = weighted_KAU_list
        
    # def determine_payment(self):
    #     n = self.remaining_time
    #     if n <= 0:
    #         return 0.0
    #     r = self.interest_rate
    #     if r == 0.0:
    #         # rimborso in quote capitale uguali
    #         return self.remaining_amount / n
    #     # rata costante (annuity)
    #     return r / (1.0 - (1.0 + r) ** (-n)) * self.remaining_amount

    def determine_payment(self):
        n = int(self.remaining_time)
        if n <= 0:
            return 0.0
        r = float(self.interest_rate)
        # Tratta r ~ 0 come caso lineare
        if abs(r) < 1e-12:
            return self.remaining_amount / n
        # rata alla francese (robusta)
        return r / (1.0 - (1.0 + r) ** (-n)) * self.remaining_amount

    def determine_interest_payment(self):
        r = self.interest_rate
        if r == 0.0 or self.remaining_time <= 0:
            return 0.0
        return r * self.remaining_amount


    def determine_capital_payment(self):
        total = self.determine_payment()
        interest = self.determine_interest_payment()
        cap = total - interest
        return cap if cap > 0.0 else 0.0

    
    def execute_payment(self):
        if self.remaining_time <= 0:
            return

        r = self.interest_rate
        payment = self.determine_payment()

        if r == 0.0:
            # solo capitale
            self.remaining_amount -= payment
        else:
            # aggiorna secondo (1+r)*debito - rata
            self.remaining_amount = (1.0 + r) * self.remaining_amount - payment

        # se manca un solo periodo, azzera eventuali residui numerici
        if self.remaining_time == 1 and self.remaining_amount < 1e-9:
            self.remaining_amount = 0.0

        # clamp di sicurezza contro piccole negatività
        if self.remaining_amount < 0.0 and abs(self.remaining_amount) < 1e-9:
            self.remaining_amount = 0.0

        #self.remaining_amount 
        
        