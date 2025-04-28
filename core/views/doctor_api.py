# 医生端接口（CDG）
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from core.models import DiagnosisSession, SOAPNote
from core.services import CDGService


def note_generate(request, session_id):
    session = get_object_or_404(DiagnosisSession, session_id=session_id)
    note, created = SOAPNote.objects.get_or_create(
        session=session,
        defaults={'initial': '', 'soap': '', 'final': ''}
    )

    if request.method == 'POST':
        step = request.POST.get('step')
        cdg_service = CDGService(session)  # 封装了各类方法

        if step == 'initial':
            # 1. 初次生成
            note.disease_name, note.initial = cdg_service.generate_initial()
        elif step == 'soap':
            # 2. soap 格式
            note.soap = cdg_service.generate_soap()
        elif step == 'final':
            # 3. 根据疾病补充信息
            note.final = final_note = cdg_service.generate_final(disease=note.disease_name)
        note.save()
        return JsonResponse({'status': 'success', 'content': getattr(note, step)})

    context = {
        'session_id': session_id,
        'note': note,
        'generated': any([note.initial, note.soap, note.final])
    }

    return render(request, 'note.html', context)
