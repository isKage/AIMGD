from django.shortcuts import render, get_object_or_404
from core.models import DiagnosisSession, SOAPNote, PSGReport


def history_list(request):
    """展示所有历史会话"""
    sessions = DiagnosisSession.objects.all().order_by('-updated_at')
    return render(request, 'history.html', {'sessions': sessions})


def history_detail(request, session_id):
    """展示单个会话的详细记录"""
    session = get_object_or_404(DiagnosisSession, session_id=session_id)
    soap_note = SOAPNote.objects.filter(session=session).first()  # 修改为允许空值
    report = PSGReport.objects.filter(session=session).first()  # 修改为允许空值

    context = {
        'session': session,
        'soap_note': soap_note,
        'report': report,
        'sessions': DiagnosisSession.objects.all().order_by('-updated_at')
    }
    return render(request, 'history_detail.html', context)
