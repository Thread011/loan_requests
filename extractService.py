import logging
import json
import re

logging.basicConfig(level=logging.DEBUG)

import sys
from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

class extract_information_service(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def text_to_json(ctx, text):
        # Define regex patterns for each field
        patterns = {
            'Nom du Client': r'Nom du Client:\s*(.*?)(?=\s*(Adresse|Email|Numéro de Téléphone|Montant du Prêt Demandé|Durée du Prêt|Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Adresse': r'Adresse:\s*(.*?)(?=\s*(Email|Numéro de Téléphone|Montant du Prêt Demandé|Durée du Prêt|Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Email': r'Email:\s*(.*?)(?=\s*(Numéro de Téléphone|Montant du Prêt Demandé|Durée du Prêt|Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Numéro de Téléphone': r'Numéro de Téléphone:\s*(.*?)(?=\s*(Montant du Prêt Demandé|Durée du Prêt|Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Montant du Prêt Demandé': r'Montant du Prêt Demandé:\s*(.*?)(?=\s*(Durée du Prêt|Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Durée du Prêt': r'Durée du Prêt:\s*(.*?)(?=\s*(Description de la Propriété|Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Description de la Propriété': r'Description de la Propriété:\s*(.*?)(?=\s*(Revenu Mensuel|Dépenses Mensuelles):|$)',
            'Revenu Mensuel': r'Revenu Mensuel:\s*(.*?)(?=\s*Dépenses Mensuelles:|$)',
            'Dépenses Mensuelles': r'Dépenses Mensuelles:\s*(.*?)(?=\s*$)'
        }
        

        # Create a dictionary to store the results
        result = {}

        # Search each field in the text using regex
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                result[field] = match.group(1).strip()

        # Convert the dictionary to JSON format
        json_result = json.dumps(result, indent=4, ensure_ascii=False)
        return json_result

            
application = Application([extract_information_service],
                          tns = 'spyne.examples.hello',
                          in_protocol = Soap11(validator='lxml'),
                          out_protocol = Soap11()
)

if __name__ == '__main__':
    
    wsgi_app = WsgiApplication(application)
    
    twisted_apps = [
        (wsgi_app, b'extract_information_service'),
    ]
    
    sys.exit(run_twisted(twisted_apps, 8000))

    
    
    