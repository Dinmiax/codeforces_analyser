import sys

sys.path.append('../')

import asyncio
import aiohttp
from collections import defaultdict
from typing import List

from sqlalchemy.orm import Session
from app.database import base
from app.models import schemas
from app.database import models
from app.config import settings

from urllib.request import urlopen, Request
from html.parser import HTMLParser
import html
import re
import sys
import json
import os


class CodeforcesUpdater:
    def __init__(self, db: Session):
        self.db = db

    async def get_solved_problems(self, handle):
        url = f"{settings.CODEFORCES_API_URL}/user.status?handle={handle}"
        params = {"handle": handle}
        try:
            async with aiohttp.ClientSession() as http:
                async with http.get(url, params=params, timeout=20) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

                if data.get("status") != "OK":
                    return None

                if data['status'] != 'OK':
                    print(f"Ошибка API: {data.get('comment', 'Неизвестная ошибка')}")
                    return None

                submissions = data['result']
                solved_problems = []

                for submission in submissions:
                    if submission.get('verdict') == 'OK':
                        contest_id = submission.get('contestId')
                        problem_json = submission.get('problem')
                        index = problem_json.get('index')
                        name = problem_json.get('name')
                        tags = problem_json.get('tags')
                        rating = problem_json.get('rating')
                        problem = {"contest_id": contest_id, "index": index, "name": name, "tags": tuple(tags),
                                   "rating": rating}
                        solved_problems.append(problem)
                res = []
                for i in solved_problems:
                    res.append(schemas.SaveProblem(contest_id=i["contest_id"], index=i["index"], name=i["name"],
                                                   tags=list(i["tags"]), rating=i["rating"]))

                return res
        except ValueError as e:
            print(f"Ошибка при парсинге JSON: {e}")
            return None

    async def check_problem(self, problem_to_find: schemas.FindProblem) -> bool:
        problem = self.db.query(models.Problem).filter(models.Problem.contest_id == problem_to_find.contest_id,
                                                       models.Problem.index == problem_to_find.index).first()
        if (problem):
            return problem
        return None

    async def add_problem(self, problem_to_add: schemas.SaveProblem):
        problem = models.Problem(
            index=problem_to_add.index,
            contest_id=problem_to_add.contest_id,
            name=problem_to_add.contest_id,
            tags=problem_to_add.tags,
            rating=problem_to_add.rating
        )
        exists = await self.check_problem(schemas.FindProblem(
            contest_id=problem_to_add.contest_id,
            index=problem_to_add.index))
        if (exists is not None):
            return exists
        self.db.add(problem)
        self.db.commit()
        self.db.refresh(problem)
        return problem

    async def add_problems(self, problems_to_add: List[schemas.SaveProblem]):
        res = []
        for problem_to_add in problems_to_add:
            problem = models.Problem(
                index=problem_to_add.index,
                contest_id=problem_to_add.contest_id,
                name=problem_to_add.contest_id,
                tags=problem_to_add.tags,
                rating=problem_to_add.rating
            )

            exists = await self.check_problem(schemas.FindProblem(
                contest_id=problem_to_add.contest_id,
                index=problem_to_add.index))
            if (exists is not None):
                res.append(exists)
                continue
            self.db.add(problem)
            res.append(problem)

        self.db.commit()
        for problem in res:
            self.db.refresh(problem)
        return res


# Это просто пиздец, я даже разбираться в этом не хочу
# Ебись оно все конем


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


class CodeforcesProblemParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        self.problem_data = {
            'title': '',
            'time_limit': '',
            'memory_limit': '',
            'statement': [],  # HTML параграфы
            'input_spec': [],  # HTML параграфы
            'output_spec': [],  # HTML параграфы
            'note': [],  # HTML параграфы
            'samples': [],  # Список тестов
            'raw_text': '',  # Сырой текст без форматирования для нейросети
        }
        self.current_section = None
        self.in_pre = False
        self.in_sample_block = False
        self.current_sample_type = None
        self.current_sample = {'input': '', 'output': ''}
        self.sample_count = 0
        self.current_test_lines = []
        self.current_text = []
        self.in_paragraph = False
        self.div_stack = []
        self.in_title = False
        self.raw_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '')
        if tag == 'div':
            self.div_stack.append(class_name)
        if tag == 'div':
            if 'problem-statement' in class_name:
                self.current_section = 'statement'
            elif 'time-limit' in class_name:
                self.current_section = 'time_limit'
            elif 'memory-limit' in class_name:
                self.current_section = 'memory_limit'
            elif 'input-specification' in class_name:
                self.current_section = 'input_spec'
            elif 'output-specification' in class_name:
                self.current_section = 'output_spec'
            elif 'sample-tests' in class_name:
                self.current_section = 'samples'
                self.in_sample_block = True
            elif 'input' in class_name and self.in_sample_block:
                self.current_sample_type = 'input'
                self.current_test_lines = []
            elif 'output' in class_name and self.in_sample_block:
                self.current_sample_type = 'output'
                self.current_test_lines = []
            elif 'note' in class_name:
                self.current_section = 'note'
            elif 'title' in class_name:
                self.in_title = True

        elif tag == 'pre':
            self.in_pre = True
            self.current_test_lines = []

        elif tag == 'p':
            self.in_paragraph = True
            self.current_text = []

        elif tag == 'br':
            if self.in_pre:
                self.current_test_lines.append('<br>')
            elif self.current_sample_type:
                self.current_test_lines.append('<br>')

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.div_stack:
                self.div_stack.pop()

            if self.in_title:
                self.in_title = False

            if tag == 'div' and self.current_sample_type:
                if self.current_sample_type == 'input':
                    self.current_sample['input'] = ''.join(self.current_test_lines)
                    self.current_test_lines = []
                elif self.current_sample_type == 'output':
                    self.current_sample['output'] = ''.join(self.current_test_lines)
                    self.current_test_lines = []
                    if self.current_sample['input'] and self.current_sample['output']:
                        self.problem_data['samples'].append({
                            'input': self.current_sample['input'],
                            'output': self.current_sample['output']
                        })
                        self.current_sample = {'input': '', 'output': ''}
                    self.sample_count += 1
                self.current_sample_type = None

        elif tag == 'pre':
            self.in_pre = False
            if self.current_sample_type == 'input':
                self.current_sample['input'] = ''.join(self.current_test_lines)
            elif self.current_sample_type == 'output':
                self.current_sample['output'] = ''.join(self.current_test_lines)
                if self.current_sample['input'] and self.current_sample['output']:
                    self.problem_data['samples'].append({
                        'input': self.current_sample['input'],
                        'output': self.current_sample['output']
                    })
                    self.current_sample = {'input': '', 'output': ''}
                self.sample_count += 1
            self.current_test_lines = []

        elif tag == 'p':
            self.in_paragraph = False
            if self.current_text:
                text = ''.join(self.current_text).strip()
                if self.current_section == 'statement':
                    self.problem_data['statement'].append(text)
                elif self.current_section == 'input_spec':
                    self.problem_data['input_spec'].append(text)
                elif self.current_section == 'output_spec':
                    self.problem_data['output_spec'].append(text)
                elif self.current_section == 'note':
                    self.problem_data['note'].append(text)
                self.raw_buffer.append(text + ' ')
            self.current_text = []


