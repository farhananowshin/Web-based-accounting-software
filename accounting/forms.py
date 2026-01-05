from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import Journal, Transaction, Account



class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput(), label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput(), label='Password Confirmation')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            self.add_error('password2', "Passwords don't match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# ==========================================
# 2. Account Management Form
# ==========================================
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Cash, Bank Account, Sales'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
        }


# ==========================================
# 3.Journal Header Form
# ==========================================
class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control-modern'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control-modern', 
                'placeholder': 'Enter transaction description...'
            }),
        }


# ==========================================
# 4. Transaction line Form
# ==========================================
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-control account-select'
            }),
            'debit': forms.NumberInput(attrs={
                'class': 'form-control-modern debit', 
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'credit': forms.NumberInput(attrs={
                'class': 'form-control-modern credit', 
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.all().order_by('name')
        
        self.fields['account'].required = False
        self.fields['debit'].required = False
        self.fields['credit'].required = False

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        debit = cleaned_data.get('debit') or 0
        credit = cleaned_data.get('credit') or 0
        
       
        if self.cleaned_data.get('DELETE'):
            return cleaned_data

        
        if not account and debit == 0 and credit == 0:
            return cleaned_data
        
        
        if (debit > 0 or credit > 0) and not account:
            raise forms.ValidationError("Please select an account.")
        
        
        if debit > 0 and credit > 0:
            raise forms.ValidationError("Enter either Debit or Credit, not both.")
        
       
        if debit < 0 or credit < 0:
            raise forms.ValidationError("Negative amounts are not allowed.")
        
        return cleaned_data


# ==========================================
# 5. TransactionFormSet (Final Setup)
# ==========================================
TransactionFormSet = inlineformset_factory(
    Journal,
    Transaction,
    form=TransactionForm,
    extra=1,          
    can_delete=True, 
    min_num=1,       
    validate_min=True 
)