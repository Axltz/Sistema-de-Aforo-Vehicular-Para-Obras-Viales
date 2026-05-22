from pathlib import Path

# Configuración de Supabase
# NOTA: La URL debe ser la base del proyecto (sin /rest/v1/)
SUPABASE_URL = "https://aeospnvtmvgcffolnllr.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlb3NwbnZ0bXZnY2Zmb2xubGxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxNTU1NzMsImV4cCI6MjA5NDczMTU3M30.8Uupw8SzpDjEFXZFcihUAilD4QD57Fw490SzgwPEOvs"

BASE_DIR = Path(__file__).resolve().parents[1]
