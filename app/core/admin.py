from django.contrib import admin

from .models import Book, BorrowRecord, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user_type')
    search_fields = ('name', 'email')
    list_filter = ('user_type',)


class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'total_copies', 'available_copies')
    search_fields = ('title', 'author')
    list_filter = ('author',)


class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'borrowed_at', 'due_date', 'returned_at')
    search_fields = ('book__title', 'member__email')
    list_filter = ('borrowed_at', 'returned_at')


admin.site.register(User, UserAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BorrowRecord, BorrowRecordAdmin)
