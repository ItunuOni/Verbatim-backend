from supabase import create_client, Client
from app.schemas.config import settings


print("SUPABASE_URL:", settings.SUPABASE_URL)
print("SUPABASE_KEY (starts with):", settings.SUPABASE_KEY[:20])
print("SUPABASE_SERVICE_KEY (starts with):", settings.SUPABASE_SERVICE_KEY[:20])

# Use the PUBLIC ANON KEY for user auth
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
