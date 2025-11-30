from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q, Sum

# Import Forms and Models
from .forms import JournalForm, TransactionFormSet, UserRegistrationForm, AccountForm
from .models import Journal, Transaction, Account, CompanySettings

# ==========================================
# 1. AUTHENTICATION
# ==========================================

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserRegistrationForm()
    
    company = CompanySettings.objects.first()
    return render(request, 'register.html', {'form': form, 'company': company})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.POST.get('remember_me'):
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    company = CompanySettings.objects.first()
    return render(request, 'login.html', {'form': form, 'company': company})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Logged out successfully.')
        return redirect('login')
    return redirect('dashboard')

# ==========================================
# 2. DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    try:
        company = CompanySettings.objects.first()
        accounts = Account.objects.all()
        
        total_assets = 0
        total_liabilities = 0
        total_revenue = 0
        total_expense = 0
        
        expense_labels = []
        expense_data = []

        for acc in accounts:
            # ড্যাশবোর্ডে আমরা সবসময় কারেন্ট ব্যালেন্স দেখাবো
            balance = acc.get_balance() 
            
            if acc.account_type == 'Asset':
                total_assets += balance
            elif acc.account_type == 'Liability':
                total_liabilities += balance
            elif acc.account_type == 'Revenue':
                total_revenue += balance
            elif acc.account_type == 'Expense':
                total_expense += balance
                if balance > 0:
                    expense_labels.append(acc.name)
                    expense_data.append(float(balance))

        net_profit = total_revenue - total_expense

        context = {
            'company': company,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'net_profit': net_profit,
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'accounts': accounts,
            'expense_labels': expense_labels,
            'expense_data': expense_data,
        }
        return render(request, 'dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Dashboard error: {str(e)}')
        return render(request, 'dashboard.html', {})

# ==========================================
# 3. JOURNAL MANAGEMENT
# ==========================================

@login_required
def create_journal_view(request):
    return handle_journal_form(request, title="Create Journal Entry", button_text="Post Entry")

