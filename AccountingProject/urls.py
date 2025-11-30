from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from accounting import views as accounting_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounting_views.dashboard_view, name='home'),

    # Auth
    path('register/', accounting_views.register_view, name='register'),
    path('login/', accounting_views.login_view, name='login'),
    path('logout/', accounting_views.logout_view, name='logout'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    # Core
    path('dashboard/', accounting_views.dashboard_view, name='dashboard'),

    # Journal
    path('journal/list/', accounting_views.journal_list_view, name='journal-list'),
    path('journal/create/', accounting_views.create_journal_view, name='journal-create'),
    path('journal/edit/<int:pk>/', accounting_views.update_journal_view, name='journal-edit'),
    path('journal/delete/<int:pk>/', accounting_views.delete_journal_view, name='journal-delete'),

    # Accounts
    path('accounts/', accounting_views.account_list_view, name='account-list'),
    path('accounts/add/', accounting_views.manage_account_view, name='account-add'),
    path('accounts/edit/<int:pk>/', accounting_views.manage_account_view, name='account-edit'),
    path('accounts/delete/<int:pk>/', accounting_views.delete_account_view, name='account-delete'),

    # AJAX
    path('ajax/add-account/', accounting_views.create_account_ajax, name='ajax-add-account'),

    # Reports
    path('ledger/<int:account_id>/', accounting_views.ledger_view, name='ledger'),
    path('report/trial-balance/', accounting_views.trial_balance_view, name='trial-balance'),
    path('report/income-statement/', accounting_views.income_statement_view, name='income-statement'),
    path('report/balance-sheet/', accounting_views.balance_sheet_view, name='balance-sheet'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
