# -*- coding: utf-8 -*-
"""
Created on Tue May  2 16:47:02 2023

@author: marce
"""

import agentpy as ap

class Firm(ap.Agent):
    
    def setup(self):
    
        self.KAU_list =[]
        self.wealth = 0
        self.cash_for_KAU = {}
        self.dividends = 0
        self.money_requests = {}
        self.equity = 0
        self.debt = 0
        self.loans_list = []
        self.KAU_debt_payment = {}
        self.KAU_dividends = {}

        self.my_bank = None
        
        self.deposit = 0
        # --- ADD in Firm.setup() ---
        self.loans_received_step = 0.0   # prestiti ricevuti in questo step
        self.repayments_step     = 0.0   # rimborsi di capitale effettuati in questo step
        self.dividends_paid_step = 0.0

    def create_dictionaries(self):
            
        for lk in self.KAU_list:
        
            self.money_requests[lk.id] = 0
            self.KAU_debt_payment[lk.id] = 0
            self.KAU_dividends[lk.id] = 0

        
    def set_cash_for_KAUs(self):
        numKAU = len(self.KAU_list)
        if numKAU <= 0:
            self.cash_for_KAU = {}
            return
        share = self.wealth / numKAU
        for lk in self.KAU_list:
            self.cash_for_KAU[lk.id] = share

    
        
    def distribute_dividends(self):
        self.dividends = 0.0
            
        for lk in self.KAU_list:
            # cap a zero: niente "dividendi negativi"
            kd = max(0.0, self.KAU_dividends.get(lk.id, 0.0))
            # paga al massimo la cassa allocata su quella KAU
            avail = max(0.0, self.cash_for_KAU.get(lk.id, 0.0))
            pay = min(kd, avail)

            self.dividends += pay
            self.cash_for_KAU[lk.id] = avail - pay
            self.KAU_dividends[lk.id] = 0.0  # azzera la richiesta dopo il pagamento
        
        # <<< AGGIUNTA: registra quanto la firm paga in questo step
        self.dividends_paid_step = float(self.dividends)
        
        if self.dividends > 0:
            for ag_h in self.model.Household_agents:
                share = ag_h.property_shares.get(self.id, 0.0)
                if share > 0:
                    ag_h.receive_dividends(self.dividends * share)

            # uscita di cassa effettiva
            self.my_bank.deposits[self.id] -= self.dividends
            self.wealth -= self.dividends


        
    def update_cash_for_KAU(self, KAU_id, delta_cash):
        
        self.cash_for_KAU[KAU_id] += delta_cash
        self.wealth += delta_cash
        self.my_bank.deposits[self.id] += delta_cash # VERSIONE VECCHIA
        # if self.my_bank is not None:  # AGGIUNTO DOPO ---------
        #     self.my_bank.deposits[self.id] = self.my_bank.deposits.get(self.id, 0.0)  + delta_cash
        
        
    def gather_KAU_request(self, KAU_id, request_amount):
      
        self.money_requests[KAU_id] = request_amount
        
        
    def reset_KAU_requests(self):
        
        for KAU_id in self.money_requests.keys():
            self.money_requests[KAU_id] = 0

    
    def send_credit_request(self):
        # 1) calcolo quota capitale e interessi dovuti su TUTTI i prestiti
        capital_payback = 0.0
        interests = 0.0
        for d in self.loans_list:
            payment = d.determine_payment()
            interest_payment = d.determine_interest_payment()

            capital_payback += (payment - interest_payment)
            interests += interest_payment

            # ripartisci su KAU secondo i pesi del prestito (se non c'è la chiave → peso 0)
            for lk in self.KAU_list:
                w = d.weighted_KAU_list.get(lk.id, 0.0)
                self.money_requests[lk.id] += w * (payment - interest_payment)
                self.KAU_debt_payment[lk.id] += w * payment
                # gli interessi riducono i dividendi, ma non devono generare dividendi negativi in payout
                self.KAU_dividends[lk.id] -= w * interest_payment

        # 2) aggiungi utili netti (non negativi) e sottrai cassa già allocata
        for lk in self.KAU_list:
            net = max(0.0, lk.net_earnings)
            self.money_requests[lk.id] += net
            self.KAU_dividends[lk.id] += net
            self.money_requests[lk.id] -= self.cash_for_KAU.get(lk.id, 0.0)

        # 3) totale richieste POSITIVE (ignora quelle negative)
        pos_requests = {k: max(0.0, v) for k, v in self.money_requests.items()}
        total_credit_request = sum(pos_requests.values())

        if total_credit_request > 0:
            print('\n Credit request ', total_credit_request)
            print('Capital repayment', capital_payback)
            print('Difference', capital_payback - total_credit_request, ' Interests', interests)

            new_loan = self.my_bank.evaluate_request(self, total_credit_request)

            # pesi proporzionali solo sulle richieste positive
            denom = sum(pos_requests.values())
            weighted_KAU_list = {k: (pos_requests[k] / denom) for k in pos_requests.keys()} if denom > 0 else {}
            
            if getattr(new_loan, 'granted_amount', 0.0) > 0:
                new_loan.weighted_KAU_list = weighted_KAU_list
                self.loans_list.append(new_loan)

                for lk in self.KAU_list:
                    w = weighted_KAU_list.get(lk.id, 0.0)
                    if w > 0:
                        self.update_cash_for_KAU(lk.id, new_loan.granted_amount * w)
                
                self.notify_loan_granted(new_loan.granted_amount)
                
        # 4) reset richieste (sempre, e **dentro** al metodo)
        self.reset_KAU_requests()
       


    def pay_wages(self):
        
        for lk in self.KAU_list:
            
            lk.pay_wages()
            # self.update_cash_for_KAU(lk.id, -lk.total_wage_payment)



    def execute_financial_payments(self):        
        
        #print('execution', self.id)
        for k_id in self.KAU_debt_payment.keys():
            
            self.update_cash_for_KAU(k_id, -self.KAU_debt_payment[k_id])

            self.KAU_debt_payment[k_id] = 0
            
            
        for l in self.loans_list:
            
            if(l.remaining_time <= self.my_bank.repayment_time):
                #print(l.id_bank)
                b = self.model.Bank_agents.select(self.model.Bank_agents.id == l.id_bank)[0]
                #print(b.id)
                payment = l.determine_payment()
                interest_payment = l.determine_interest_payment()
                
                # --- ADD: quota capitale rimborsata nello step
                principal_paid = max(0.0, payment - interest_payment)
                self.notify_principal_repaid(principal_paid)
        
                print(self.id)
                b.receive_payment(payment, interest_payment)
                l.execute_payment()
                
                
        self.pay_wages()
                
        self.distribute_dividends()
        
            
    def update_loans_age(self):
        
        for l in self.loans_list[:]:  # copia superficiale
            
            l.remaining_time -= 1
            if l.remaining_time <= 0:
                self.loans_list.remove(l)
                

    def compute_total_debt(self):
        
        self.debt = sum([l.remaining_amount for l in self.loans_list])
        
        
                
    def compute_wealth_from_dep(self):
        
        self.deposit = self.my_bank.deposits.get(self.id, 0.0)
        
        
    # --- ADD in Firm class ---
    def notify_loan_granted(self, amount: float):
        self.loans_received_step += float(amount)
        
    def notify_principal_repaid(self, principal: float):
        self.repayments_step += float(principal)
