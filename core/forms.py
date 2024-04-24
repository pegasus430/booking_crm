from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.urls import reverse_lazy
from core.models import User, Worker, Client, Event, Invoice, EventStatus, Settings, ChatRoom, Skill, Category
from django.forms.widgets import Select
#from ukpostcodeutils import validation

#Form Layout from Crispy Forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = User
        fields = ('username',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username',)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name', 'password1', 'password2']

class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        exclude = ('active','events','message_confirmation', 'documents')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        exclude = ('documents',)

class CustomSelectWidget(forms.Select):
    def __init__(self, *args, **kwargs):
        self.add_url = kwargs.pop('add_url', None)
        self.change_url = kwargs.pop('change_url', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        if self.add_url:
            add_link = f'<a href="{self.add_url}" class="btn btn-secondary" target="_blank">Add new client</a>'
            output += add_link
            output += """
                <script>
                // Listen for message from the AddClientForm window with the ID of the newly created client
                window.addEventListener('message', event => {
                    if (event.origin !== window.location.origin) return;
                    const clientId = event.data.clientId;
                    const select = document.querySelector('#id_client');
                    const option = select.querySelector(`[value="${clientId}"]`);
                    if (option) {
                        select.value = clientId;
                    } else {
                        // If the option is not in the select (e.g. the user selected a different client
                        // while the AddClientForm was open), reload the page to update the select
                        location.reload();
                    }
                });
                </script>
            """
        return output

class CustomStatusSelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_custom_status = True

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option["attrs"]["data-custom-status"] = option["value"] == ""  # Mark the option as custom status if value is empty string
        return option
    
class EventForm(forms.ModelForm):
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter Title'}))
    client = forms.ModelChoiceField(queryset=Client.objects.all(), widget=CustomSelectWidget(add_url=reverse_lazy('add_client')))
    address = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    town = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
	#county = forms.CharField(max_length=100, required=True, widget = forms.HiddenInput())
    post_code = forms.CharField(max_length=8, required=False, widget = forms.HiddenInput())
	#country = forms.CharField(max_length=40, required=True, widget = forms.HiddenInput())
    
    class Meta:
        model = Event
        exclude = ('job_number', 'job_title', )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            "start_time":forms.TimeInput(attrs={'type': 'time'}),
            
            
        }

    def __init__(self, *args, **kwargs):
        self.new_client = kwargs.pop('new_client', False)
        self.client_instance = kwargs.pop('client_instance', None)
        super().__init__(*args, **kwargs)

        # If a new client was added, pre-populate the client field
        if self.new_client and self.client_instance:
            self.fields['client'].initial = self.client_instance

        

class InvoiceForm(forms.ModelForm):
    THE_OPTIONS = [
    ('7 days', '7 days'),
    ('14 days', '14 days'),
    ('30 days', '30 days'),
    ]
    STATUS_OPTIONS = [
    ('CURRENT', 'CURRENT'),
    ('OVERDUE', 'OVERDUE'),
    ('PAID', 'PAID'),
    ]
    
    
    invoice_number = forms.CharField(
                    required = True,
                    label='Invoice number',
                    widget=forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Enter Invoice Number'}),)
    po_number = forms.CharField(
                    required = False,
                    label='PO number',
                    widget=forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Enter PO Number'}),)
    paymentTerms = forms.ChoiceField(
                    choices = THE_OPTIONS,
                    required = True,
                    label='Select Payment Terms',
                    widget=forms.Select(attrs={'class': 'form-control mb-3'}),)
    status = forms.ChoiceField(
                    choices = STATUS_OPTIONS,
                    required = True,
                    label='Change Invoice Status',
                    widget=forms.Select(attrs={'class': 'form-control mb-3'}),)
    
    dueDate = forms.DateField(
                        required = False,
                        label='Invoice Due',
                        widget=forms.DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}),)
    
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                # Add additional attributes to the fields if needed
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-6'),
                Column('dueDate', css_class='form-group col-md-6'),
                css_class='form-row'),
            Row(
                Column('paymentTerms', css_class='form-group col-md-6'),
                Column('status', css_class='form-group col-md-6'),
                css_class='form-row'),
            

            Submit('submit', ' EDIT INVOICE '))
        

    class Meta:
        model = Invoice
        fields = ['client', 'invoice_number', 'po_number', 'dueDate', 'paymentTerms', 'status']

        

class SelectEventsForm(forms.Form):
    selected_events = forms.ModelMultipleChoiceField(
        queryset=Event.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    def label_from_instance(self, obj):
        # Customize the display of events in the form
        # Here, we're displaying events by title and job number
        return f"{obj.title} - {obj.job_number}"

class SelectClientsForm(forms.Form):
    selected_client = forms.ModelChoiceField(queryset=Client.objects.all())
    class Meta:
        model = Invoice
        fields = ['client']

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = '__all__'  # Include all fields from the Settings model


class CreateChatRoomForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = ChatRoom
        fields = ['name', 'participants']

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'price_value', 'supplement_value']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'size': '50'}),  # Example size value
            'price_value': forms.NumberInput(attrs={'class': 'form-control', 'size': '10'}),
            'supplement_value': forms.NumberInput(attrs={'class': 'form-control', 'size': '10'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'size': '50'}),
        }
     