import logging
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from suds.client import Client
from spyne import ComplexModel, Unicode
import random
import re

logging.basicConfig(level=logging.DEBUG)

def parsing_val(value_str):
    if not value_str:
        return 0
    return int(value_str.replace('EUR', ''))


class DictionaryItem(ComplexModel):
    __namespace__ = ''
    key = Unicode
    value = Unicode

class FinancialDatabase:
    def __init__(self):
        self.clients = {
            'default_client': {
                'value_debt': 5000,
                'late_payments': 2,
                'has_bankruptcy': False
            }
        }

    def add_client(self, client_id, data):
        # Simulate some financial history when adding a new client
        self.clients[client_id] = {
            'value_debt': random.randint(1000, 1005),
            'late_payments': random.randint(0, 2),
            'has_bankruptcy': random.choice([True, False])
        }
        logging.info(f"Données financière ajoutées pour ID: {client_id}")

    def get_financial_data(self, client_id):
        if client_id not in self.clients:
            # Generate random data for new clients
            self.add_client(client_id)
        return self.clients.get(client_id)

class ClientDatabase:
    def __init__(self):
        self.clients = {}

    def add_client(self, client_id, data):
        self.clients[client_id] = data
        logging.info(f"Client {client_id} added to database")

    def get_client(self, client_id):
        return self.clients.get(client_id, None)

    def get_monthly_expenses(self, client_id):
        client_data = self.get_client(client_id)
        if client_data and 'Dépenses Mensuelles' in client_data:
            try:
                return parsing_val(client_data['Dépenses Mensuelles'])
            except ValueError:
                logging.error(f"Erreur parsing ID: {client_id}")
                return 0
        return 0
    
    def get_monthly_income(self, client_id):
        client_data = self.get_client(client_id)
        if client_data and 'Revenu Mensuel' in client_data:
            try:
                return parsing_val(client_data['Revenu Mensuel'])
            except ValueError as e:
                logging.error(f"Erreur parsing ID: {e}")
                return 0
        return 0


