from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib import messages
import calendar
import json
import csv
import telnyx
from django.conf import settings
from django.views.generic import ListView
from django.db.models import Max
from datetime import date, datetime, timedelta
import datetime as dt
from io import BytesIO
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from calendar import HTMLCalendar
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import Event, Worker, Client, Document, Sms, Timesheet, Skill, Category, Invoice, Settings, EventStatus, ChatMessage
from core.forms import WorkerForm, ClientForm, EventForm, InvoiceForm, SelectEventsForm, SelectClientsForm, SettingsForm, CreateChatRoomForm, SkillForm, CategoryForm
from django.db.models import Q
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from re import search, sub
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal
import re
import random
from django.template.loader import get_template
from django.core.mail import EmailMessage
import logging
#from ukpostcodeutils import validation
import requests
from django.db.models import Count







telnyx.api_key = settings.TELNYX_API_KEY


class IndexView(LoginRequiredMixin, View):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        year = request.GET.get("year")
        month_number = request.GET.get("month")
        if not year and not month_number:
            year=datetime.now().year
            month=datetime.now().strftime('%B')
            month = month.capitalize()
            month_number = list(calendar.month_name).index(month)
            month_number = int(month_number)
        else:
            year =  int(year)
            month_number= int(month_number)
        
        now = datetime.now()
        if year != now.year or month_number != now.month:
            today = ""
        else:
            today = now.day
            
        weeks = calendar.monthcalendar(year, month_number)
        month_name = calendar.month_name[month_number]
        
        # Retrieve invoices in "current" or "overdue" status
        invoices = Invoice.objects.filter(paid_invoice=False)
        # Calculate the total amount for these invoices
        

        # Calculate the sum of grand_total for these invoices
        unpaid_invoices = Decimal('0.00')
        for invoice in invoices:
            events = invoice.event.all()
            event_total_costs = [event.event_cost for event in events]
            total_cost_of_events = sum(event_total_costs)
            vat = Decimal('0.20') * total_cost_of_events
            grand_total = total_cost_of_events + vat

            unpaid_invoices += grand_total
           

        events = Event.objects.filter(date__year=year, date__month=month_number)
        form = EventForm()

        today = dt.datetime.now().date()
        last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
        last_sunday = last_monday + dt.timedelta(days=6)

        # Get the total pay for all timesheets for the given date range
        unpaid_timesheets = 0
        sheets = Timesheet.objects.filter(
            job_date__range=[last_monday, last_sunday]
        ).values(
            "worker",
            "worker__first_name",
            "worker__last_name"
        ).annotate(dcount=Count('worker')).order_by()
        for sheet in sheets:
            worker_id = sheet['worker']
            ctx = get_timesheet_details(worker_id)
            unpaid_timesheets += ctx['total_pay']

        
        prev_month = month_number - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        # Get the next month and year
        next_month = month_number + 1
        next_year = year
        if next_month == 13:
            next_month = 1
            next_year += 1

        # Get the selected day from the request (assuming it's passed as a query parameter)
        selected_day = request.GET.get("day")
        
        # Define events_of_day with an empty queryset
        events_of_day = Event.objects.none()

        if selected_day:
            # Convert the selected_day to an integer
            selected_day = int(selected_day)
           
            # Filter events for the selected day
            events_of_day = events.filter(date__day=selected_day)

            
        ctx={
            "weeks":weeks,
            "month_name":month_name,
            "month_number":month_number,
            "year":year,
            "today":today,
            "events":events,
            "form":form,
            "prev_year":prev_year,
            "next_year":next_year,
            "prev_month":prev_month,
            "next_month":next_month,
            "unpaid_invoices": unpaid_invoices,
            "events_of_day": events_of_day,
            "unpaid_timesheets":unpaid_timesheets,
            #"today_events": today_events
            }
        return render(request, self.template_name, ctx)
    
    def post(self, request, *args, **kwargs):
        pass

###################################################################
#
#                       Worker Views
#
###################################################################

class WorkerListView(LoginRequiredMixin, View):
    template_name = "worker_list.html"

    def get(self, request, *args, **kwargs):
        workers = Worker.objects.all().order_by('-active')
        skills = Skill.objects.all()
        categories = Category.objects.all()
        #print(skills)
        return render(request, self.template_name, {"workers":workers, "skills":skills, "categories":categories})
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        cat = request.POST.get("cat")
        skill = request.POST.get("skill")
        kwargs={}
        if skill:
            skill = get_object_or_404(Skill, name=skill)
            kwargs["skills"]=skill
        if cat:
            cat = get_object_or_404(Category, name=cat)
            kwargs["categories"]=cat
        

        workers = Worker.objects.filter(**kwargs).filter(
                Q(first_name__icontains=name) | Q(last_name__icontains=name))
        skills = Skill.objects.all()
        categories = Category.objects.all()
        return render(request, self.template_name, {"workers":workers, "skills":skills, "categories":categories})

class WorkerDetailView(LoginRequiredMixin, View):
    template_name = "worker_detail.html"

    def get(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)

        # Get the current date
        today = date.today()
        last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)

        # Calculate the start and end dates of the week
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Filter the events for the current worker by the date range
        assigned_events = worker.events.filter(date__range=[start_of_week, end_of_week])
        
        # Retrieve the timesheet history for the worker
        timesheet_title = f"{worker.first_name} {worker.last_name} - Week of {last_monday}"
        sheets = Timesheet.objects.filter(worker=worker

            ).values(
                "worker",
                "worker__first_name",
                "worker__last_name"
                ).annotate(dcount=Count('worker')).order_by()
        for sheet in sheets:
            worker_id = sheet['worker']
            ctx = get_timesheet_details(worker_id)
            sheet['total_pay'] = ctx['total_pay']

        return render(request, self.template_name, {"worker":worker, "assigned_events": assigned_events, "timesheets": sheets, "timesheet_title":timesheet_title})
    
