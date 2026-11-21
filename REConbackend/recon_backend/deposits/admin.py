from django.contrib import admin
from .models import Deposit, WiFiSession, Bin, SystemSetting

admin.site.site_header = "RECON ADMIN"
admin.site.site_title = "RECON ADMIN"
admin.site.index_title = "RECON ADMIN"


class ReconStyledAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("admin/css/custom_admin.css",)
        }


@admin.register(Deposit)
class DepositAdmin(ReconStyledAdmin):
    pass


@admin.register(WiFiSession)
class WiFiSessionAdmin(ReconStyledAdmin):
    pass


@admin.register(Bin)
class BinAdmin(ReconStyledAdmin):
    pass


@admin.register(SystemSetting)
class SystemSettingAdmin(ReconStyledAdmin):
    pass