class ServiceComposite:
    def __init__(self):
        self.client_db = ClientDatabase()
        self.financial_db = FinancialDatabase()
        
        self.SERVICE_WSDL_EXTRACT = 'http://localhost:8000/extract_information_service?wsdl'
        self.SERVICE_WSDL_SOLVENCY = 'http://localhost:8001/credit_check_service?wsdl'
        self.SERVICE_WSDL_PROPERTY = 'http://localhost:8003/property_evaluation_service?wsdl'
        self.SERVICE_WSDL_APPROVAL = 'http://localhost:8004/approval_decision_service?wsdl'
        
        self.extract_client = Client(self.SERVICE_WSDL_EXTRACT)
        self.solvency_client = Client(self.SERVICE_WSDL_SOLVENCY)
        self.property_client = Client(self.SERVICE_WSDL_PROPERTY)
        self.approval_client = Client(self.SERVICE_WSDL_APPROVAL)

    def get_loan_amount(self, text):
        """Extract loan amount from text"""
        match = re.search(r'Montant du Prêt Demandé:\s*(\d+)\s*EUR', text)
        return float(match.group(1)) if match else 0

    def get_employment_years(self, text):
        """Extract employment years (simulated)"""
        # In reality, this would come from the application form
        return 3  # Default to 3 years for demonstration

    def get_approval_decision(self, client_id, text, property_evaluation):
        """Get approval decision for a loan application"""
        try:
            # Get financial data
            financial_data = self.financial_db.get_financial_data(client_id)
            
            # Extract credit score from solvency (simulated mapping)
            solvency = self.get_credit_check(client_id)
            credit_score = 750 if solvency == "solvent" else 650
            
            # Extract property value from evaluation
            value_match = re.search(r'Valeur Estimée: ([\d,]+\.?\d*)', property_evaluation)
            property_value = float(value_match.group(1).replace(',', '')) if value_match else 0
            
            # Get loan amount
            loan_amount = self.get_loan_amount(text)
            
            # Get monthly income and expenses
            monthly_income = self.client_db.get_monthly_income(client_id)
            monthly_expenses = self.client_db.get_monthly_expenses(client_id)
            
            # Get employment stability
            stable_employment_years = self.get_employment_years(text)
            
            # Call approval service
            decision = self.approval_client.service.evaluate_loan_application(
                credit_score=credit_score,
                property_value=property_value,
                loan_amount=loan_amount,
                monthly_income=monthly_income,
                monthly_expenses=monthly_expenses,
                stable_employment_years=stable_employment_years,
                late_payments=financial_data['late_payments'],
                has_bankruptcy=financial_data['has_bankruptcy'],
                property_valuation=property_value
            )
            
            return decision
            
        except Exception as e:
            logging.error(f"Failed to get approval decision: {e}")
            raise

    def extract_property_info(self, text):
        """Extract property information from loan request content"""
        # Extract location from address
        address_match = re.search(r'Adresse:\s*(.*?)(?=\s*\n|$)', text)
        location = "Paris"  # Default
        if address_match:
            address = address_match.group(1)
            if "Lyon" in address:
                location = "Lyon"
        
        # Extract property type and size from description
        description_match = re.search(r'Description de la Propriété:\s*(.*?)(?=\s*\n|$)', text)
        description = description_match.group(1) if description_match else ""
        
        property_type = "apartment"  # Default
        if any(word in description.lower() for word in ["maison", "villa", "pavillon"]):
            property_type = "house"
        
        # Try to extract size from description
        size_match = re.search(r'(\d+)\s*m²', description)
        size_sqm = float(size_match.group(1)) if size_match else 75.0  # Default size
        
        return {
            "location": location,
            "property_type": property_type,
            "size_sqm": size_sqm,
            "description": description
        }

    def evaluate_property(self, text):
        """Evaluate the property using the property evaluation service"""
        try:
            property_info = self.extract_property_info(text)
            
            # Call the property evaluation service
            return self.property_client.service.evaluate_property(
                location=property_info["location"],
                property_type=property_info["property_type"],
                size_sqm=property_info["size_sqm"],
                description=property_info["description"]
            )
            
        except Exception as e:
            logging.error(f"Property evaluation error: {e}")
            raise

    def process_and_store(self, client_id, text):
        try:
            # First evaluate the property
            property_evaluation = self.evaluate_property(text)
            if property_evaluation.startswith("NON CONFORME"):
                raise ValueError(property_evaluation)

            # Call information extraction service
            info_response = self.extract_client.service.text_to_json(text)
            client_data = json.loads(info_response)
            
            # Store client and financial data
            self.client_db.add_client(client_id, client_data)
            self.financial_db.add_client(client_id, {})
            
            # Get approval decision
            approval_decision = self.get_approval_decision(client_id, text, property_evaluation)
            
            logging.info(f"Client {client_id} processed with decision")
            
            return {
                "client_data": client_data,
                "property_evaluation": property_evaluation,
                "approval_decision": approval_decision
            }
            
        except Exception as e:
            logging.error(f"Failed to process and store client data: {e}")
            raise


    def get_client_info(self, client_id):
        client_data = self.client_db.get_client(client_id)
        if not client_data:
            raise ValueError(f"Aucun client trouvé avec ID: {client_id}")
        return client_data

    def get_credit_check(self, client_id):
        try:
            client_data = self.client_db.get_client(client_id)
            if not client_data:
                raise ValueError(f"Aucun client trouvé avec ID: {client_id}")

            financial_data = self.financial_db.get_financial_data(client_id)
            
            monthly_income = self.client_db.get_monthly_income(client_id)
            monthly_expenses = self.client_db.get_monthly_expenses(client_id)
            
            solvency = self.solvency_client.service.credit_check(
                monthly_income=monthly_income,
                monthly_expenses=monthly_expenses,
                outstanding_debt=financial_data['value_debt'],
                late_payments=financial_data['late_payments'],
                has_bankruptcy=financial_data['has_bankruptcy']
            )
            
            return solvency
            
        except Exception as e:
            logging.error(f"Failed to perform credit check: {e}")
            raise