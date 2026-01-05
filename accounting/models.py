from django.db import models
from django.db.models import Sum

# -------------------------------------------
# 1. Chart of Accounts Model
# -------------------------------------------
class Account(models.Model):
    ACCOUNT_TYPES = (
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Revenue', 'Revenue'),
        ('Expense', 'Expense'),
        ('Other', 'Other')
    )
    
    name = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)

    def __str__(self):
        return self.name

    def get_balance(self, filter_date=None):
        
        tx_filter = {'journal__status': 'Posted'}
        
      
        if filter_date:
            tx_filter['journal__date__lte'] = filter_date

        
        debit_sum = self.transaction_set.filter(**tx_filter).aggregate(Sum('debit'))['debit__sum'] or 0
        credit_sum = self.transaction_set.filter(**tx_filter).aggregate(Sum('credit'))['credit__sum'] or 0
        
      
        if self.account_type in ['Asset', 'Expense']:
            return debit_sum - credit_sum
        else:
            return credit_sum - debit_sum


# -------------------------------------------
# 2. Journal Entry Header Model
# -------------------------------------------
class Journal(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Posted', 'Posted'),
    ]
    
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Posted')

    def __str__(self):
        return f"Journal #{self.id} - {self.date}"

    def get_total_amount(self):
        return self.transactions.aggregate(total=models.Sum('debit'))['total'] or 0


# -------------------------------------------
# 3. Transaction Line Model
# -------------------------------------------
class Transaction(models.Model):
    journal = models.ForeignKey(Journal, related_name='transactions', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.account.name} - Dr:{self.debit} Cr:{self.credit}"


# -------------------------------------------
# 4. Company Settings (Branding)
# -------------------------------------------
class CompanySettings(models.Model):
    company_name = models.CharField(max_length=100, default="AccuFlow ERP")
    tagline = models.CharField(max_length=150, default="Web-Based Professional Accounting System", blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, default="৳") 
    
    class Meta:
        verbose_name = "Company Settings"
        verbose_name_plural = "Company Settings"

    def __str__(self):
        return self.company_name