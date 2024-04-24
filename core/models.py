from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from decimal import Decimal

phone_regex = RegexValidator(
        regex=r'^\+?\d{12}$',
        message='Phone number must be 12 digits with an optional "+" sign and without any spaces or special characters.')

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)
    price_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supplement_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name
    
class EventStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=10)  # Store the color as a string (e.g., "#FF0000")

    def __str__(self):
        return self.name

class Document(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    
class Client(models.Model):
    company_name = models.CharField(max_length=100)
    primary_email = models.EmailField(max_length=100, null=True, blank=True)
    secondary_email = models.EmailField(max_length=100, default='', null=True, blank=True)
    accounts_email = models.EmailField(max_length=100, default='', null=True, blank=True)
    phone = models.CharField(max_length=15,null=True, blank=True, validators=[phone_regex])
    address = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=10, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    company_registration_nr = models.CharField(max_length=50, default='', blank=True)
    vat = models.CharField(max_length=15, default='', blank=True)
    bank_account = models.CharField(max_length=20, null=True, blank=True)
    sort_code = models.CharField(max_length=20, null=True, blank=True)
    name_on_bank_account = models.CharField(max_length=100, null=True, blank=True)
    documents = models.ManyToManyField(Document, blank=True)
       
    def __str__(self):
	     return(f"{self.company_name}") 

class Event(models.Model):
    title = models.CharField(max_length=120)
    job_number = models.CharField(max_length=120, default="")
    job_title = models.CharField(max_length=120, default="")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True, default=None)
    start_time = models.TimeField(null=False, blank=True, default=None)
    duration = models.IntegerField(default=2)
    location = models.CharField(max_length=120, blank=True, null=True, default='')
    town = models.CharField(max_length=120, blank=True, null=True, default='')
    address = models.CharField(max_length=120, blank=True, null=True, default='')
    postcode = models.CharField(max_length=120, blank=True, null=True, default='')
    skills_needed = models.ManyToManyField(Skill, blank=True)
    categories_needed = models.ManyToManyField(Category, blank=True)
    workers = models.ManyToManyField('Worker', related_name='events_workers', blank=True)
    nr_of_crew = models.IntegerField(default=1)
    site_contact = models.CharField(max_length=120, default='', null=True, blank=True)
    notes = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.ForeignKey(EventStatus, on_delete=models.SET_NULL, null=True, blank=True)
    cc_required = models.IntegerField(default=0, null=True)
    cc_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00, null=True)
    travel_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00, null=True)
    extra_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00, null=True)
    fuel_surcharge = models.DecimalField(decimal_places=2, max_digits=5, default=0.00, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.job_number}"
    
    @property
    def event_cost(self):
        # Check if the crew count is valid in the crew_rates dictionary
        if self.nr_of_crew not in Invoice.crew_rates:
            raise ValueError("Invalid number of crew members")

        # Check if the duration is valid in the crew_rates dictionary for the given crew count
        if self.duration not in Invoice.crew_rates[self.nr_of_crew]:
            raise ValueError("Invalid event duration")

        # Calculate the crew rate based on crew count and duration
        crew_rate = Invoice.crew_rates[self.nr_of_crew][self.duration]

        # Calculate the total for supplements based on crew count
        extra_supplement_total = self.extra_supplement * self.nr_of_crew
        cc_supplement_total = self.cc_supplement * self.cc_required  # Replace 'nr_of_cc_required' with the appropriate field for the number of cc required for the event
        travel_supplement_total = self.travel_supplement * self.nr_of_crew

        # Calculate the extras sum
        extras_sum = extra_supplement_total + cc_supplement_total + travel_supplement_total + self.fuel_surcharge

        # Calculate the total cost of the event
        total_cost = crew_rate + extras_sum

        # Save the extras sum to the field in the model
        self.extras_sum = extras_sum
        self.save()

        return total_cost