@login_required
def update_journal_view(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    return handle_journal_form(request, journal, "Edit Journal Entry", "Update Entry")

@login_required
def handle_journal_form(request, journal=None, title="", button_text=""):
    if request.method == "POST":
        form = JournalForm(request.POST, instance=journal)
        formset = TransactionFormSet(request.POST, instance=journal)
        
        if form.is_valid() and formset.is_valid():
            if 'save_draft' in request.POST:
                status = 'Draft'
                msg = "Journal saved as Draft!"
            else:
                status = 'Posted'
                msg = "Journal Posted Successfully!"

            total_debit = 0
            total_credit = 0
            valid_lines = 0

            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE'):
                    debit = line_form.cleaned_data.get('debit') or 0
                    credit = line_form.cleaned_data.get('credit') or 0
                    if debit == 0 and credit == 0: continue
                    total_debit += debit
                    total_credit += credit
                    valid_lines += 1

            if valid_lines < 2:
                messages.error(request, "At least 2 valid lines required.")
                return render(request, 'journal_form.html', {'form': form, 'formset': formset, 'title': title, 'button_text': button_text})

            if status == 'Posted' and abs(total_debit - total_credit) > 0.01:
                messages.error(request, f"Unbalanced! Dr: {total_debit}, Cr: {total_credit}")
                return render(request, 'journal_form.html', {'form': form, 'formset': formset, 'title': title, 'button_text': button_text})

            try:
                with transaction.atomic():
                    journal_obj = form.save(commit=False)
                    journal_obj.status = status
                    journal_obj.save()
                    
                    if journal: journal.transactions.all().delete()
                    
                    for line_form in formset:
                        if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE'):
                            debit = line_form.cleaned_data.get('debit') or 0
                            credit = line_form.cleaned_data.get('credit') or 0
                            if debit == 0 and credit == 0: continue
                            
                            line = line_form.save(commit=False)
                            line.journal = journal_obj
                            line.save()
                    
                    messages.success(request, msg)
                    return redirect('journal-list')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = JournalForm(instance=journal)
        formset = TransactionFormSet(instance=journal)
    
    return render(request, 'journal_form.html', {'form': form, 'formset': formset, 'title': title, 'button_text': button_text})

@login_required
def journal_list_view(request):
    selected_date = request.GET.get('date', '').strip()
    search_query = request.GET.get('search', '').strip()
    journals = Journal.objects.all().order_by('-date', '-id')

    if selected_date:
        journals = journals.filter(date=selected_date)
    if search_query:
        journals = journals.filter(
            Q(description__icontains=search_query) |
            Q(transactions__account__name__icontains=search_query)
        ).distinct()

    return render(request, 'journal_list.html', {'journals': journals, 'selected_date': selected_date, 'search_query': search_query})

@login_required
def delete_journal_view(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    if request.method == "POST":
        journal.delete()
        messages.success(request, 'Journal deleted!')
        return redirect('journal-list')
    return render(request, 'journal_confirm_delete.html', {'journal': journal})

# ==========================================
# 4. ACCOUNT MANAGEMENT
# ==========================================

@csrf_exempt
@login_required
def create_account_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            account_type = data.get('account_type', '').strip()
            
            if Account.objects.filter(name__iexact=name).exists():
                return JsonResponse({'status': 'error', 'message': 'Account exists!'})
            
            account = Account.objects.create(name=name, account_type=account_type)
            return JsonResponse({'status': 'success', 'id': account.id, 'name': account.name})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def account_list_view(request):
    search_query = request.GET.get('search', '').strip()
    accounts = Account.objects.all().order_by('account_type', 'name')
    if search_query:
        accounts = accounts.filter(Q(name__icontains=search_query) | Q(account_type__icontains=search_query))
    
    account_data = []
    for account in accounts:
        # অ্যাকাউন্ট লিস্টে সব সময় কারেন্ট ব্যালেন্স দেখাবে
        balance = account.get_balance() 
        account_data.append({
            'id': account.id, 'name': account.name, 'account_type': account.account_type,
            'balance': balance, 'balance_abs': abs(balance), 'is_negative': balance < 0,
        })
    
    return render(request, 'account_list.html', {'accounts': account_data, 'search_query': search_query})

@login_required
def manage_account_view(request, pk=None):
    account = get_object_or_404(Account, pk=pk) if pk else None
    title = "Edit Account" if pk else "Add New Account"
    form = AccountForm(request.POST or None, instance=account)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, 'Account saved!')
        return redirect('account-list')
    return render(request, 'account_form.html', {'form': form, 'title': title})

@login_required
def delete_account_view(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        try:
            account.delete()
            messages.success(request, 'Account deleted!')
        except:
            messages.error(request, 'Cannot delete used account.')
    return redirect('account-list')

# ==========================================
# 5. REPORTS (DATE FILTER ENABLED)
# ==========================================

@login_required
def ledger_view(request, account_id):
    account = get_object_or_404(Account, pk=account_id)
    transactions = Transaction.objects.filter(account=account, journal__status='Posted').select_related('journal').order_by('journal__date', 'id')
    
    balance = 0
    ledger_data = []
    
    for t in transactions:
        if account.account_type in ['Asset', 'Expense']:
            balance += (t.debit - t.credit)
        else:
            balance += (t.credit - t.debit)
        
        ledger_data.append({
            'date': t.journal.date, 'description': t.journal.description,
            'journal_ref': t.journal.id, 'debit': t.debit, 'credit': t.credit, 'balance': balance
        })
    
    return render(request, 'ledger.html', {'account': account, 'ledger_data': ledger_data, 'current_balance': balance})

@login_required
def trial_balance_view(request):
    """Trial Balance with Date Filter"""
    # 1. ইউজার কোনো ডেট সিলেক্ট করেছে কিনা তা চেক করা
    selected_date = request.GET.get('date')
    
    accounts = Account.objects.all()
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for account in accounts:
        # 2. ডেট মডেলে পাঠিয়ে দেওয়া হচ্ছে
        balance = account.get_balance(selected_date)
        
        if balance == 0: continue
        
        entry = {'account': account.name, 'type': account.account_type, 'debit': 0, 'credit': 0}
        
        if account.account_type in ['Asset', 'Expense']:
            if balance >= 0:
                entry['debit'] = balance
                total_debit += balance
            else:
                entry['credit'] = abs(balance)
                total_credit += abs(balance)
        else:
            if balance >= 0:
                entry['credit'] = balance
                total_credit += balance
            else:
                entry['debit'] = abs(balance)
                total_debit += abs(balance)
        
        trial_balance.append(entry)
    
    return render(request, 'trial_balance.html', {
        'trial_balance': trial_balance, 
        'total_debit': total_debit, 
        'total_credit': total_credit,
        'selected_date': selected_date # ডেট টেমপ্লেটে ফেরত পাঠানো
    })

@login_required
def income_statement_view(request):
    """Income Statement with Date Filter"""
    selected_date = request.GET.get('date')
    
    revenues = Account.objects.filter(account_type='Revenue')
    expenses = Account.objects.filter(account_type='Expense')
    
    # 3. সব জায়গায় selected_date ব্যবহার করা হচ্ছে
    total_revenue = sum(a.get_balance(selected_date) for a in revenues)
    total_expense = sum(a.get_balance(selected_date) for a in expenses)
    net_profit = total_revenue - total_expense

    return render(request, 'income_statement.html', {
        'revenues': revenues, 'expenses': expenses,
        'total_revenue': total_revenue, 'total_expense': total_expense, 
        'net_profit': net_profit,
        'selected_date': selected_date
    })

@login_required
def balance_sheet_view(request):
    """Balance Sheet with Date Filter"""
    selected_date = request.GET.get('date')
    
    # Calculate Net Profit upto date
    rev_total = sum(a.get_balance(selected_date) for a in Account.objects.filter(account_type='Revenue'))
    exp_total = sum(a.get_balance(selected_date) for a in Account.objects.filter(account_type='Expense'))
    net_profit = rev_total - exp_total
    
    assets = Account.objects.filter(account_type='Asset')
    liabilities = Account.objects.filter(account_type='Liability')
    equity = Account.objects.filter(account_type='Equity')
    
    # Pass date to all get_balance calls
    total_assets = sum(a.get_balance(selected_date) for a in assets)
    total_liabilities = sum(a.get_balance(selected_date) for a in liabilities)
    capital_base = sum(a.get_balance(selected_date) for a in equity)
    
    total_equity_with_profit = capital_base + net_profit
    total_liab_equity = total_liabilities + total_equity_with_profit
    
    return render(request, 'balance_sheet.html', {
        'assets': assets, 'liabilities': liabilities, 'equity_accounts': equity,
        'net_profit': net_profit, 'total_assets': total_assets,
        'total_liabilities': total_liabilities, 'capital_base': capital_base,
        'total_equity_with_profit': total_equity_with_profit,
        'total_liab_equity': total_liab_equity,
        'selected_date': selected_date
    })