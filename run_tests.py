#!/usr/bin/env python3
"""
Script para ejecutar tests con coverage desde Docker o directamente.
"""

import subprocess
import sys
import os


def run_tests():
    """Ejecuta los tests con coverage."""
    
    # Configurar variables de entorno para testing
    os.environ['TESTING'] = 'true'
    
    # Comando para ejecutar tests
    cmd = [
        sys.executable, '-m', 'pytest',
        '--cov=app',
        '--cov-branch', 
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov',
        '--cov-report=json:coverage.json',
        '--cov-fail-under=40',  # Bajamos el threshold inicial
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    print("🧪 Ejecutando tests con coverage...")
    print(f"Comando: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n✅ Tests ejecutados exitosamente!")
            print("📊 Reporte de coverage generado en htmlcov/index.html")
        else:
            print(f"\n❌ Tests fallaron con código: {result.returncode}")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ Error: pytest no encontrado.")
        print("💡 Ejecuta desde Docker: docker-compose exec api python run_tests.py")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
