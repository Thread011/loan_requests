import logging
import re
import sys
from spyne import Application, rpc, ServiceBase, \
    Integer, AnyDict, Array, Boolean, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.util.wsgi_wrapper import run_twisted

logging.basicConfig(level=logging.DEBUG)

class credit_check_service(ServiceBase):

    @rpc(Integer, Integer, Integer, Integer, Boolean, _returns=Unicode)
    def credit_check(ctx, monthly_income, monthly_expenses, outstanding_debt, late_payments, has_bankruptcy):
                
        # Calculate credit score based on conditions
        score = 1000 - (outstanding_debt * 0.1) - (late_payments * 50)
                
        if has_bankruptcy:
            score -= 200
    
        solvency = "solvent" if score >= 700 and monthly_income > monthly_expenses else "not solvent"
        return solvency


# Define the Spyne application
application = Application([credit_check_service],
                          tns='spyne.examples.credit_check',
                          in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11()
)

# Run the application
if __name__ == '__main__':
    wsgi_app = WsgiApplication(application)
    
    twisted_apps = [
        (wsgi_app, b'credit_check_service'),
    ]
    
    sys.exit(run_twisted(twisted_apps, 8001))