def handle_data(self, data):
    if any(keyword in data for keyword in [
        'Server time:', 'Privacy Policy', 'Terms and Conditions',
        'Mobile version', 'Desktop version', 'Mirzayanov',
        'Programming contests', 'Web 2.0', 'Copyright', 'Supported by',
        'User lists', 'Name', 'switch to', 'Codeforces (c)'
    ]):
        return
    if re.match(
            r'^\s*(function|var|let|const|document|window|navigator|\.on\(|\.click\(|\.ready\(|\.hover\(|\$\(|jQuery)',
            data.strip()):
        return
    if self.current_section == 'time_limit' and not self.in_title:
        time_match = re.search(r'(\d+)\s*(second|sec|s)', data, re.IGNORECASE)
        if time_match:
            num = time_match.group(1)
            unit = 'seconds' if int(num) != 1 else 'second'
            self.problem_data['time_limit'] = f"{num} {unit}"

    elif self.current_section == 'memory_limit' and not self.in_title:
        memory_match = re.search(r'(\d+)\s*(megabyte|mb|mebibyte|mib)', data, re.IGNORECASE)
        if memory_match:
            num = memory_match.group(1)
            self.problem_data['memory_limit'] = f"{num} MB"

    # Обработка заголовка
    elif self.in_title:
        if re.match(r'^[A-F]\.\s+', data.strip()):
            self.problem_data['title'] = data.strip()

    # Сбор текста в параграфах
    elif self.in_paragraph:
        self.current_text.append(data)
        self.raw_buffer.append(data + ' ')

    # Сбор тестов
    elif self.in_pre or self.current_sample_type:
        if self.current_sample_type:
            self.current_test_lines.append(data)
        elif self.in_pre:
            self.current_test_lines.append(data)


def handle_entityref(self, name):
    decoded = html.unescape(f"&{name};")
    if self.in_paragraph:
        self.current_text.append(decoded)
        self.raw_buffer.append(decoded + ' ')
    elif self.in_pre or self.current_sample_type:
        if self.current_sample_type:
            self.current_test_lines.append(decoded)
        elif self.in_pre:
            self.current_test_lines.append(decoded)


def handle_charref(self, name):
    if name.startswith('x'):
        decoded = chr(int(name[1:], 16))
    else:
        decoded = chr(int(name))

    if self.in_paragraph:
        self.current_text.append(decoded)
        self.raw_buffer.append(decoded + ' ')
    elif self.in_pre or self.current_sample_type:
        if self.current_sample_type:
            self.current_test_lines.append(decoded)
        elif self.in_pre:
            self.current_test_lines.append(decoded)


def get_raw_text(self):
    raw_text = ''.join(self.raw_buffer)
    raw_text = re.sub(r'\s+', ' ', raw_text)
    raw_text = re.sub(r'\n+', ' ', raw_text)
    return raw_text.strip()