class Worker(models.Model):
    TITLE_CHOICES = [
        ('Mr', 'Mr.'),
        ('Mrs', 'Mrs.'),
        ('Miss', 'Miss.'),
    ]
    profile_picture = models.ImageField(null=True, blank=True, upload_to="profiles/")
    active = models.BooleanField(default=True)
    title = models.CharField(choices=TITLE_CHOICES, max_length=5, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15,null=True,validators=[phone_regex])
    address = models.CharField(max_length=100, null=True, blank=True)
    postcode = models.CharField(max_length=10, null=True, blank=True)
    next_of_kin = models.CharField(max_length=100, null=True, blank=True)
    nin = models.CharField(max_length=20, null=True, blank=True)
    utr = models.CharField(max_length=20, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    hourly_rate = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    bank_account = models.CharField(max_length=20, null=True, blank=True)
    sort_code = models.CharField(max_length=20, null=True, blank=True)
    name_on_bank_account = models.CharField(max_length=100, null=True, blank=True)
    #timesheet = models.ManyToManyField(Timesheet, blank=True)
    events = models.ManyToManyField(Event, related_name='worker_events', blank=True)
    message_confirmation = models.CharField(max_length=10, default="None")
    categories = models.ManyToManyField(Category, blank=True)
    documents = models.ManyToManyField(Document, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Sms(models.Model):
    sender = models.CharField(max_length=20)
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)
    # recipient = models.CharField(max_length=20)
    msg_type = models.CharField(max_length=10, choices=[("sent","Sent"),("received","Received")])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.worker:
            return "{}-{}".format(self.msg_type, self.worker.first_name)
        else:
            return "{}-{}".format(self.msg_type, "Unknown Worker")

class Timesheet(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    title = models.CharField(null=False, max_length=100, default='')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    job_date = models.DateField(null=False, blank=True, default=None)
    start_time = models.TimeField(null=False, blank=True, default=None)
    quoted_hours = models.IntegerField()
    worked_hours = models.IntegerField(null=True)
    cc_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    travel_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    extra_supplement = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    #total_for_job = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    totals = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    total_pay = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    paid = models.BooleanField(default=False)

    @property
    def total_for_job(self):
        if self.worked_hours <= 2:
            return 35 + self.extra_supplement + self.cc_supplement + self.travel_supplement
        elif self.worked_hours== 3:
           return 35 + (self.worked_hours- 2) * self.worker.hourly_rate + self.extra_supplement + self.cc_supplement + self.travel_supplement
        else:
            return self.worked_hours * self.worker.hourly_rate + self.extra_supplement + self.cc_supplement + self.travel_supplement

    def get_absolute_url(self):
        return reverse('timesheet_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.worker} - {self.event} - {self.job_date} - {self.start_time}"
    
class Invoice(models.Model):
    TERMS = [
    ('7 days', '7 days'),
    ('14 days', '14 days'),
    ('30 days', '30 days'),
    ('60 days', '60 days'),
    
    ]

    STATUS = [
    ('CURRENT', 'CURRENT'),
    ('EMAIL_SENT', 'EMAIL_SENT'),
    ('OVERDUE', 'OVERDUE'),
    ('PAID', 'PAID'),
    ]

    event = models.ManyToManyField(Event, blank=True)
    client = models.ForeignKey(Client, blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateField(auto_now_add=True)
    dueDate = models.DateField(null=True, blank=True)
    paymentTerms = models.CharField(choices=TERMS, default='14 days', max_length=100)
    status = models.CharField(choices=STATUS, default='CURRENT', max_length=100)
    invoice_number = models.CharField(max_length=255)
    po_number = models.CharField(max_length=25, default='', null=True, blank=True)
    vat = models.DecimalField(max_digits=6, decimal_places=2, default=None, null=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True)
    sent_date = models.DateField(blank=True, null=True)
    paid_invoice = models.BooleanField(default=False)
    

    crew_rates = {
        1: {2: 65, 3: 79, 4: 90, 5: 112, 6: 134, 7: 156, 8:178, 9:200, 10: 222},
        2: {2: 130, 3: 158, 4: 180, 5: 224, 6: 268, 7: 312, 8: 356, 9: 400, 10: 444},
        3: {2: 195, 3: 237, 4: 270, 5: 336, 6: 402, 7: 468, 8: 534, 9: 600, 10: 666},
        4: {2: 275, 3: 331, 4: 380, 5: 473, 6: 566, 7: 659, 8: 752, 9: 845, 10: 938},
        5: {2: 340, 3: 410, 4: 470, 5: 585, 6: 700, 7: 815, 8: 930, 9: 1045, 10: 1160},
        6: {2: 405, 3: 489, 4: 560, 5: 697, 6: 834, 7: 971, 8: 1108, 9: 1245, 10: 1382},
        7: {2: 470, 3: 568, 4: 650, 5: 809, 6: 968, 7: 1127, 8: 1286, 9: 1445, 10: 1604},
        8: {2: 535, 3: 647, 4: 740, 5: 921, 6: 1102, 7: 1282, 8: 1464, 9: 1645, 10: 1826},
        9: {2: 600, 3: 726, 4: 830, 5: 1033, 6: 1236, 7: 1439, 8: 1642, 9: 1845, 10: 2048},
        10: {2: 665, 3: 805, 4: 920, 5: 1145, 6: 1370, 7: 1595, 8: 1820, 9: 2045, 10: 2270},        
        # and so on...
    }

class Settings(models.Model):
    name = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(null=True, blank=True, upload_to="logos/")
    address = models.CharField(max_length=200, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    primary_email = models.EmailField(max_length=100, blank=True)
    secondary_email = models.EmailField(max_length=100, blank=True)
    accounts_email = models.EmailField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    company_reg_number = models.CharField(max_length=50, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)
    bank_account = models.CharField(max_length=20, null=True, blank=True)
    sort_code = models.CharField(max_length=20, null=True, blank=True)
    name_on_bank_account = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name or 'Settings'   
    
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender}: {self.content}'
    
class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    
    
    
