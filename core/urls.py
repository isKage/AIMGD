from django.urls import path
from core.views import patient_api, doctor_api, report_api, history

urlpatterns = [
    # PIM
    path('index/', patient_api.index, name='chat_index'),
    path('start-chat/', patient_api.start_chat, name='start_chat'),
    path('patient/<uuid:session_id>/chat/', patient_api.patient_chat, name='patient_chat'),

    # CDG
    path('doctor/<uuid:session_id>/note/', doctor_api.note_generate, name='doctor_note'),

    # PSG
    path('patient/<uuid:session_id>/report/', report_api.report_generate, name='report_generate'),

    # history
    path('history/', history.history_list, name='history_list'),
    path('history/<uuid:session_id>/detail/', history.history_detail, name='history_detail'),
]

