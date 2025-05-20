from openai import OpenAI
import json
import time
import re

import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIMGD.settings")
django.setup()  # os.environ['DJANGO_SETTINGS_MODULE']

from django.conf import settings
from core.models import *


class GEvaluation:
    def __init__(self, save_path, prompt_path):
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL
        )
        self.save_path = save_path
        self.prompt_path = prompt_path
        self.data = []

    def eval(self, session_id, source, system_output):
        cur_prompt = self.evaluate_prompt(source, system_output)
        # score = self.score(cur_prompt)
        score = 1.41
        self.data.append({
            'session_id': session_id,
            'source': source,
            'system_output': system_output,
            'score': score
        })

    def evaluate_prompt(self, source, system_output):
        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        cur_prompt = prompt.replace('{{Document}}', source).replace('{{Summary}}', system_output)

        return cur_prompt

    def score(self, cur_prompt):
        _response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[{"role": "system", "content": cur_prompt}],
            temperature=1.0,
            max_tokens=5,
            top_p=1.0,
            n=4
        )
        time.sleep(0.5)

        all_responses_str = [_response['choices'][i]['message']['content'] for i in range(len(_response['choices']))]

        all_scores = [self._extract_score(x) for x in all_responses_str]
        score = sum(all_scores) / len(all_scores)

        return score

    def _extract_score(self, response_str: str) -> float:
        matched = re.search("^ ?([\d\.]+)", response_str)
        if matched:
            try:
                score = float(matched.group(1))
            except:
                score = 0.0
        else:
            score = 0.0
        return score

    def save(self):
        with open(self.save_path, 'w', encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)


if __name__ == '__main__':
    save_path = "eval_res/report.json"
    prompt_path = "prompts/summeval/coh_detailed.txt"

    source = "abc abc"
    # system_output = "bca bca"

    g_eval = GEvaluation(save_path=save_path, prompt_path=prompt_path)
    system_output = SOAPNote.objects.get(id=8).final
    print(system_output)

    # cur_prompt = g_eval.evaluate_prompt(source=source, system_output=system_output)

    g_eval.eval(session_id="oijdso-f8u902u-0i2901e-u10fu", source=source, system_output=system_output)

    g_eval.save()
