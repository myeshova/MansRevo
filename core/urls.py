from django.contrib import admin
from django.urls import path, include

# --- FORCE MASTER PRODUCTION PASSWORD OVERRIDE ON STARTUP ---
from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    # Wipe out any mismatched states
    User.objects.filter(username='myeshova').delete()
    # Create your true login entry straight to the cloud tables
    u = User.objects.create_superuser('myeshova', 'admin@example.com', 'MansRevoMaster2026!')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print("--- ONLINE ACCOUNT FORCED SUCCESSFULLY ---")
except Exception as e:
    print(f"Startup account script skipped: {e}")
# -------------------------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')), # Or whatever your store root inclusion path is named
]
