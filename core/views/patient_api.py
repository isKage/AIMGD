from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from core.models import DiagnosisSession
from core.services import PIMService
import json


def index(request):
    """首页视图"""
    return render(request, 'index.html')


def start_chat(request):
    """创建新会话并重定向到聊天页面"""
    new_session = DiagnosisSession.objects.create()
    return redirect('patient_chat', session_id=new_session.session_id)


def patient_chat(request, session_id):
    """聊天页面视图"""
    session = get_object_or_404(DiagnosisSession, session_id=session_id)

    if request.method == 'POST':
        # 获取患者输入
        patient_input = request.POST.get('patient_input', '').strip()
        if not patient_input:
            return JsonResponse({'error': '输入不能为空'}, status=400)

        # 调用PIM服务处理
        pim_service = PIMService()

        if not session.patient_response:
            '''第一次问诊'''
            session_data = pim_service.start_new_session(
                patient_desc=patient_input,
                session_id=session_id
            )

            # 生成问题
            ai_response = pim_service.generate_question(session_data['IEG'], session_data['diseases'])

            # 保存初始数据
            session.append_patient_response(patient_input)
            session.append_disease(session_data['diseases'])
            session.append_IEG(session_data['IEG'])
            session.append_ai_response(ai_response)

        else:
            '''后续对话'''

            # 获取症状回答 True or False
            ieg = DiagnosisSession.objects.get(session_id=session_id).IEG[-1]
            symptom_opt = max(ieg)
            for k in ieg:
                if ieg[k] > ieg[symptom_opt]:
                    symptom_opt = k
            question = DiagnosisSession.objects.get(session_id=session_id).ai_response[-1]
            symptom_response = pim_service.is_symptom_occurrence(patient_input, symptom_opt, question)  # {'S1': True}
            session.update_symptom_answer(symptom_opt, symptom_response[symptom_opt])  # 存入症状回答

            session_data = pim_service.next_round(
                patient_ans=patient_input,
                session_id=session_id,
                symptom_response=symptom_response[symptom_opt],
                symptom=symptom_opt
            )

            # 获取下一个问题
            ai_response = pim_service.generate_question(session_data['IEG'], session_data['diseases'])

            # 保存数据
            session.append_patient_response(patient_input)
            session.append_disease(session_data['diseases'])
            session.append_IEG(session_data['IEG'])
            session.append_ai_response(ai_response)

            # 刷新session对象
            # session.refresh_from_db()

            # 返回JSON响应
            # return JsonResponse({'session': session})

        if pim_service.should_stop(session_id=session_id):
            return redirect('report_generate', session_id=session_id)

    # GET请求显示聊天页面
    return render(request, 'chat.html', {'session': session})
