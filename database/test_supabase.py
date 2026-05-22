"""
test_supabase.py — Verificación rápida de conectividad con Supabase
Ejecutar desde la raíz del proyecto:
  python -m database.test_supabase
"""
import sys
import os

# Añadir la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SUPABASE_URL, SUPABASE_ANON_KEY

def main():
    print("=" * 60)
    print("  TEST DE CONEXIÓN A SUPABASE")
    print("=" * 60)
    
    # 1. Verificar credenciales
    print(f"\n📋 URL:  {SUPABASE_URL}")
    print(f"📋 Key:  {SUPABASE_ANON_KEY[:20]}...{SUPABASE_ANON_KEY[-10:]}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("\n❌ ERROR: Las credenciales están vacías.")
        print("   Revisa src/config.py")
        return False
    
    # 2. Crear cliente
    print("\n🔄 Creando cliente Supabase...")
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("✅ Cliente creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        print("   ¿Instalaste supabase-py? → pip install supabase")
        return False
    
    # 3. Insertar dato de prueba
    print("\n🔄 Insertando dato de prueba...")
    try:
        test_data = {
            "total_count": 42,
            "data": {
                "total_vehicles": 5,
                "flujo_por_minuto": 12.3,
                "interaccion_pct": 35.7,
                "fluidez_avance": "FLUJO LIBRE",
                "velocidad_marcha": "FLUJO MODERADO",
                "alerta_embotellamiento": False,
                "conteo_grupos_activos": 1,
                "cluster_metrics": [
                    {
                        "nombre": "Grupo de Vehiculos",
                        "conteo": 3,
                        "riesgo": "BAJO",
                        "densidad_pct": 60.0,
                        "velocidad": 12.3,
                        "ids": [1, 2, 3]
                    }
                ]
            }
        }
        
        response = client.table("metrics").insert(test_data).execute()
        
        if response.data and len(response.data) > 0:
            row = response.data[0]
            print(f"✅ Dato insertado correctamente!")
            print(f"   ID:        {row['id']}")
            print(f"   Timestamp: {row['ts']}")
            print(f"   Count:     {row['total_count']}")
        else:
            print("⚠️  Respuesta vacía (puede que las políticas RLS bloqueen la inserción)")
            print("   Verifica que ejecutaste el setup.sql en Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Error insertando dato: {e}")
        print("\n   POSIBLES CAUSAS:")
        print("   1. No has ejecutado setup.sql en Supabase SQL Editor")
        print("   2. La tabla 'metrics' no existe")
        print("   3. Las políticas RLS no están configuradas")
        return False
    
    # 4. Leer datos
    print("\n🔄 Leyendo datos de la tabla...")
    try:
        response = client.table("metrics") \
            .select("*") \
            .order("ts", desc=True) \
            .limit(5) \
            .execute()
        
        if response.data:
            print(f"✅ {len(response.data)} registro(s) encontrados:")
            for row in response.data:
                ts = row['ts'][:19].replace('T', ' ')
                d = row.get('data', {})
                print(f"   [{ts}] Count={row['total_count']} | Flujo={d.get('flujo_por_minuto', '?')} veh/min | Estado={d.get('fluidez_avance', '?')}")
        else:
            print("⚠️  No se encontraron registros")
            return False
            
    except Exception as e:
        print(f"❌ Error leyendo datos: {e}")
        return False
    
    # 5. Resultado final
    print("\n" + "=" * 60)
    print("  ✅ ¡TODAS LAS PRUEBAS PASARON!")
    print("  El frontend debería mostrar los datos automáticamente.")
    print("  Abre index.html en el navegador para verificar.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
