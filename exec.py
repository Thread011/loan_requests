import subprocess
import time
import sys

SERVICES = [
    ('Service extraction', 'extractService.py'),
    ('Service Solvabilité', 'checkSolvabService.py'),
    ('Service Estimation', 'propEvalService.py'),
    ('Service Décision', 'decisionService.py'),
    ('Service API', 'api_service.py')
]

def start_services():
    processes = []
    for name, file in SERVICES:
        print(f"Starting {name}...")
        process = subprocess.Popen([sys.executable, file])
        processes.append(process)
        time.sleep(3) 
    
    print("Tout les services sont en exécution. Ctrl+C pour arrêter.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt des services...")
        for process in processes:
            process.terminate()

if __name__ == '__main__':
    start_services()