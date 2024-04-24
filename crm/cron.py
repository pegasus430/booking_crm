from django_cron import CronJobBase, Schedule
from datetime import datetime, timedelta
from core.models import Event
from django.core.mail import send_mail
from django.conf import settings

class SendConfirmationEmails(CronJobBase):
    RUN_EVERY_MINS = 1  # Adjust the frequency as needed

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'crm.send_confirmation_emails'  # Replace with your app's code

    def do(self):
        # Get events that need confirmation
        events_to_confirm = Event.objects.filter(
            date__lt=datetime.now().date() - timedelta(days=1),  # Events that occurred yesterday or earlier
            confirmation_sent=False  # Assuming you have a field to track if confirmation email was sent
        )

        for event in events_to_confirm:
            print(f'Sending confirmation email for Event ID: {event.id}')
            
            # Send confirmation email
            subject = 'Confirmation Needed: Event Crew and Duration'
            message = 'Hi there, I hope you\'re doing well. Could you please confirm the chargeable hours for the crew provided to you yesterday at (event location), event number of crew - event duration.'  # Modify the message accordingly
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[event.client.primary_email],
                fail_silently=False,
            )

            print(f'Confirmation email sent for Event ID: {event.id}')