# Я ебал разбираца в этом, просто ебну класс поверх и пару враперов, а там уже сами думайте
class ProblemParser:
    def parse_problem(self, contest_id, problem_id):
        url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"

        # print(f"Загружаем задачу {problem_id} из контеста {contest_id}...")

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as response:
                html_content = response.read().decode('utf-8')

            parser = CodeforcesProblemParser()
            parser.feed(html_content)

            problem_data = parser.problem_data
            if not problem_data['title']:
                title_match = re.search(r'<div class="title">([A-F])\.\s*(.*?)</div>', html_content)
                if title_match:
                    problem_data['title'] = f"{title_match.group(1)}. {html.unescape(title_match.group(2).strip())}"

            if not problem_data['time_limit']:
                time_match = re.search(r'<div class="time-limit">.*?(\d+)\s*(second|sec|s)',
                                       html_content, re.IGNORECASE | re.DOTALL)
                if time_match:
                    num = time_match.group(1)
                    unit = 'seconds' if int(num) != 1 else 'second'
                    problem_data['time_limit'] = f"{num} {unit}"

            if not problem_data['memory_limit']:
                memory_match = re.search(r'<div class="memory-limit">.*?(\d+)\s*(megabyte|mb|mebibyte|mib)',
                                         html_content, re.IGNORECASE | re.DOTALL)
                if memory_match:
                    num = memory_match.group(1)
                    problem_data['memory_limit'] = f"{num} MB"
            if not problem_data['statement']:
                statement_pattern = r'<div class="problem-statement">(.*?)<div class="input-specification">'
                statement_match = re.search(statement_pattern, html_content, re.DOTALL)
                if statement_match:
                    statement_html = statement_match.group(1)
                    statement_html = re.sub(r'<div class="title">.*?</div>', '', statement_html, flags=re.DOTALL)
                    statement_html = re.sub(r'<div class="time-limit">.*?</div>', '', statement_html, flags=re.DOTALL)
                    statement_html = re.sub(r'<div class="memory-limit">.*?</div>', '', statement_html, flags=re.DOTALL)
                    paragraphs = re.findall(r'<p>(.*?)</p>', statement_html, re.DOTALL)
                    for para in paragraphs:
                        para_text = re.sub(r'<[^>]+>', ' ', para)
                        para_text = re.sub(r'\s+', ' ', para_text)
                        para_text = html.unescape(para_text).strip()
                        if para_text:
                            problem_data['statement'].append(para_text)

            # Если input_spec не получен
            if not problem_data['input_spec']:
                input_pattern = r'<div class="input-specification">.*?<div class="section-title">.*?</div>(.*?)</div>'
                input_match = re.search(input_pattern, html_content, re.DOTALL)
                if input_match:
                    input_html = input_match.group(1)
                    paragraphs = re.findall(r'<p>(.*?)</p>', input_html, re.DOTALL)
                    for para in paragraphs:
                        para_text = re.sub(r'<[^>]+>', ' ', para)
                        para_text = re.sub(r'\s+', ' ', para_text)
                        para_text = html.unescape(para_text).strip()
                        if para_text:
                            problem_data['input_spec'].append(para_text)

            # Если output_spec не получен
            if not problem_data['output_spec']:
                output_pattern = r'<div class="output-specification">.*?<div class="section-title">.*?</div>(.*?)</div>'
                output_match = re.search(output_pattern, html_content, re.DOTALL)
                if output_match:
                    output_html = output_match.group(1)
                    paragraphs = re.findall(r'<p>(.*?)</p>', output_html, re.DOTALL)
                    for para in paragraphs:
                        para_text = re.sub(r'<[^>]+>', ' ', para)
                        para_text = re.sub(r'\s+', ' ', para_text)
                        para_text = html.unescape(para_text).strip()
                        if para_text:
                            problem_data['output_spec'].append(para_text)

            # Если note не получен
            if not problem_data['note']:
                note_pattern = r'<div class="note">.*?<div class="section-title">.*?</div>(.*?)</div>'
                note_match = re.search(note_pattern, html_content, re.DOTALL)
                if note_match:
                    note_html = note_match.group(1)
                    paragraphs = re.findall(r'<p>(.*?)</p>', note_html, re.DOTALL)
                    for para in paragraphs:
                        para_text = re.sub(r'<[^>]+>', ' ', para)
                        para_text = re.sub(r'\s+', ' ', para_text)
                        para_text = html.unescape(para_text).strip()
                        if para_text:
                            problem_data['note'].append(para_text)

            # Если примеры не получены
            if not problem_data['samples']:
                samples_section = re.search(r'<div class="sample-tests">(.*?)</div>\s*</div>', html_content, re.DOTALL)
                if samples_section:
                    samples_html = samples_section.group(1)
                    input_blocks = re.findall(r'<div class="input">(.*?)</div>', samples_html, re.DOTALL)
                    output_blocks = re.findall(r'<div class="output">(.*?)</div>', samples_html, re.DOTALL)

                    for i in range(min(len(input_blocks), len(output_blocks))):
                        input_html = input_blocks[i]
                        output_html = output_blocks[i]
                        pre_match = re.search(r'<pre>(.*?)</pre>', input_html, re.DOTALL)
                        if pre_match:
                            input_text = pre_match.group(1)
                            input_text = re.sub(r'<[^>]+>', '', input_text)
                            input_text = html.unescape(input_text).strip()
                            input_text = input_text.replace('\n', '<br>')
                        else:
                            test_lines = re.findall(r'<div class="test-example-line[^"]*"[^>]*>(.*?)</div>', input_html,
                                                    re.DOTALL)
                            if test_lines:
                                lines_by_num = {}
                                for line in test_lines:
                                    num_match = re.search(r'test-example-line-(\d+)', line)
                                    if num_match:
                                        line_num = num_match.group(1)
                                        text_match = re.search(r'>(.*?)<', line)
                                        if text_match:
                                            text = html.unescape(text_match.group(1)).strip()
                                            if line_num not in lines_by_num:
                                                lines_by_num[line_num] = []
                                            lines_by_num[line_num].append(text)
                                input_parts = []
                                for line_num in sorted(lines_by_num.keys()):
                                    line_text = '<br>'.join(lines_by_num[line_num])
                                    input_parts.append(line_text)
                                input_text = '<br><br>'.join(input_parts)
                            else:
                                input_text = ''

                        # Обрабатываем output аналогично
                        pre_match = re.search(r'<pre>(.*?)</pre>', output_html, re.DOTALL)
                        if pre_match:
                            output_text = pre_match.group(1)
                            output_text = re.sub(r'<[^>]+>', '', output_text)
                            output_text = html.unescape(output_text).strip()
                            output_text = output_text.replace('\n', '<br>')
                        else:
                            test_lines = re.findall(r'<div class="test-example-line[^"]*"[^>]*>(.*?)</div>',
                                                    output_html,
                                                    re.DOTALL)
                            if test_lines:
                                lines_by_num = {}
                                for line in test_lines:
                                    num_match = re.search(r'test-example-line-(\d+)', line)
                                    if num_match:
                                        line_num = num_match.group(1)
                                        text_match = re.search(r'>(.*?)<', line)
                                        if text_match:
                                            text = html.unescape(text_match.group(1)).strip()
                                            if line_num not in lines_by_num:
                                                lines_by_num[line_num] = []
                                            lines_by_num[line_num].append(text)

                                output_parts = []
                                for line_num in sorted(lines_by_num.keys()):
                                    line_text = '<br>'.join(lines_by_num[line_num])
                                    output_parts.append(line_text)
                                output_text = '<br><br>'.join(output_parts)
                            else:
                                output_text = ''

                        if input_text or output_text:
                            problem_data['samples'].append({
                                'input': input_text,
                                'output': output_text
                            })

            problem_data['raw_text'] = parser.get_raw_text()
            if problem_data['input_spec'] and problem_data['input_spec'][0]:
                problem_data['input_spec'][0] = re.sub(r'^Input[:\s]*', '', problem_data['input_spec'][0],
                                                       flags=re.IGNORECASE)
            if problem_data['output_spec'] and problem_data['output_spec'][0]:
                problem_data['output_spec'][0] = re.sub(r'^Output[:\s]*', '', problem_data['output_spec'][0],
                                                        flags=re.IGNORECASE)
            if problem_data['note'] and problem_data['note'][0]:
                problem_data['note'][0] = re.sub(r'^Note[:\s]*', '', problem_data['note'][0], flags=re.IGNORECASE)
            if problem_data['note']:
                cleaned_notes = []
                for note in problem_data['note']:
                    note = re.sub(r'Codeforces \(c\).*', '', note, flags=re.DOTALL)
                    note = re.sub(r'Server time:.*', '', note, flags=re.DOTALL)
                    note = re.sub(r'Dec/\d{2}/\d{4}.*', '', note)
                    note = re.sub(r'\(l\d\).*', '', note)
                    note = re.sub(r'mobile version.*', '', note, flags=re.IGNORECASE)
                    note = re.sub(r'Supported by.*', '', note)
                    note = re.sub(r'User lists Name.*', '', note)
                    note = re.sub(r'\$\(function.*', '', note, flags=re.DOTALL)
                    note = re.sub(r'\.ready\(function.*', '', note, flags=re.DOTALL)
                    note = re.sub(r'Copyright.*', '', note)
                    note = re.sub(r'Mirzayanov.*', '', note)
                    note = note.strip()
                    if note:
                        cleaned_notes.append(note)
                problem_data['note'] = cleaned_notes

            return problem_data

        except Exception as e:
            print(f"Ошибка при загрузке задачи: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def get_problem(self, problem: schemas.FindProblem) -> schemas.ProblemData:
        data = self.parse_problem(problem.contest_id, problem.index)
        return schemas.ProblemData(data)
