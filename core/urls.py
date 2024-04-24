from django.urls import path
from core import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('get_addresses/', views.get_addresses, name='get_addresses'),

    #------------------------Worker urls ----------------------------#
    path("workers/", views.WorkerListView.as_view(), name="worker_list"),
    path("worker_detail/<int:worker_id>/", views.WorkerDetailView.as_view(), name="worker_detail"),
    path("add_worker/", views.AddWorkerView.as_view(), name="add_worker"),
    path('toggle_worker_status/<int:id>/', views.toggle_worker_status, name='toggle_worker_status'),
    path("edit_worker/<int:worker_id>/", views.EditWorkerView.as_view(), name="edit_worker"),
    path("delete_worker/<int:worker_id>/", views.DeleteWorkerView.as_view(), name="delete_worker"),
    path("add_worker_document/", views.AddWorkerDocumentView.as_view(), name="add_worker_document"),
    path("delete_worker_document/<int:worker_id>/<int:document_id>/", views.DeleteWorkerDocumentView.as_view(), name="delete_worker_document"),
    

    #------------------------Client urls ----------------------------#
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("client_detail/<int:client_id>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("add_client/", views.AddClientView.as_view(), name="add_client"),
    path('add_client/', views.AddClientView.as_view(), name='add_client_redirect'),
    path("edit_client/<int:client_id>/", views.EditClientView.as_view(), name="edit_client"),
    path("delete_client/<int:client_id>/", views.DeleteClientView.as_view(), name="delete_client"),
    path("add_client_document/", views.AddClientDocumentView.as_view(), name="add_client_document"),
    path("delete_client_document/<int:client_id>/<int:document_id>/", views.DeleteClientDocumentView.as_view(), name="delete_client_document"),

    #------------------------Event urls ----------------------------#
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("event_detail/<int:event_id>/", views.EventDetailView.as_view(), name="event_detail"),
    path("add_event/", views.AddEventView.as_view(), name="add_event"),
    path("edit_event/<int:event_id>/", views.EditEventView.as_view(), name="edit_event"),
    path("delete_event/<int:event_id>/", views.DeleteEventView.as_view(), name="delete_event"),
    path("remove_event_worker/<int:event_id>/<int:worker_id>/", views.RemoveWorkerFromEvent.as_view(), name="remove_event_worker"),
    path("assign_worker/", views.AssignWorker.as_view(), name="assign_worker"),
    path('event/duplicate/<int:pk>/', views.DuplicateEventView.as_view(), name='duplicate_event'),
    #------------------------Timesheet urls ----------------------------#
    path("timesheets/", views.TimesheetListView.as_view(), name="timesheet_list"),
    path('timesheets/get_timesheet_byweek', views.get_timesheet_byweek, name='get_timesheet_byweek'),
    path('timesheet_detail/<int:worker_id>/', views.TimesheetDetailView.as_view(), name='timesheet_detail'),
    path('timesheet/<int:worker_id>/pdf/', views.download_timesheet_pdf, name='download_timesheet_pdf'),
    path('timesheet/<int:worker_id>/csv/', views.download_csv, name='download_csv'),
    path('update_timesheet/<int:timesheet_id>/update/', views.update_timesheet, name='update_timesheet'),
    path('update_timesheet_with_hourlyrate/<int:worker_id>/update/', views.update_timesheet_with_hourlyrate, name='update_timesheet_with_hourlyrate'),
    path('delete_timesheet/<int:worker_id>/', views.delete_timesheet, name='delete_timesheet'),
    path('create_timesheet/<int:worker_id>/', views.create_timesheet, name='create_timesheet'),
    path('auto_create_timesheet/', views.auto_create_timesheet, name='auto_create_timesheet'),
    path('send_timesheet/<int:worker_id>/', views.send_timesheet_email, name='send_timesheet_email'),
    #------------------------Invoice urls ----------------------------#
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    #path('create_invoice/<int:client_id>/', views.create_invoice, name='create_invoice'),
    path('create_invoice/', views.createInvoice, name='create_invoice'),
    path('create-build/<int:id>/', views.createBuildInvoice, name='create-build-invoice'),
    #path('update_invoice/<int:invoice_id>/update', views.update_invoice, name='update_invoice'),
    path('delete_invoice/<int:invoice_id>/', views.delete_invoice, name='delete_invoice'),
    path('view_invoice/<int:id>/', views.view_invoice, name='view_invoice'),
    path('download_invoice_pdf/<int:id>/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('send-invoice-email/<int:invoice_id>/', views.send_invoice_email, name='send_invoice_email'),
    path('invoice/<int:invoice_id>/toggle/', views.toggle_invoice_status, name='toggle_invoice_status'),
    #path('invoice_detail/<str:invoice_number>/<int:client_id>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),

    #------------------------SMS urls ----------------------------#
    path("sms/", views.SMSView.as_view(), name="sms"),
    path("getsms", views.getsms, name="getsms"),
    path("send_sms/", views.send_sms, name="send_sms"),
    path('sms/webhook/', views.sms_webhook, name='sms_webhook'),
    path('send_crew_list/<int:event_id>/', views.send_crew_list, name='send_crew_list'),
    #path('start_new_chat/', views.start_new_chat, name='start_new_chat'),


    #------------------------Settings urls ----------------------------#
    path("company_settings/", views.SettingsView.as_view(), name="settings"),
    path('settings_edit/', views.SettingsEditView.as_view(), name='settings_edit'),

#------------------------Internal chat urls ----------------------------#
    path('chat/', views.ChatView.as_view(), name='chat'),

#------------------------Skills and Categories urls ----------------------------#

    path('delete_skill/<int:pk>/', views.delete_skill, name='delete_skill'),
    path('delete_category/<int:pk>/', views.delete_category, name='delete_category'),
]

