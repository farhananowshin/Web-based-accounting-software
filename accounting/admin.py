from django.contrib import admin
from django.utils.html import format_html
from .models import Account, Journal, Transaction, CompanySettings


# ===========================================
# Account Admin
# ===========================================
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type')
    list_filter = ('account_type',)
    search_fields = ('name',)
    ordering = ('name',)


# ===========================================
# Transaction Inline (Journal এর ভেতরে)
# ===========================================
class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 2
    fields = ('account', 'debit', 'credit')


# ===========================================
# Journal Admin
# ===========================================
@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'description', 'status', 'get_total_amount')
    list_filter = ('status', 'date')
    search_fields = ('description',)
    date_hierarchy = 'date'
    inlines = [TransactionInline]
    
    def get_total_amount(self, obj):
        return f"৳ {obj.get_total_amount():,.2f}"
    get_total_amount.short_description = 'Total Amount'


# ===========================================
# Company Settings Admin (Logo Upload সহ)
# ===========================================
@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'tagline', 'currency_symbol', 'logo_status')
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'tagline', 'currency_symbol')
        }),
        ('Branding', {
            'fields': ('logo', 'logo_preview')
        }),
    )
    readonly_fields = ('logo_preview',)
    
    # Logo preview দেখানোর জন্য
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.logo.url
            )
        return format_html('<span style="color: #999;">No logo uploaded yet</span>')
    
    logo_preview.short_description = 'Current Logo Preview'
    
    # Logo status column for list view
    def logo_status(self, obj):
        if obj.logo:
            return format_html('<span style="color: green;">✓ Uploaded</span>')
        return format_html('<span style="color: #999;">No Logo</span>')
    
    logo_status.short_description = 'Logo'

    # একাধিক সেটিংস যেন তৈরি না হয়
    def has_add_permission(self, request):
        # যদি কোনো CompanySettings object already থাকে, তাহলে নতুন add করতে দেবে না
        if CompanySettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    # Delete করতে না দেওয়ার জন্য (optional - চাইলে রাখতে পারো)
    def has_delete_permission(self, request, obj=None):
        # Company settings delete করতে দিতে চাইলে True করে দাও
        return True
