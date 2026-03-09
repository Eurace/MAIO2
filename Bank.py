# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 09:13:48 2023

@author: marce
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 10:42:28 2023

@author: giaco
"""

import agentpy as ap
import numpy as np
import Loan as Loan

class Bank(ap.Agent):

    def setup(self):
        
        # balance sheet variables
        self.loans = []
        self.reserves = 0
        self.total_deposits = 0
        self.equity = 0
        self.deposits = {}
        
        
        # behavioural variables 
        self.CAR = 0                    
        self.threshold = 0
        self.interest_rate = 0
        
        self.repayment_time = 0
        
        self.interests_payment = 0
        self.dividends = 0
        
    def evaluate_request(self, firm, credit_requested):
        # blocca richieste nulle/negative
        if credit_requested is None or credit_requested <= 0:
            return Loan.Loan(0, 0, self.interest_rate, self.id, firm.id, self.repayment_time + 1, {})

        # gating super-semplice sul threshold (come nel tuo modello)
        if self.threshold > 0:
            new_loan = Loan.Loan(
                credit_requested,           # granted_amount
                credit_requested,           # remaining_amount
                self.interest_rate,
                self.id,                    # id_bank
                firm.id,                    # id_firm
                self.repayment_time + 1,    # remaining_time
                {}                          # weighted_KAU_list inizialmente vuoto (dict)
            )
            self.loans.append(new_loan)
            return new_loan

        # rifiuto
        return Loan.Loan(0, 0, self.interest_rate, self.id, firm.id, self.repayment_time + 1, {})

   
   

    def receive_payment(self, total_payment, interest_payment):
        self.reserves += total_payment
        if self.reserves < 0 and abs(self.reserves) < 1e-12:
            self.reserves = 0.0
        self.interests_payment += interest_payment

        
    
    def distribute_dividends(self):
        self.dividends = self.interests_payment
        self.interests_payment = 0.0

        n = len(self.model.Household_agents)
        if n <= 0 or self.dividends <= 0:
            return

        div_h = self.dividends / n
        for ag_h in self.model.Household_agents:
            ag_h.receive_dividends(div_h)

        self.reserves -= self.dividends
  
            
    def update_loans_list(self):
        
        for ln in self.loans[:]:
            
            if(ln.remaining_time <= 0):
                
                self.loans.remove(ln)
                
                
                
    def compute_total_deposits(self):
        
        self.total_deposits = sum(self.deposits.values())