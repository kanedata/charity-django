from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "charity_django.companies"
    verbose_name = "Companies House Register"
    verbose_name_plural = "Companies House Register"
