# propertyEvalService.py

import logging
import sys
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

logging.basicConfig(level=logging.DEBUG)

class PropertyDatabase:
    def __init__(self):
        # Simulated database of recent property sales in different regions
        self.market_data = {
            'Paris': {
                'apartment': {'price_per_sqm': 10000, 'recent_sales': 150},
                'house': {'price_per_sqm': 12000, 'recent_sales': 80}
            },
            'Lyon': {
                'apartment': {'price_per_sqm': 5000, 'recent_sales': 120},
                'house': {'price_per_sqm': 6000, 'recent_sales': 60}
            }
        }
        
        # Simulated database of legal regulations
        self.legal_regulations = {
            'Paris': {'min_size': 9, 'max_height': 25, 'protected_areas': ['Marais', 'Montmartre']},
            'Lyon': {'min_size': 14, 'max_height': 22, 'protected_areas': ['Vieux Lyon']}
        }

class property_evaluation_service(ServiceBase):
    def __init__(self):
        super(property_evaluation_service, self).__init__()
        self.db = PropertyDatabase()

    def _analyze_market_data(self, location, property_type, size_sqm):
        """Analyze market data to estimate property value"""
        if location not in self.db.market_data or property_type.lower() not in self.db.market_data[location]:
            raise KeyError("Location or property type not found in database")
            
        market_info = self.db.market_data[location][property_type.lower()]
        base_value = market_info['price_per_sqm'] * size_sqm
        
        # Adjust based on market activity
        market_activity_multiplier = min(1.1, max(0.9, market_info['recent_sales'] / 100))
        return base_value * market_activity_multiplier

    def _virtual_inspection(self, description):
        """Analyze property description for condition assessment"""
        description = description.lower()
        
        # Keywords indicating property condition
        positive_keywords = ['rénové', 'neuf', 'moderne', 'récent', 'lumineux']
        negative_keywords = ['travaux', 'rénover', 'ancien', 'humidité']
        
        # Count indicators
        positive_count = sum(1 for word in positive_keywords if word in description)
        negative_count = sum(1 for word in negative_keywords if word in description)
        
        # Determine condition and value multiplier
        if positive_count > negative_count:
            status = "Bon état"
            multiplier = 1.1
            notes = "Propriété bien entretenue"
        elif positive_count < negative_count:
            status = "Rénovation nécessaire"
            multiplier = 0.9
            notes = "Des travaux peuvent être nécessaires"
        else:
            status = "État moyen"
            multiplier = 1.0
            notes = "État général satisfaisant"
            
        return {
            'status': status,
            'value_multiplier': multiplier,
            'notes': notes
        }

    def _check_legal_compliance(self, location, size_sqm, description):
        """Check legal compliance of the property"""
        regulations = self.db.legal_regulations.get(location, {})
        
        # Check minimum size requirement
        if size_sqm < regulations.get('min_size', 0):
            return {
                'compliant': False,
                'reason': f"Surface insuffisante (minimum {regulations['min_size']}m²)"
            }
            
        # Check if in protected area
        description_lower = description.lower()
        for area in regulations.get('protected_areas', []):
            if area.lower() in description_lower:
                return {
                    'compliant': False,
                    'reason': f"Situé dans une zone protégée ({area})"
                }
                
        return {
            'compliant': True,
            'reason': None
        }

    @rpc(Unicode, Unicode, Float, Unicode, _returns=Unicode)
    def evaluate_property(ctx, location, property_type, size_sqm, description):
        """
        Evaluate a property based on market data, virtual inspection, and legal compliance.
        """
        try:
            # Create instance for this request
            service = property_evaluation_service()
            
            # 1. Market Data Analysis
            market_value = service._analyze_market_data(location, property_type, size_sqm)
            
            # 2. Virtual Inspection
            condition_assessment = service._virtual_inspection(description)
            
            # 3. Legal Compliance Check
            legal_status = service._check_legal_compliance(location, size_sqm, description)
            
            # Calculate final evaluation
            if not legal_status['compliant']:
                return f"NON CONFORME: {legal_status['reason']}"
                
            # Adjust market value based on condition
            final_value = market_value * condition_assessment['value_multiplier']
            
            return f"""EVALUATION DÉTAILLÉE:
Valeur Estimée: {final_value:,.2f} EUR
Analyse du Marché: {market_value:,.2f} EUR
État du Bien: {condition_assessment['status']}
Conformité Légale: {'Conforme' if legal_status['compliant'] else 'Non Conforme'}
Remarques: {condition_assessment['notes']}"""

        except KeyError:
            return "ERREUR: Localisation ou type de bien non reconnu"
        except Exception as e:
            logging.error(f"Evaluation error: {e}")
            return "ERREUR: Impossible d'évaluer la propriété"

# Define the Spyne application
application = Application([property_evaluation_service],
                        tns='spyne.examples.property_evaluation',
                        in_protocol=Soap11(validator='lxml'),
                        out_protocol=Soap11())

if __name__ == '__main__':
    wsgi_app = WsgiApplication(application)
    
    twisted_apps = [
        (wsgi_app, b'property_evaluation_service'),
    ]
    
    sys.exit(run_twisted(twisted_apps, 8003))