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
# ২. Account Management Form
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
# ৩. জার্নাল হেডার ফর্ম
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
# ৪. ট্রানজ্যাকশন লাইন ফর্ম
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
        # আমরা ভিউ থেকে ভ্যালিডেশন হ্যান্ডেল করব, তাই এখানে রিকোয়ার্ড ফলস রাখছি
        self.fields['account'].required = False
        self.fields['debit'].required = False
        self.fields['credit'].required = False

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        debit = cleaned_data.get('debit') or 0
        credit = cleaned_data.get('credit') or 0
        
        # যদি লাইনটি ডিলিট করার জন্য মার্ক করা থাকে, তবে ভ্যালিডেশনের দরকার নেই
        if self.cleaned_data.get('DELETE'):
            return cleaned_data

        # যদি লাইনটি পুরোপুরি খালি হয়, তবে ইগনোর করুন
        if not account and debit == 0 and credit == 0:
            return cleaned_data
        
        # যদি এমাউন্ট থাকে কিন্তু অ্যাকাউন্ট না থাকে
        if (debit > 0 or credit > 0) and not account:
            raise forms.ValidationError("Please select an account.")
        
        # একই লাইনে ডেবিট ও ক্রেডিট উভয়ই থাকতে পারবে না
        if debit > 0 and credit > 0:
            raise forms.ValidationError("Enter either Debit or Credit, not both.")
        
        # নেগেটিভ এমাউন্ট চেক
        if debit < 0 or credit < 0:
            raise forms.ValidationError("Negative amounts are not allowed.")
        
        return cleaned_data


# ==========================================
# ৫. TransactionFormSet (Final Setup)
# ==========================================
TransactionFormSet = inlineformset_factory(
    Journal,
    Transaction,
    form=TransactionForm,
    extra=1,          # শুরুতে ১টি খালি লাইন দেখাবে (আপনি চাইলে ৫ করতে পারেন)
    can_delete=True,  # ডিলিট বাটন কাজ করবে
    min_num=1,        # অন্তত ১টি লাইন থাকতেই হবে
    validate_min=True # মিনিমাম লাইন ভ্যালিডেশন চেক করবে
)