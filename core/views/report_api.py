# 患者报告接口（PSG）
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from core.models import DiagnosisSession, SOAPNote, PSGReport
from core.services import PSGService


def report_generate(request, session_id):
    session = get_object_or_404(DiagnosisSession, session_id=session_id)
    disease_dict = session.diseases[-1]
    disease_name = max(disease_dict, key=disease_dict.get)
    # note = get_object_or_404(SOAPNote, session_id=session_id)  # 获取 SOAP
    report, created = PSGReport.objects.get_or_create(
        session=session,
        defaults={'concise': '', 'final': '', 'disease_name': disease_name}
    )

    if request.method == "POST":
        step = request.POST.get('step')
        psg_service = PSGService(session)

        if step == 'concise':
            # 1. 初次生成易懂报告
            # report.concise = psg_service.generate_concise()
            pass
        elif step == 'final':
            # 2. 最终
            report.final = psg_service.generate_final()
        report.save()
        return JsonResponse({'status': 'success', 'content': getattr(report, step)})

    context = {
        'session_id': session_id,
        'report': report,
        'generated': any(report.final)
    }

    return render(request, 'report.html', context)