def toggle_worker_status(request, id):
    worker = get_object_or_404(Worker, pk=id)
    worker.active = not worker.active  # Toggle the active/inactive status
    worker.save()
    return redirect("worker_detail", worker_id=id)

    
class AddWorkerView(LoginRequiredMixin, View):
    template_name = "add_worker.html"

    def get(self, request, *args, **kwargs):
        form = WorkerForm()
        return render(request, self.template_name, {"form":form})
    
    def post(self, request, *args, **kwargs):
        form = WorkerForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        return redirect("worker_list")
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST' and request.FILES.get('csv_file'):
            return self.upload_workers(request)
        return super().dispatch(request, *args, **kwargs)

    def upload_workers(self, request):
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
            else:
                # Read the CSV file
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')
                # Skip the header row
                next(csv_data)
                workers_uploaded = 0
                validation_errors = []
            for row in csv_data:
                try:
                    worker = Worker.objects.create(
                        first_name=row[0],
                        last_name=row[1],
                        phone=row[2],
                        email=row[3],
                        hourly_rate=row[4],
                        #date_of_birth=row[5],
                        nin=row[6],
                        utr=row[7],
                        name_on_bank_account=row[8],
                        bank_account=row[9],
                        sort_code=row[10],
                        address=row[11],
                        postcode=row[12],
                        # Add more fields as needed
                    )
                    worker.save()
                    workers_uploaded += 1
                except ValidationError as e:
                    error_message = str(e)
                    if '“” value must be a decimal number' not in error_message:
                        validation_errors.append(error_message)

            if workers_uploaded > 0:
                messages.success(request, f'{workers_uploaded} worker(s) uploaded successfully.')
            if validation_errors:
                messages.warning(request, 'Validation errors: {}'.format('. '.join(validation_errors)))

        return render(request, 'worker_list.html')
    
    

