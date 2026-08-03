from django.contrib import admin

from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'borrowed_at', 'due_date', 'returned_at')
    list_select_related = ('book', 'member')
    search_fields = ('book__title', 'member__email')
    list_filter = ('borrowed_at', 'returned_at')
