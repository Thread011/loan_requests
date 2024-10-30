import logging
import sys
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

logging.basicConfig(level=logging.DEBUG)

class InstitutionPolicies:
    def __init__(self):
        # Simulated institution policies
        self.policies = {
            'credit_score_minimum': 700,
            'max_debt_to_income_ratio': 0.45,  # 45% maximum
            'min_stable_employment_years': 2,
            'max_loan_to_value_ratio': 0.85,  # 85% maximum
            'min_credit_history_years': 3,
            'interest_rates': {
                'excellent': 0.029,  # 2.9%
                'good': 0.034,      # 3.4%
                'average': 0.039,   # 3.9%
                'poor': 0.045       # 4.5%
            }
        }

class RiskAnalysis:
    @staticmethod
    def calculate_risk_score(credit_score, property_value, loan_amount, 
                           monthly_income, monthly_expenses, stable_employment,
                           payment_history):
        try:
            # Calculate key ratios
            debt_to_income = (monthly_expenses / monthly_income)
            loan_to_value = loan_amount / property_value
            
            # Base score starts at 100
            risk_score = 100
            
            # Adjust based on credit score
            risk_score += (credit_score - 700) / 10
            
            # Adjust based on debt-to-income ratio (lower is better)
            risk_score -= (debt_to_income * 100)
            
            # Adjust based on loan-to-value ratio
            risk_score -= (loan_to_value * 50)
            
            # Adjust based on employment stability
            risk_score += (stable_employment * 5)
            
            # Adjust based on payment history (negative impact for late payments)
            risk_score -= (payment_history['late_payments'] * 10)
            if payment_history['has_bankruptcy']:
                risk_score -= 50
                
            return max(0, min(100, risk_score))  # Clamp between 0 and 100
            
        except Exception as e:
            logging.error(f"Error calculating risk score: {e}")
            return 0

class PredictionModel:
    @staticmethod
    def predict_default_probability(risk_score, debt_to_income, loan_to_value,
                                  stable_employment, payment_history):
        try:
            # Simple prediction model (in reality, this would be a trained ML model)
            base_probability = (100 - risk_score) / 100
            
            # Adjust based on key factors
            adjustments = [
                1.5 if debt_to_income > 0.45 else 0.8,
                1.3 if loan_to_value > 0.85 else 0.9,
                0.7 if stable_employment >= 2 else 1.2,
                1.5 if payment_history['late_payments'] > 2 else 0.9,
                2.0 if payment_history['has_bankruptcy'] else 1.0
            ]
            
            # Apply all adjustments
            for adj in adjustments:
                base_probability *= adj
                
            return min(1.0, base_probability)  # Cap at 100%
            
        except Exception as e:
            logging.error(f"Error predicting default probability: {e}")
            return 1.0  # Return highest risk on error

class approval_decision_service(ServiceBase):
    def __init__(self):
        super(approval_decision_service, self).__init__()
        self.policies = InstitutionPolicies()
        self.risk_analyzer = RiskAnalysis()
        self.prediction_model = PredictionModel()

    @rpc(Float, Float, Float, Float, Float, Integer, Integer, Boolean, 
         Float, _returns=Unicode)
    def evaluate_loan_application(ctx, credit_score, property_value, loan_amount,
                                monthly_income, monthly_expenses, stable_employment_years,
                                late_payments, has_bankruptcy, property_valuation):
        """
        Evaluate a loan application and make an approval decision
        """
        try:
            service = approval_decision_service()
            policies = service.policies.policies
            
            # 1. Risk Analysis
            payment_history = {
                'late_payments': late_payments,
                'has_bankruptcy': has_bankruptcy
            }
            
            risk_score = RiskAnalysis.calculate_risk_score(
                credit_score, property_value, loan_amount,
                monthly_income, monthly_expenses, stable_employment_years,
                payment_history
            )
            
            # 2. Check Institution Policies
            debt_to_income = monthly_expenses / monthly_income
            loan_to_value = loan_amount / property_value
            
            policy_violations = []
            if credit_score < policies['credit_score_minimum']:
                policy_violations.append("Score de crédit insuffisant")
            if debt_to_income > policies['max_debt_to_income_ratio']:
                policy_violations.append("Ratio dette/revenu trop élevé")
            if loan_to_value > policies['max_loan_to_value_ratio']:
                policy_violations.append("Ratio prêt/valeur trop élevé")
            if stable_employment_years < policies['min_stable_employment_years']:
                policy_violations.append("Stabilité d'emploi insuffisante")
            
            # 3. Prediction Model
            default_probability = PredictionModel.predict_default_probability(
                risk_score, debt_to_income, loan_to_value,
                stable_employment_years, payment_history
            )
            
            # 4. Make Decision
            is_approved = len(policy_violations) == 0 and default_probability < 0.3
            
            # 5. Determine Loan Terms if approved
            if is_approved:
                # Determine interest rate based on risk score
                if risk_score >= 80:
                    interest_rate = policies['interest_rates']['excellent']
                elif risk_score >= 70:
                    interest_rate = policies['interest_rates']['good']
                elif risk_score >= 60:
                    interest_rate = policies['interest_rates']['average']
                else:
                    interest_rate = policies['interest_rates']['poor']
                
                return f"""DÉCISION: APPROUVÉ
Score de Risque: {risk_score:.1f}/100
Probabilité de Défaut: {default_probability:.1%}
Taux d'Intérêt Proposé: {interest_rate:.1%}
Montant Approuvé: {loan_amount:,.2f} EUR"""
            
            else:
                reasons = '\n'.join(f"- {v}" for v in policy_violations)
                return f"""DÉCISION: REFUSÉ
Score de Risque: {risk_score:.1f}/100
Probabilité de Défaut: {default_probability:.1%}
Raisons:
{reasons}
Recommandations:
- Améliorer le score de crédit
- Réduire le ratio dette/revenu
- Augmenter la période d'emploi stable"""

        except Exception as e:
            logging.error(f"Evaluation error: {e}")
            return "ERREUR: Impossible d'évaluer la demande de prêt"

application = Application([approval_decision_service],
                        tns='spyne.examples.approval_decision',
                        in_protocol=Soap11(validator='lxml'),
                        out_protocol=Soap11())

if __name__ == '__main__':
    wsgi_app = WsgiApplication(application)
    
    twisted_apps = [
        (wsgi_app, b'approval_decision_service'),
    ]
    
    sys.exit(run_twisted(twisted_apps, 8004))