class EditWorkerView(LoginRequiredMixin, View):
    template_name = "edit_worker.html"

    def get(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)
        form = WorkerForm(instance=worker)
        return render(request, self.template_name, {"form":form, "worker":worker})
    
    def post(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)
        form = WorkerForm(request.POST,request.FILES, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, "Worker information updated successfully.")
            return redirect("worker_detail", worker_id=worker.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in field '{field}': {error}")
            return render(
                request,
                self.template_name,
                {"form": form, "worker": worker}
            )

class DeleteWorkerView(LoginRequiredMixin, View):
    template_name = "delete.html"

    def get(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)
        ctx={
            "model":"Worker",
            "name":"{} {}".format(worker.first_name, worker.last_name),
            "obj":worker
            }
        return render(request, self.template_name, ctx)
    
    def post(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        get_object_or_404(Worker, pk=worker_id).delete()
        return redirect("worker_list")

class AddWorkerDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        doc = request.FILES.get("document")
        worker_id = request.POST.get("worker_id")

        doc = Document(file=doc)
        doc.save()
        worker = get_object_or_404(Worker, pk=worker_id)
        worker.documents.add(doc)
        return redirect("worker_detail", worker_id=worker_id)

class DeleteWorkerDocumentView(LoginRequiredMixin, View):
    # template_name = "delete.html"

    def get(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        document_id = self.kwargs.get("document_id")
        get_object_or_404(Document, pk=document_id).delete()
        return redirect("worker_detail", worker_id=worker_id)

###################################################################
#
#                       Client Views
#
###################################################################

class ClientListView(LoginRequiredMixin, View):
    template_name = "client_list.html"

    def get(self, request, *args, **kwargs):
        clients = Client.objects.all()
        return render(request, self.template_name, {"clients":clients})

class ClientDetailView(LoginRequiredMixin, View):
    template_name = "client_detail.html"

    def get(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        client = get_object_or_404(Client, pk=client_id)

        return render(request, self.template_name, {"client":client})

class AddClientView(LoginRequiredMixin, View):
    template_name = "add_client.html"

    def get(self, request, *args, **kwargs):
        form = ClientForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            add_event_url = reverse('add_event') + f"?client={client.id}"
            return redirect(add_event_url)

        return redirect("client_list")

class EditClientView(LoginRequiredMixin, View):
    template_name = "edit_client.html"

    def get(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        client = get_object_or_404(Client, pk=client_id)
        form = ClientForm(instance=client)
        return render(request, self.template_name, {"form": form, "client": client})
    
    def post(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        client = get_object_or_404(Client, pk=client_id)
        form = ClientForm(request.POST, instance=client)

        if form.is_valid():
            form.save()
            return redirect("client_detail", client_id=client.id)
        else:
            print(form.errors)
            return render(request, self.template_name, {"form": form, "client": client})


class DeleteClientView(LoginRequiredMixin, View):
    template_name = "delete.html"

    def get(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        client = get_object_or_404(Client, pk=client_id)
        ctx={
            "model":"Client",
            "name":"{}".format(client.company_name),
            "obj":client
            }
        return render(request, self.template_name, ctx)
    
    def post(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        get_object_or_404(Client, pk=client_id).delete()
        return redirect("client_list")

class AddClientDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        doc = request.FILES.get("document")
        client_id = request.POST.get("client_id")

        doc = Document(file=doc)
        doc.save()
        client = get_object_or_404(Client, pk=client_id)
        client.documents.add(doc)
        return redirect("client_detail", client_id=client_id)

class DeleteClientDocumentView(LoginRequiredMixin, View):
    # template_name = "delete.html"

    def get(self, request, *args, **kwargs):
        client_id = self.kwargs.get("client_id")
        document_id = self.kwargs.get("document_id")
        get_object_or_404(Document, pk=document_id).delete()
        return redirect("client_detail", client_id=client_id)
###################################################################
#
#                       Event Views
#
###################################################################

class EventListView(LoginRequiredMixin, View):
    template_name = "event_list.html"

    def get(self, request, *args, **kwargs):
        events = Event.objects.all()
        return render(request, self.template_name, {"events":events})

class EventDetailView(LoginRequiredMixin, View):
    template_name = "event_detail.html"

    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        sms_workers = Worker.objects.filter(active=True, message_confirmation="sent,{}".format(event.id))
        lst = list(event.workers.all().values_list("id"))
        if len(lst)>0:
            workers = Worker.objects.all().exclude(id__in=lst[0])
        else:
            workers = Worker.objects.all()
        return render(request, self.template_name, {"event":event, "workers":workers, "sms_workers":sms_workers})

description = """Can you do? {title}\n
{date}\n
Start time: {start}\n
Hours: {duration}\n
Crew : {crew}\n
Client: {client}\n
Location: {location}\n
Contact: {contact}\n
Note: {notes}\n
"""

class AddEventView(LoginRequiredMixin, View):
    template_name = "add_event.html"

    def get(self, request, *args, **kwargs):
        form = EventForm()
        return render(request, self.template_name, {"form":form})
    
    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
      
        if form.is_valid():
            event = form.save(commit=False)
            
            if not event.job_number:
                max_count = Event.objects.aggregate(max_count=Max('job_number'))
                count = 1
                if max_count['max_count']:
                    last_job_number = max_count['max_count']
                    last_number = int(last_job_number.split('-')[0].split()[-1])
                    if last_number >= 9999:
                        count = 1
                    else:
                        count = last_number + 1
                event.job_number = f"{count:04d}-1"

            if not event.description:
                event.description = description.format(
                    title=event.job_number,
                    date=event.date,
                    start=event.start_time,
                    duration=event.duration,
                    crew=event.nr_of_crew,
                    client=event.client,
                    location=event.location,
                    contact="TBC",
                    notes=event.notes
                )
            event.save()
        else:
            print(form.errors)
        return redirect(request.META.get('HTTP_REFERER'))
    

class EditEventView(LoginRequiredMixin, View):
    template_name = "edit_event.html"

    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        form = EventForm(instance=event)
        return render(request, self.template_name, {"form": form, "event": event})

    def post(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        form = EventForm(request.POST, instance=event)

        # Get the selected worker IDs from the form data
        selected_worker_ids = request.POST.getlist("workers")

        # Check if the number of selected workers is greater than or equal to the crew limit
        if len(selected_worker_ids) > event.nr_of_crew:
            messages.error(request, "This job is already complete. No more workers can be added.")
            return redirect('event_detail', event_id=event.id)

        # Check for conflicting events for each selected worker
        conflicting_workers = Worker.objects.filter(
            events__date=event.date,
            events__start_time=event.start_time,
            id__in=selected_worker_ids,
        ).exclude(events=event)

        if form.is_valid() and not conflicting_workers:
            form.save()

            # Assign the event to each selected worker
            for worker_id in selected_worker_ids:
                worker = get_object_or_404(Worker, pk=worker_id)
                worker.events.add(event)

            return redirect("event_detail", event_id=event.id)
        else:
            if conflicting_workers:
                # Handle the case where there are workers already assigned to other events at the same time
                messages.warning(request, "The following workers are already assigned to other events at the same time:")
                for worker in conflicting_workers:
                    conflicting_event = worker.events.filter(date=event.date, start_time=event.start_time).first()
                    messages.warning(request, f"{worker.first_name} {worker.last_name} is assigned to {conflicting_event.title}.")

            print(form.errors)

        return redirect("event_detail", event_id=event.id)


class DeleteEventView(LoginRequiredMixin, View):
    template_name = "delete.html"

    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        ctx={
            "model":"Event",
            "name":"{} - {}".format(event.title, event.job_number),
            "obj":event
            }
        return render(request, self.template_name, ctx)
    
    def post(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        get_object_or_404(Event, pk=event_id).delete()
        return redirect("index")

class RemoveWorkerFromEvent(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        worker_id = self.kwargs.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)
        event = get_object_or_404(Event, pk=event_id)
        event.workers.remove(worker)
        worker.events.remove(event)
        return redirect("event_detail", event_id=event_id)

class AssignWorker(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        selected_worker_ids = request.POST.getlist('workers')
        sms = request.POST.get("sms")
        selected_workers = Worker.objects.filter(id__in=selected_worker_ids)
        event_id = request.POST.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        
        for worker in selected_workers:
            if worker.phone:
                text=f"{sms} Reply with {event.title} Yes or {event.title} No"
                telnyx.Message.create(
                    from_="+447537188201",
                    to=worker.phone,
                    text=f"{event.description} Reply with {event.job_number} Yes or {event.job_number} No"
                )

                sms = Sms.objects.create(
                    sender="+447537188201",
                    worker=worker,
                    msg_type="sent",
                    content=text
                )
                worker.message_confirmation = "sent,{}".format(event.id)
                worker.save()

                worker.events.add(event)

        return redirect("event_detail", event_id=event_id)
    
class DuplicateEventView(LoginRequiredMixin, View):
    template_name = "duplicate_event.html"

    def get(self, request, pk):
        original_event = Event.objects.get(pk=pk)
        

        # Extract the event count from the original job number
        match = search(r"\d+-\d+$", original_event.job_number)
        event_count = 1  # Default event count if not found

        if match:
            event_count_str = match.group()
            event_count = int(event_count_str.split('-')[1])

        # Increment the event count and update the job number for the new event
        new_event_count = event_count + 1
        new_job_number = sub(r"\d+-\d+$", f"{event_count_str.split('-')[0]}-{new_event_count}", original_event.job_number)

        new_event = Event.objects.create(
            job_number=new_job_number,
            title=original_event.title,
            date=original_event.date,
            start_time=original_event.start_time,
            duration=original_event.duration,
            location=original_event.location,
            client=original_event.client,
            nr_of_crew=original_event.nr_of_crew,
            site_contact=original_event.site_contact,
            notes=original_event.notes,
            description=original_event.description,
            extra_supplement=original_event.extra_supplement,
            cc_supplement=original_event.cc_supplement,
            travel_supplement=original_event.travel_supplement,
            # Add other fields as needed
        )

        new_event.skills_needed.set(original_event.skills_needed.all())
        new_event.categories_needed.set(original_event.categories_needed.all())

        # Optionally, update any other fields of the new event as desired

        # Redirect to the edit view of the newly created event after duplication
        return redirect("edit_event", event_id=new_event.pk)

def get_addresses(request):
    if request.method == 'GET':
        postcode = request.GET.get('postcode')
                
        # Make a request to the Google Geocoding API
        google_api_key = 'AIzaSyAvPU31yECwIIMNsiv8YKZiZB9WGWFLQE4'
        response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={postcode}&key={google_api_key}')
        data = response.json()
        print("Google API response:", data)  # Add this line for debugging
        addresses = []
        if data['status'] == 'OK':
            for result in data['results']:
                addresses.append(result['formatted_address'])
        
        return JsonResponse({'addresses': addresses})



###################################################################
#
#                       Timesheet Views
#
###################################################################

class TimesheetListView(LoginRequiredMixin, View):
    template_name = "timesheet_list.html"

    def get(self, request, *args, **kwargs):
        today = dt.datetime.now().date()
        last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
        last_sunday = last_monday + dt.timedelta(days=6)
        sheets = Timesheet.objects.filter(
            job_date__range=[last_monday, last_sunday]
            ).values(
                "worker",
                "worker__first_name",
                "worker__last_name"
                ).annotate(dcount=Count('worker')).order_by()
        for sheet in sheets:
            worker_id = sheet['worker']
            ctx = get_timesheet_details(worker_id)
            sheet['total_pay'] = ctx['total_pay']

        return render(request, self.template_name, {'timesheets': sheets})

def get_timesheet_byweek(request):
    if request.method == 'POST':
        str_last_monday = request.POST.get('last_monday')
        last_monday = dt.datetime.strptime(str_last_monday, "%Y-%m-%d")        
        str_last_sunday = request.POST.get('last_sunday')
        last_sunday = dt.datetime.strptime(str_last_sunday, "%Y-%m-%d")
        sheets = Timesheet.objects.filter(
            job_date__range=[last_monday, last_sunday]
            ).values(
                "worker",
                "worker__first_name",
                "worker__last_name"
                ).annotate(dcount=Count('worker')).order_by()
        for sheet in sheets:
            worker_id = sheet['worker']
            ctx = get_timesheet_details(worker_id)
            sheet['total_pay'] = ctx['total_pay']

        data = list(sheets)        
        return JsonResponse(data, safe=False)


def get_timesheet_details(worker_id):
    worker = get_object_or_404(Worker, id=worker_id)
    today = dt.datetime.now().date()
    last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    last_sunday = last_monday + dt.timedelta(days=6)

    timesheets = Timesheet.objects.filter(
        worker=worker,
        job_date__range=[last_monday, last_monday + dt.timedelta(days=6)])
    total_worked_hours = 0
    total_pay=0
    for sheet in timesheets:
        total_worked_hours += sheet.worked_hours
        total_pay += sheet.total_for_job

    ctx={
        "worker":worker,
        'timesheets': timesheets,
        "total_worked_hours":total_worked_hours,
        "total_pay":total_pay
    }
    return ctx

class TimesheetDetailView(LoginRequiredMixin, View):
    template_name = "timesheet_detail.html"

    def get(self, request, *args, **kwargs):
        worker_id = self.kwargs.get("worker_id")
        ctx = get_timesheet_details(worker_id)
        return render(request, self.template_name, ctx)

def download_timesheet_pdf(request, worker_id):
    ctx = get_timesheet_details(worker_id)
    worker = Worker.objects.get(id=worker_id)
    today = dt.datetime.now().date()        
    last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    last_sunday = last_monday + dt.timedelta(days=6)
    html_content = render_to_string('timesheet_pdf.html', ctx)
    # Create thePDF document
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)
    if pisa_status.err:
        return HttpResponse('Error converting HTML to PDF', status=500)
    # Rewind the buffer and create the HTTP response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"{worker.first_name} {worker.last_name} - Week of {last_monday}~{last_sunday}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

def download_csv(request, worker_id):
    ctx = get_timesheet_details(worker_id)
    worker = Worker.objects.get(id=worker_id)
    today = dt.datetime.now().date()        
    last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    last_sunday = last_monday + dt.timedelta(days=6)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{worker.first_name} {worker.last_name} - Week of {last_monday}~{last_sunday}.csv"'

    writer = csv.writer(response)
    # Write CSV headers
    writer.writerow(['Date', 'Time', 'Event', 'Client', 'Quoted Hours', 'Worked Hours', 'Extra Supplement', 'CC Supplement', 'Travel Supplement', 'Total for Event'])

    
    for sheet in ctx["timesheets"]:
        date = sheet.event.date.strftime('%Y-%m-%d') if sheet.event.date else ''  # Handle None values
        time = sheet.event.start_time.strftime('%H:%M') if sheet.event.start_time else ''  # Handle None values
        event_title = sheet.event.title if sheet.event.title else ''  # Handle None values
        client = sheet.event.client if sheet.event.client else ''  # Handle None values
        quoted_hours = sheet.event.duration if sheet.event.duration else ''  # Handle None values
        worked_hours = sheet.worked_hours
        extra_supplement = sheet.extra_supplement
        cc_supplement = sheet.cc_supplement
        travel_supplement = sheet.travel_supplement
        total_for_job = sheet.total_for_job

        writer.writerow([date, time, event_title, client, quoted_hours, worked_hours,extra_supplement,cc_supplement,travel_supplement,total_for_job])
        # writer.writerow([date, time])

    return response

def update_timesheet(request, timesheet_id):
    if request.method=="POST":
        worked_hours = request.POST.get("worked_hours")
        extra_supplement = request.POST.get("extra_supplement")
        cc_supplement = request.POST.get("cc_supplement")
        travel_supplement = request.POST.get("travel_supplement")
        hourly_rate = request.POST.get("hourly_rate")
        timesheet = get_object_or_404(Timesheet,id=timesheet_id)
        timesheet.worked_hours = worked_hours
        timesheet.extra_supplement = extra_supplement
        timesheet.cc_supplement = cc_supplement
        timesheet.travel_supplement = travel_supplement
        timesheet.save()
    
    return redirect("timesheet_detail", worker_id=timesheet.worker.id)

def update_timesheet_with_hourlyrate(request, worker_id):
    if request.method == 'POST':
        hourly_rate = request.POST.get('hourly_rate')
        worker = Worker.objects.get(id=worker_id)
        worker.hourly_rate = hourly_rate
        worker.save()
        timesheets = Timesheet.objects.filter(worker=worker)
        
        for timesheet in timesheets:
            timesheet.save()
        
    return redirect("timesheet_detail", worker_id=worker_id)

def delete_timesheet(request, worker_id):
    sheets = Timesheet.objects.filter(worker=worker_id).delete()
    return redirect("timesheet_list")

def create_timesheet(request, worker_id):
    # Get the worker object
    worker = Worker.objects.get(id=worker_id)
    
    # Get the current date
    today = dt.datetime.now().date()

    # Calculate the date range for the previous week (Monday to Sunday)
    last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    last_sunday = last_monday + dt.timedelta(days=6)

    # Retrieve the events for the previous week
    events = Event.objects.filter(date__range=[last_monday, last_sunday], workers=worker)
    timesheet_exists = Timesheet.objects.filter(worker=worker, job_date__range=[last_monday, last_monday + dt.timedelta(days=6)]).exists()
    
    if timesheet_exists:
        # A timesheet already exists, display a message to the user
        messages.error(request, 'A timesheet already exists for this week.')
        # Redirect to a specific URL or render a different template if needed
        return redirect('timesheet_list')  # Example redirect to timesheet_list URL
    elif not events:
        # No events found for the worker in the previous week, display a message
        messages.info(request, 'No jobs found for this worker in the previous week.')
        # Redirect to a specific URL or render a different template if needed
        return redirect('worker_list')  # Example redirect to worker_list URL
    else:
        # Get all events worked by the worker in the previous week (Mon-Sun)
        events = Event.objects.filter(date__range=[last_monday, last_monday + dt.timedelta(days=6)], workers=worker)
        timesheet_title = f"{worker.first_name} {worker.last_name} - Week of {last_monday}~{last_sunday}"
        for event in events:
            
            timesheet = Timesheet(
                title=timesheet_title,
                worker=worker,
                event=event,
                job_date=event.date,
                start_time=event.start_time,
                quoted_hours=event.duration,
                worked_hours=event.duration,
                cc_supplement=event.cc_supplement,
                travel_supplement=event.travel_supplement,
                extra_supplement=event.extra_supplement,
                #total_pay=total_pay,
            )
            timesheet.save()
            
    return redirect("timesheet_detail", worker_id=worker.id)

def auto_create_timesheet(request):
    # Get all workers 
    workers = Worker.objects.all()
    print(workers)
    # Get the current date
    today = dt.datetime.now().date()

    # Calculate the date range for the previous week (Monday to Sunday)
    last_monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    last_sunday = last_monday + dt.timedelta(days=6)

    for worker in workers:
        # Retrieve the events for the previous week
        events = Event.objects.filter(date__range=[last_monday, last_sunday], workers=worker)
        timesheet_exists = Timesheet.objects.filter(worker=worker, job_date__range=[last_monday, last_monday + dt.timedelta(days=6)]).exists()

        if not timesheet_exists and events:
            # Get all events worked by the worker in the previous week (Mon-Sun)
            events = Event.objects.filter(date__range=[last_monday, last_monday + dt.timedelta(days=6)], workers=worker)
            timesheet_title = f"{worker.first_name} {worker.last_name} - Week of {last_monday}~{last_sunday}"
            for event in events:
                
                timesheet = Timesheet(
                    title=timesheet_title,
                    worker=worker,
                    event=event,
                    job_date=event.date,
                    start_time=event.start_time,
                    quoted_hours=event.duration,
                    worked_hours=event.duration,
                    cc_supplement=event.cc_supplement,
                    travel_supplement=event.travel_supplement,
                    extra_supplement=event.extra_supplement,
                    #total_pay=total_pay,
                )
                timesheet.save()
    
    return redirect("timesheet_list")

def timesheet_history(request, worker_id):
    # Retrieve the worker object
    worker = Worker.objects.get(id=worker_id)
        
    # Retrieve all timesheets for the worker, sorted by date (most recent first)
    sheets = Timesheet.objects.filter(worker=worker).order_by()
    
    return render(request, 'timesheet_detail.html', {'worker': worker, 'timesheets': sheets})

def send_timesheet_email(request, worker_id):
    ctx = get_timesheet_details(worker_id)
    html_content = render_to_string('timesheet_pdf.html', ctx)
    # Fetch worker details based on the worker_id
    worker = get_object_or_404(Worker, id=worker_id)
    # Get the worker's primary email from the worker object
    worker_primary_email = worker.email

    # Create the PDF document
    buffer = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=buffer)

    if pdf.err:
        messages.error(request, 'Failed to generate PDF')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # Rewind the buffer and create the EmailMessage instance
    buffer.seek(0)
    pdf_filename = f'timesheet.pdf'
    email = EmailMessage(
        subject='Your Timesheet',
        body='Please find attached your timesheet.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[worker_primary_email],  # Set the recipient's email address here
        reply_to=[settings.DEFAULT_FROM_EMAIL]
    )
    email.attach(pdf_filename, buffer.read(), 'application/pdf')

    try:
        # Send the email
        email.send()
        messages.success(request, 'Email sent successfully')
    except:
        messages.error(request, 'Failed to send email')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

###################################################################
#
#                       Invoice Views
#
###################################################################
class InvoiceListView(LoginRequiredMixin, View):
    template_name = "invoice_list.html"  # Change this to your desired template name

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.all()
        today = date.today()

        # Calculate total cost and grand total for each invoice
        for invoice in invoices:
            events = invoice.event.all()
            event_total_costs = [event.event_cost for event in events]
            total_cost_of_events = sum(event_total_costs)
            vat = Decimal('0.20') * total_cost_of_events
            grand_total = total_cost_of_events + vat

            invoice.total_cost_of_events = total_cost_of_events
            invoice.grand_total = grand_total

            if invoice.paid_invoice:
                invoice.color = 'green'
            elif invoice.dueDate:
                dueDate = invoice.dueDate
                days_overdue = (dueDate - today).days
                if days_overdue >=30:
                    invoice.color = 'red'
                elif days_overdue >= 14:
                    invoice.color = 'orange'
                elif days_overdue >= 7:
                    invoice.color = 'yellow'
                else:
                    invoice.color = 'white'
            else:
                invoice.color = 'white'

        return render(request, self.template_name, {'invoices': invoices})


def createInvoice(request):
    # create a blank invoice
    new_invoice = Invoice.objects.create()
    new_invoice.save()

    return redirect('create-build-invoice', id=new_invoice.id)


def createBuildInvoice(request, id):
    try:
        invoice = get_object_or_404(Invoice, id=id)
    except:
        messages.error(request, 'Something went wrong')
        return redirect('invoice_list')

    events = Event.objects.all()

    context = {}
    context['invoice'] = invoice
    context['events'] = events

    if request.method == 'GET':
        inv_form = InvoiceForm(instance=invoice)
        select_events_form = SelectEventsForm()
        # Pass the client associated with the invoice to the form
        #select_clients_form = SelectClientsForm(initial={'client': invoice.client.id if invoice.client else None})

        context['select_events_form'] = select_events_form
        context['inv_form'] = inv_form
        #context['select_clients_form'] = select_clients_form
        return render(request, 'create_invoice.html', context)

    if request.method == 'POST':
        inv_form = InvoiceForm(request.POST, instance=invoice)
        select_events_form = SelectEventsForm(request.POST)
        #select_clients_form = SelectClientsForm(request.POST, initial={'client': invoice.client.id if invoice.client else None})

        if select_events_form.is_valid():
            selected_events = select_events_form.cleaned_data['selected_events']
            events_to_add = Event.objects.filter(id__in=selected_events)
            invoice.event.set(events_to_add)  # Use set() to update the many-to-many relationship

            messages.success(request, "Invoice events added successfully")
            return redirect('create-build-invoice', id=invoice.id)

        elif inv_form.is_valid() and 'paymentTerms' in request.POST:
            inv_form.save()

            messages.success(request, "Invoice updated successfully")
            return redirect('invoice_list')

        else:
            context['select_events_form'] = select_events_form
            context['inv_form'] = inv_form
            #context['select_clients_form'] = select_clients_form
            messages.error(request, "Problem processing your request")
            return render(request, 'create_invoice.html', context)

    return render(request, 'create_invoice.html', context)

def view_invoice(request, id):
    invoice = get_object_or_404(Invoice, id=id)
    events = invoice.event.all()
    

    # Calculate the total cost for each event and store it in a list
    event_total_costs = [event.event_cost for event in events]

    # Calculate the sum of total costs for all events
    total_cost_of_events = sum(event_total_costs)

    # Calculate the VAT (20% of the total cost of events)
    vat = Decimal('0.20') * total_cost_of_events

    # Calculate the grand total (total cost of events + VAT)
    grand_total = total_cost_of_events + vat

    try:
        company_settings = Settings.objects.first()
    except Settings.DoesNotExist:
        company_settings = None

    context = {
        'invoice': invoice,
        'events': events,
        'vat': vat,
        'grand_total': grand_total,
        'company_settings': company_settings,  # Include the fetched company settings in the context
        #'extras_sum': events.extras_sum,
        
    }

    return render(request, 'invoice_detail.html', context)

def download_invoice_pdf(request, id):
    invoice = get_object_or_404(Invoice, id=id)
    events = invoice.event.all()

    # Calculate the total cost for each event and store it in a list
    event_total_costs = [event.event_cost for event in events]

    # Calculate the sum of total costs for all events
    total_cost_of_events = sum(event_total_costs)

    # Calculate the VAT (20% of the total cost of events)
    vat = Decimal('0.20') * total_cost_of_events

    # Calculate the grand total (total cost of events + VAT)
    grand_total = total_cost_of_events + vat

    try:
        company_settings = Settings.objects.first()
    except Settings.DoesNotExist:
        company_settings = None

    context = {
        'invoice': invoice,
        'events': events,
        'vat': vat,
        'grand_total': grand_total,
        'company_settings': company_settings,
    }

    # Render the new template for the PDF content
    html_content = render_to_string('invoice_pdf.html', context)

    # Create the PDF document
    buffer = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=buffer)

    if pdf.err:
        return HttpResponse('Error generating PDF', status=500)

    # Rewind the buffer and create the HTTP response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number} - {invoice.client.company_name}.pdf"'

    return response


@csrf_exempt
def toggle_invoice_status(request, invoice_id):
    if request.method == 'POST':
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            invoice.paid_invoice = not invoice.paid_invoice
            invoice.save()
            data = {'status': 'success', 'paid': invoice.paid_invoice}
            return JsonResponse(data)
        except Invoice.DoesNotExist:
            data = {'status': 'error', 'message': 'Invoice not found'}
            return JsonResponse(data, status=404)
    else:
        data = {'status': 'error', 'message': 'Invalid request method'}
        return JsonResponse(data, status=400)


def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.delete()
    # Redirect back to the invoice list page after deletion
    return redirect('invoice_list')

def generate_invoice_pdf_content(invoice, events, vat, grand_total, company_settings):
    context = {
        'invoice': invoice,
        'events': events,
        'vat': vat,
        'grand_total': grand_total,
        'company_settings': company_settings,
    }

    # Render the HTML content using the template
    html_content = render_to_string('invoice_pdf.html', context)

    # Create the PDF document
    buffer = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=buffer)

    if pdf.err:
        return None  # Return None on error
    else:
        return buffer.getvalue()  # Return the PDF content buffer

    
def send_invoice_email(request, invoice_id):
    # Get the invoice object
    invoice = get_object_or_404(Invoice, id=invoice_id)
    events = invoice.event.all()

    # Calculate the total cost for each event and store it in a list
    event_total_costs = [event.event_cost for event in events]

    # Calculate the sum of total costs for all events
    total_cost_of_events = sum(event_total_costs)

    # Calculate the VAT (20% of the total cost of events)
    vat = Decimal('0.20') * total_cost_of_events

    # Calculate the grand total (total cost of events + VAT)
    grand_total = total_cost_of_events + vat

    # Get the client's email from the invoice
    client_email = invoice.client.primary_email

    try:
        company_settings = Settings.objects.first()
    except Settings.DoesNotExist:
        company_settings = None

    context = {
        'invoice': invoice,
        'events': events,
        'vat': vat,
        'grand_total': grand_total,
        'company_settings': company_settings,
    }

    # Render the new template for the PDF content
    html_content = render_to_string('invoice_pdf.html', context)

    # Create the PDF document
    buffer = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=buffer)

    if pdf.err:
        messages.error(request, 'Failed to generate PDF')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # Rewind the buffer and create the EmailMessage instance
    buffer.seek(0)
    pdf_filename = f'{invoice.invoice_number}.pdf'
    email = EmailMessage(
        subject='Your Invoice',
        body='Please find attached your invoice.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_email],
        reply_to=[settings.DEFAULT_FROM_EMAIL]
    )
    email.attach(pdf_filename, buffer.read(), 'application/pdf')

    try:
        # Send the email
        email.send()
        messages.success(request, 'Email sent successfully')
    except:
        messages.error(request, 'Failed to send email')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))







###################################################################
#
#                       SMS Views
#
###################################################################

class SMSView(LoginRequiredMixin, View):
    template_name = "sms.html"

    def get(self, request, *args, **kwargs):
        active_sms_workers = Worker.objects.filter(
            sms__msg_type__in=['received', 'sent']
        ).distinct()
        all_workers = Worker.objects.all()

        # Assuming you have some way to listen for incoming messages
        if request.GET.get("received_sms_content") and request.GET.get("received_sms_sender"):
            # Receiving SMS from an unsaved number
            Sms.objects.create(
                sender=request.GET.get("received_sms_sender"),
                content=request.GET.get("received_sms_content"),
                msg_type='received'
            )

        return render(request, self.template_name, {"active_sms_workers": active_sms_workers, "all_workers": all_workers})
    
    def post(self, request, *args, **kwargs):
        worker_id = request.POST.get("worker_id")
        phone_number = request.POST.get("phone_number")
        sms_content = request.POST.get("sms_content")
        
        if worker_id:
            # Sending SMS to a saved worker
            worker = Worker.objects.get(pk=worker_id)
            # Logic to send SMS to the saved worker

        elif phone_number:
            # Sending SMS to a non-saved number
            # Logic to send SMS to the provided phone number

            return JsonResponse({"result": "SMS sent successfully"})



def send_sms(request):
    if request.method == "POST":
        sms = request.POST.get("sms")
        worker_id = request.POST.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)

        if sms == "event_description":
            event = Event.objects.get(...)  # Get the relevant event object
            message = f"{event.description} Reply with {event.title} Yes or {event.title} No"
        else:
            message = sms

        telnyx.Message.create(
            from_="+447537188201",
            to=worker.phone,
            text=message
        )

        sms = Sms.objects.create(
            sender="+447537188201",
            worker=worker,
            msg_type="sent",
            content=sms
        )

        return JsonResponse({"result": sms.content})


@csrf_exempt
def getsms(request):
    if request.method == "POST":
        worker_id = request.POST.get("worker_id")
        worker = get_object_or_404(Worker, pk=worker_id)
        sms = Sms.objects.filter(worker=worker).values_list()
        return JsonResponse({"sms":list(sms)})

@csrf_exempt
def sms_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        event_type = data['data']['event_type']
        from_number = data['data']['payload']['from']['phone_number']
        to_number = data['data']['payload']['to'][0]['phone_number']
        body = data['data']['payload']['text']

        worker = Worker.objects.get(phone=from_number)

        # Convert the reply text to lowercase for case-insensitive matching
        body_lower = body.lower()

        try:
            event_id = worker.message_confirmation.split(",")[1]
            event = Event.objects.get(pk=event_id)

            # Check if the reply contains the event's job number followed by 'yes'
            if event.job_number in body_lower and 'yes' in body_lower:
                sms = Sms.objects.create(
                    sender="+447537188201",
                    worker=worker,
                    msg_type="received",
                    content=body
                )

                if event.workers.count() < event.nr_of_crew:
                    # Assign the worker to the event
                    event.workers.add(worker)
                    worker.message_confirmation = "confirmed"
                    worker.save()

                    confirmation_message = f"You have been assigned to the event: {event.job_number}"
                    telnyx.Message.create(
                        from_="+447537188201",
                        to=worker.phone,
                        text=confirmation_message
                    )
                    sms = Sms.objects.create(
                        sender="+447537188201",
                        worker=worker,
                        msg_type="sent",
                        content=confirmation_message
                    )
                else:
                    worker.message_confirmation = "None"
                    worker.save()
                    notification_message = "This event has already been assigned the maximum number of crew members."
                    telnyx.Message.create(
                        from_="+447537188201",
                        to=worker.phone,
                        text=notification_message
                    )
                    sms = Sms.objects.create(
                        sender="+447537188201",
                        worker=worker,
                        msg_type="sent",
                        content=notification_message
                    )

        except IndexError:
            pass

        # For any other response, store the received message without assigning the worker
        sms = Sms.objects.create(
            sender="+447537188201",
            worker=worker,
            msg_type="received",
            content=body
        )

        # Perform any other actions based on the received message
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)


    
@csrf_exempt   
def send_crew_list(request, event_id):
    event = Event.objects.get(pk=event_id)

    if event.workers.count() == event.nr_of_crew:
        workers_assigned = event.workers.all()
        crew_list_message = f"Crew list {event.title} {event.job_number}\n" \
                            f"{event.date}\n" \
                            f"Start time: {event.start_time}\n" \
                            f"Hours: {event.duration}\n" \
                            f"Crew: {event.nr_of_crew}\n" \
                            f"Client: {event.client}\n" \
                            f"Location: {event.location}\n" \
                            f"Contact: {event.site_contact}\n" \
                            f"************************\n" \
                            f"{' - '.join([f'{w.first_name} - {w.phone}' for w in workers_assigned])}\n" \
                            f"Note: {event.notes}\n" 

        for worker_assigned in workers_assigned:
            telnyx.Message.create(
                from_="+447537188201",
                to=worker_assigned.phone,
                text=crew_list_message
            )
            sms = Sms.objects.create(
                sender="+447537188201",
                worker=worker_assigned,
                msg_type="sent",
                content=crew_list_message
            )

        return HttpResponse("Crew list SMS sent successfully!")
    else:
        return HttpResponse("Cannot send crew list. The required crew has not been assigned yet.")

class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        settings = Settings.objects.first()  # Fetch the settings object, adjust as needed
        skills = Skill.objects.all()
        categories = Category.objects.all()
        skill_form = SkillForm()
        category_form = CategoryForm()
        context = {
            'settings': settings,
            'skills': skills,
            'categories': categories,
            'skill_form': skill_form,
            'category_form': category_form,
        }
        return render(request, 'company_settings.html', context)

    def post(self, request):
        settings = Settings.objects.first()  # Fetch the settings object, adjust as needed
        skill_form = SkillForm(request.POST)
        category_form = CategoryForm(request.POST)
        
        if skill_form.is_valid():
            skill_form.save()
            return redirect('settings')
        
        if category_form.is_valid():
            category_form.save()
            return redirect('settings')
        
        skills = Skill.objects.all()
        categories = Category.objects.all()
        context = {
            'settings': settings,
            'skills': skills,
            'categories': categories,
            'skill_form': skill_form,
            'category_form': category_form,
        }
        return render(request, 'company_settings.html', context)

class SettingsEditView(LoginRequiredMixin, View):
    template_name = 'settings_edit.html'
    form_class = SettingsForm

    def get(self, request):
        settings = Settings.objects.first()  # Fetch the settings object, adjust as needed
        form = self.form_class(instance=settings)
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request):
        settings = Settings.objects.first()  # Fetch the settings object, adjust as needed
        form = self.form_class(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('settings')  # Redirect to the settings page
        context = {'form': form}
        return render(request, self.template_name, context)

def delete_skill(request, pk):
    if request.method == 'POST':
        skill_to_delete = Skill.objects.get(id=pk)
        skill_to_delete.delete()
        messages.success(request, 'Skill successfully deleted.')
    return redirect('settings')
    

def delete_category(request, pk):
    if request.method == 'POST':
        category_to_delete = Category.objects.get(id=pk)
        category_to_delete.delete()
        messages.success(request, 'Category successfully deleted.')
    return redirect('settings')

###################################################################
#
#                       CHAT Views
#
###################################################################    
    

class ChatView(LoginRequiredMixin, ListView):
    model = ChatMessage
    template_name = 'chat/chat.html'
    context_object_name = 'messages'
    ordering = 'timestamp'

def create_chat_room(request):
    if request.method == 'POST':
        form = CreateChatRoomForm(request.POST)
        if form.is_valid():
            chat_room = form.save()
            form.save_m2m()  # Save the participants
            # Redirect or display a success message
    else:
        form = CreateChatRoomForm()

    return render(request, 'chat/create_chat_room.html', {'form': form})