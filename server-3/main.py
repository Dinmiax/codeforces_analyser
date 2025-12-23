#!/usr/bin/env python3
"""
🤖 CODEFORCES LLM AGENT SYSTEM - Полная версия с новым парсером, переводчиком и генератором контестов
"""

import json
import re
import time
import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import asyncio
import aiohttp
from pydantic import BaseModel, Field
import html
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from bs4 import BeautifulSoup

# Импорт Mistral AI
try:
    from mistralai import Mistral

    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    print("⚠️ Mistral AI не установлен. Используйте: pip install mistralai")

# Импорт конфигурации
try:
    from config import (
        MISTRAL_API_KEY, APIConfig, PathConfig, ContestConfig,
        TranslationConfig, KeywordsConfig, MessagesConfig, PromptsConfig
    )
except ImportError:
    # Fallback конфигурация
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")


    class APIConfig:
        MISTRAL_MODEL = "mistral-large-latest"
        MISTRAL_TEMPERATURE = 0.7
        MISTRAL_MAX_TOKENS = 4000


    class ContestConfig:
        MIN_PROBLEMS = 2
        MAX_PROBLEMS = 10
        DEFAULT_PROBLEM_COUNT = 5
        CF_TOPICS = {
            "dp": {"name": "Динамическое программирование"},
            "graphs": {"name": "Графы"},
            "math": {"name": "Математика"},
            "greedy": {"name": "Жадные алгоритмы"},
            "implementation": {"name": "Реализация"}
        }

        @staticmethod
        def get_difficulty_info(difficulty):
            levels = {
                1: {"label": "Новичок", "min_rating": 800, "max_rating": 1000},
                2: {"label": "Легкий", "min_rating": 1000, "max_rating": 1300},
                3: {"label": "Средний", "min_rating": 1300, "max_rating": 1600},
                4: {"label": "Сложный", "min_rating": 1600, "max_rating": 1900},
                5: {"label": "Эксперт", "min_rating": 1900, "max_rating": 2400},
            }
            return levels.get(difficulty, levels[3])

# ==================== ИНИЦИАЛИЗАЦИЯ MISTRAL AI ====================

if MISTRAL_AVAILABLE and MISTRAL_API_KEY:
    mistral_client = Mistral(api_key=MISTRAL_API_KEY)
else:
    mistral_client = None
    print("⚠️ Mistral AI не инициализирован. Проверьте API ключ и установку библиотеки.")

# ==================== НОВЫЙ ПАРСЕР С ИЗВЛЕЧЕНИЕМ ТЕСТОВ ====================

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


class CodeforcesProblemParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        # Основные данные задачи
        self.problem_data = {
            'title': '',
            'time_limit': '',
            'memory_limit': '',
            'statement': [],
            'input_spec': [],
            'output_spec': [],
            'note': [],
            'samples': [],
            'raw_text': '',
        }

        # Состояние для извлечения тестов
        self.in_sample_section = False
        self.in_input_div = False
        self.in_output_div = False
        self.in_pre = False
        self.collecting_input = False
        self.collecting_output = False
        self.current_input = []
        self.current_output = []

        # Текущая секция
        self.current_section = None

        # Для текста
        self.current_text = []
        self.in_paragraph = False
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '')

        # Отслеживаем секцию с тестами
        if tag == 'div':
            if 'sample-tests' in class_name:
                self.in_sample_section = True
            elif 'input' in class_name and self.in_sample_section:
                self.in_input_div = True
                self.collecting_input = True
                self.current_input = []
            elif 'output' in class_name and self.in_sample_section:
                self.in_output_div = True
                self.collecting_output = True
                self.current_output = []
            elif 'title' in class_name:
                self.in_title = True

        elif tag == 'pre':
            self.in_pre = True

        elif tag == 'p':
            self.in_paragraph = True
            self.current_text = []

        # Определение других секций
        if tag == 'div':
            if 'problem-statement' in class_name:
                self.current_section = 'statement'
            elif 'input-specification' in class_name:
                self.current_section = 'input_spec'
            elif 'output-specification' in class_name:
                self.current_section = 'output_spec'
            elif 'note' in class_name:
                self.current_section = 'note'
            elif 'time-limit' in class_name:
                self.current_section = 'time_limit'
            elif 'memory-limit' in class_name:
                self.current_section = 'memory_limit'

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.in_output_div:
                self.in_output_div = False
                self.collecting_output = False
                # Сохраняем тест
                if self.current_input and self.current_output:
                    input_text = ''.join(self.current_input).strip()
                    output_text = ''.join(self.current_output).strip()

                    # Очищаем от лишних <br> в конце
                    while input_text.endswith('<br>'):
                        input_text = input_text[:-4]
                    while output_text.endswith('<br>'):
                        output_text = output_text[:-4]

                    if input_text and output_text:
                        self.problem_data['samples'].append({
                            'input': input_text,
                            'output': output_text
                        })

            elif self.in_input_div:
                self.in_input_div = False
                self.collecting_input = False

            if self.in_title:
                self.in_title = False

        elif tag == 'pre':
            self.in_pre = False

        elif tag == 'p':
            self.in_paragraph = False
            if self.current_text:
                text = ''.join(self.current_text).strip()
                if text:
                    if self.current_section == 'statement':
                        self.problem_data['statement'].append(text)
                        self.problem_data['raw_text'] += text + ' '
                    elif self.current_section == 'input_spec':
                        self.problem_data['input_spec'].append(text)
                        self.problem_data['raw_text'] += text + ' '
                    elif self.current_section == 'output_spec':
                        self.problem_data['output_spec'].append(text)
                        self.problem_data['raw_text'] += text + ' '
                    elif self.current_section == 'note':
                        self.problem_data['note'].append(text)
                        self.problem_data['raw_text'] += text + ' '
                self.current_text = []

    def handle_data(self, data):
        # Пропускаем технический мусор
        if any(keyword in data.lower() for keyword in [
            'server time:', 'privacy policy', 'terms and conditions',
            'mobile version', 'desktop version', 'mirzayanov',
            'programming contests', 'web 2.0', 'copyright', 'supported by',
            'user lists', 'name', 'switch to', 'codeforces (c)',
            'входные данные', 'выходные данные', 'input', 'output',
            'скопировать', 'copy', 'пример', 'example', 'примеры', 'examples'
        ]):
            return

        # Собираем данные тестов
        if self.in_pre:
            if self.collecting_input:
                if data.strip():
                    # Обрабатываем строки с переносами
                    lines = data.replace('\r\n', '\n').split('\n')
                    for i, line in enumerate(lines):
                        if line.strip():
                            self.current_input.append(line.strip())
                            if i < len(lines) - 1 and lines[i + 1].strip():
                                self.current_input.append('<br>')

            elif self.collecting_output:
                if data.strip():
                    lines = data.replace('\r\n', '\n').split('\n')
                    for i, line in enumerate(lines):
                        if line.strip():
                            self.current_output.append(line.strip())
                            if i < len(lines) - 1 and lines[i + 1].strip():
                                self.current_output.append('<br>')

        # Собираем текст других секций
        elif self.in_paragraph:
            self.current_text.append(data)

        # Обработка заголовка
        elif self.in_title and re.match(r'^[A-F]\.\s+', data.strip()):
            self.problem_data['title'] = data.strip()

        # Обработка ограничений по времени
        elif self.current_section == 'time_limit':
            time_match = re.search(r'(\d+)\s*(second|sec|s)', data, re.IGNORECASE)
            if time_match:
                num = time_match.group(1)
                unit = 'seconds' if int(num) != 1 else 'second'
                self.problem_data['time_limit'] = f"{num} {unit}"

        # Обработка ограничений по памяти
        elif self.current_section == 'memory_limit':
            memory_match = re.search(r'(\d+)\s*(megabyte|mb|mebibyte|mib)', data, re.IGNORECASE)
            if memory_match:
                num = memory_match.group(1)
                self.problem_data['memory_limit'] = f"{num} MB"


def parse_problem_sync(contest_id, problem_id):
    """Синхронный парсинг задачи с Codeforces"""
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"

    print(f"Загружаем задачу {problem_id} из контеста {contest_id}...")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html_content = response.read().decode('utf-8')

        # Парсим с помощью нашего парсера
        parser = CodeforcesProblemParser()
        parser.feed(html_content)

        problem_data = parser.problem_data

        # Используем BeautifulSoup для извлечения тестов
        if not problem_data['samples']:
            print("Используем BeautifulSoup для извлечения тестов...")
            problem_data['samples'] = extract_tests_with_bs4(html_content)
        else:
            print(f"Парсер нашел {len(problem_data['samples'])} тестов")

        # Если все еще нет тестов, используем старый метод как запасной вариант
        if not problem_data['samples']:
            print("BeautifulSoup не нашел тестов, используем старый метод...")
            problem_data['samples'] = extract_tests_directly(html_content)

        # Если не нашли заголовок
        if not problem_data['title']:
            title_match = re.search(r'<div class="title">([A-F])\.\s*(.*?)</div>', html_content)
            if title_match:
                problem_data['title'] = f"{title_match.group(1)}. {html.unescape(title_match.group(2).strip())}"

        # Если не нашли ограничения по времени
        if not problem_data['time_limit']:
            time_match = re.search(r'<div class="time-limit">.*?(\d+)\s*(second|sec|s)',
                                   html_content, re.IGNORECASE | re.DOTALL)
            if time_match:
                num = time_match.group(1)
                unit = 'seconds' if int(num) != 1 else 'second'
                problem_data['time_limit'] = f"{num} {unit}"

        # Если не нашли ограничения по памяти
        if not problem_data['memory_limit']:
            memory_match = re.search(r'<div class="memory-limit">.*?(\d+)\s*(megabyte|mb|mebibyte|mib)',
                                     html_content, re.IGNORECASE | re.DOTALL)
            if memory_match:
                num = memory_match.group(1)
                problem_data['memory_limit'] = f"{num} MB"

        # Если не нашли statement
        if not problem_data['statement']:
            statement_match = re.search(r'<div class="problem-statement">(.*?)<div class="input-specification">',
                                        html_content, re.DOTALL)
            if statement_match:
                statement_html = statement_match.group(1)
                # Убираем заголовок и ограничения
                statement_html = re.sub(r'<div class="title">.*?</div>', '', statement_html, re.DOTALL)
                statement_html = re.sub(r'<div class="time-limit">.*?</div>', '', statement_html, re.DOTALL)
                statement_html = re.sub(r'<div class="memory-limit">.*?</div>', '', statement_html, re.DOTALL)

                # Ищем параграфы
                paragraphs = re.findall(r'<p>(.*?)</p>', statement_html, re.DOTALL)
                for para in paragraphs:
                    para_text = re.sub(r'<[^>]+>', ' ', para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = html.unescape(para_text).strip()
                    if para_text:
                        problem_data['statement'].append(para_text)

        # Если не нашли input_spec
        if not problem_data['input_spec']:
            input_match = re.search(
                r'<div class="input-specification">.*?<div class="section-title">.*?</div>(.*?)</div>',
                html_content, re.DOTALL)
            if input_match:
                input_html = input_match.group(1)
                paragraphs = re.findall(r'<p>(.*?)</p>', input_html, re.DOTALL)
                for para in paragraphs:
                    para_text = re.sub(r'<[^>]+>', ' ', para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = html.unescape(para_text).strip()
                    if para_text:
                        problem_data['input_spec'].append(para_text)

        # Если не нашли output_spec
        if not problem_data['output_spec']:
            output_match = re.search(
                r'<div class="output-specification">.*?<div class="section-title">.*?</div>(.*?)</div>',
                html_content, re.DOTALL)
            if output_match:
                output_html = output_match.group(1)
                paragraphs = re.findall(r'<p>(.*?)</p>', output_html, re.DOTALL)
                for para in paragraphs:
                    para_text = re.sub(r'<[^>]+>', ' ', para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = html.unescape(para_text).strip()
                    if para_text:
                        problem_data['output_spec'].append(para_text)

        # Если не нашли note
        if not problem_data['note']:
            note_match = re.search(r'<div class="note">.*?<div class="section-title">.*?</div>(.*?)</div>',
                                   html_content, re.DOTALL)
            if note_match:
                note_html = note_match.group(1)
                paragraphs = re.findall(r'<p>(.*?)</p>', note_html, re.DOTALL)
                for para in paragraphs:
                    para_text = re.sub(r'<[^>]+>', ' ', para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = html.unescape(para_text).strip()
                    if para_text:
                        problem_data['note'].append(para_text)

        # Очищаем raw_text от дубликатов
        if problem_data['raw_text']:
            # Убираем повторяющиеся фразы
            sentences = problem_data['raw_text'].split('. ')
            unique_sentences = []
            seen = set()
            for sentence in sentences:
                if sentence.strip() and sentence.strip() not in seen:
                    seen.add(sentence.strip())
                    unique_sentences.append(sentence.strip())
            problem_data['raw_text'] = '. '.join(unique_sentences)

        # Убираем дубликаты тестов (оставляем максимум 3 уникальных теста)
        if problem_data['samples']:
            unique_samples = []
            seen_inputs = set()
            for sample in problem_data['samples']:
                input_text = sample['input'].strip()
                if input_text and input_text not in seen_inputs:
                    seen_inputs.add(input_text)
                    unique_samples.append(sample)

            # Оставляем только первые 3 уникальных теста
            problem_data['samples'] = unique_samples[:3]

        return problem_data

    except Exception as e:
        print(f"Ошибка при загрузке задачи: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def extract_tests_with_bs4(html_content):
    """Извлекает тесты с помощью BeautifulSoup"""
    samples = []

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Найти все блоки с тестами
        test_blocks = soup.find_all("div", class_="sample-test")

        if not test_blocks:
            print("Не найдены блоки с тестами sample-test")
            return samples

        print(f"Найдено блоков с тестами: {len(test_blocks)}")

        for block_idx, block in enumerate(test_blocks, 1):
            # Найти все блоки input и output внутри sample-test
            input_divs = block.find_all("div", class_="input")
            output_divs = block.find_all("div", class_="output")

            if not input_divs or not output_divs:
                print(f"В блоке {block_idx} не найдены input/output divs")
                continue

            print(f"В блоке {block_idx} найдено input: {len(input_divs)}, output: {len(output_divs)}")

            # Обрабатываем пары input/output
            for i, (inp_div, out_div) in enumerate(zip(input_divs, output_divs)):
                # Находим pre теги внутри input/output
                inp_pre = inp_div.find("pre")
                out_pre = out_div.find("pre")

                if not inp_pre or not out_pre:
                    print(f"  В тесте {i + 1} не найдены pre теги")
                    continue

                # Получаем текст из pre тегов
                input_text = get_pre_content(inp_pre)
                output_text = get_pre_content(out_pre)

                if input_text and output_text:
                    samples.append({
                        'input': input_text,
                        'output': output_text
                    })
                    print(f"  Тест {i + 1} добавлен")

    except Exception as e:
        print(f"Ошибка при извлечении тестов с BeautifulSoup: {e}")

    return samples


def get_pre_content(pre_tag):
    """Получает содержимое pre тега в правильном формате"""
    try:
        # Если есть div с классом test-example-line
        test_lines = pre_tag.find_all("div", class_=re.compile("test-example-line"))
        if test_lines:
            lines = []
            for line_div in test_lines:
                line_text = line_div.get_text(strip=True)
                if line_text:
                    lines.append(line_text)
            return '<br>'.join(lines)

        # Обычный текст в pre теге
        # Используем get_text с separator для сохранения структуры
        text = pre_tag.get_text("\n")

        # Разбиваем на строки, очищаем
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)

        return '<br>'.join(lines)

    except Exception as e:
        print(f"Ошибка при обработке pre тега: {e}")
        return ""


def extract_tests_directly(html_content):
    """Прямое извлечение тестов из HTML с помощью регулярных выражений (запасной вариант)"""
    samples = []

    print("Запасной метод извлечения тестов...")

    # Находим секцию с тестами
    sample_section_match = re.search(r'<div class="sample-tests">(.*?)</div>\s*</div>', html_content, re.DOTALL)

    if not sample_section_match:
        print("Не найдена секция с тестами")
        return samples

    sample_section = sample_section_match.group(1)

    # Находим все блоки с тестами
    test_blocks = re.findall(r'<div class="sample-test">(.*?)</div>\s*</div>', sample_section, re.DOTALL)

    if not test_blocks:
        print("Не найдены блоки с тестами, пробуем другой формат...")
        # Пробуем найти отдельные input и output блоки
        return extract_separate_input_output(sample_section)

    print(f"Найдено блоков с тестами: {len(test_blocks)}")

    for i, test_block in enumerate(test_blocks, 1):
        # Извлекаем input
        input_match = re.search(r'<div class="input">.*?<pre.*?>(.*?)</pre>', test_block, re.DOTALL)
        output_match = re.search(r'<div class="output">.*?<pre.*?>(.*?)</pre>', test_block, re.DOTALL)

        if not input_match or not output_match:
            print(f"Не найден input или output в блоке {i}")
            continue

        input_html = input_match.group(1)
        output_html = output_match.group(1)

        # Обрабатываем input
        input_text = process_test_content(input_html)
        output_text = process_test_content(output_html)

        if input_text and output_text:
            samples.append({
                'input': input_text,
                'output': output_text
            })
            print(f"Добавлен тест {i}")

    return samples


def extract_separate_input_output(sample_section):
    """Извлекает тесты из отдельных input/output блоков"""
    samples = []

    # Находим все input блоки
    input_blocks = re.findall(r'<div class="input">(.*?)</div>', sample_section, re.DOTALL)
    output_blocks = re.findall(r'<div class="output">(.*?)</div>', sample_section, re.DOTALL)

    print(f"Найдено input блоков: {len(input_blocks)}, output блоков: {len(output_blocks)}")

    for i in range(min(len(input_blocks), len(output_blocks))):
        input_block = input_blocks[i]
        output_block = output_blocks[i]

        # Извлекаем содержимое из pre тега
        input_pre_match = re.search(r'<pre.*?>(.*?)</pre>', input_block, re.DOTALL)
        output_pre_match = re.search(r'<pre.*?>(.*?)</pre>', output_block, re.DOTALL)

        if not input_pre_match or not output_pre_match:
            print(f"Не найден pre тег в блоке {i + 1}")
            continue

        input_html = input_pre_match.group(1)
        output_html = output_pre_match.group(1)

        # Обрабатываем содержимое
        input_text = process_test_content(input_html)
        output_text = process_test_content(output_html)

        if input_text and output_text:
            samples.append({
                'input': input_text,
                'output': output_text
            })
            print(f"Добавлен тест {i + 1} из отдельных блоков")

    return samples


def process_test_content(html_content):
    """Обрабатывает содержимое теста (input или output)"""
    # Если есть div с классом test-example-line
    if 'test-example-line' in html_content:
        return process_test_example_lines(html_content)

    # Обычный текст в pre теге
    # Удаляем все HTML теги
    text = re.sub(r'<[^>]+>', '', html_content)
    # Декодируем HTML сущности
    text = html.unescape(text)
    # Убираем лишние пробелы и переносы
    text = text.strip()
    # Разбиваем на строки
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Объединяем обратно с <br>
    return '<br>'.join(lines)


def process_test_example_lines(html_content):
    """Обрабатывает формат с test-example-line"""
    lines_by_number = {}

    # Ищем все строки с test-example-line
    line_pattern = r'<div[^>]*class="[^"]*test-example-line[^"]*"[^>]*>(.*?)</div>'
    line_matches = re.findall(line_pattern, html_content, re.DOTALL)

    for i, line_html in enumerate(line_matches):
        # Извлекаем номер строки из класса
        num_match = re.search(r'test-example-line-(\d+)', html_content)
        line_num = num_match.group(1) if num_match else str(i)

        # Очищаем содержимое
        line_text = re.sub(r'<[^>]+>', '', line_html)
        line_text = html.unescape(line_text).strip()

        if line_num not in lines_by_number:
            lines_by_number[line_num] = []

        lines_by_number[line_num].append(line_text)

    # Формируем результат
    result_lines = []
    for line_num in sorted(lines_by_number.keys()):
        line_group = lines_by_number[line_num]
        # Если все части пустые, пропускаем
        if any(part for part in line_group):
            result_lines.append(' '.join(line_group))

    return '<br>'.join(result_lines)


def create_react_friendly_json(problem_data, contest_id, problem_id):
    """Создает JSON файл, удобный для использования в React.js"""
    if not problem_data:
        return None

    # Создаем объект tests (максимум 3 теста)
    tests_dict = {}
    for i, sample in enumerate(problem_data['samples'][:3], 1):
        input_text = sample['input']
        output_text = sample['output']

        # Очистка текста
        input_text = clean_test_text(input_text)
        output_text = clean_test_text(output_text)

        tests_dict[f'test{i}'] = {
            'input': input_text,
            'output': output_text
        }

    # Форматируем данные для React
    output_data = {
        'metadata': {
            'contest_id': contest_id,
            'problem_id': problem_id,
            'title': problem_data['title'],
            'time_limit': problem_data.get('time_limit', ''),
            'memory_limit': problem_data.get('memory_limit', ''),
            'header': f"{problem_data['title']}<br>Ограничение по времени: {problem_data.get('time_limit', '')} | Ограничение по памяти: {problem_data.get('memory_limit', '')}"
        },

        'content': {
            'task': '<br><br>'.join(problem_data['statement']),
            'input': '<br><br>'.join(problem_data['input_spec']),
            'output': '<br><br>'.join(problem_data['output_spec']),
        },

        'tests': tests_dict,

        'raw': {
            'raw_text': problem_data.get('raw_text', ''),
            'statement_paragraphs': problem_data['statement'],
            'input_paragraphs': problem_data['input_spec'],
            'output_paragraphs': problem_data['output_spec'],
            'note_paragraphs': problem_data['note']
        }
    }

    # Добавляем примечание
    if problem_data['note']:
        output_data['content']['note'] = '<br><br>'.join(problem_data['note'])
        output_data['raw']['note_paragraphs'] = problem_data['note']

    return output_data


def clean_test_text(text):
    """Очищает текст теста"""
    if not text:
        return ''

    # Убираем <br> в начале и конце
    while text.startswith('<br>'):
        text = text[4:]
    while text.endswith('<br>'):
        text = text[:-4]

    # Разбиваем на строки и убираем пустые
    lines = [line.strip() for line in text.split('<br>') if line.strip()]

    return '<br>'.join(lines)


# ==================== АСИНХРОННЫЕ ВЕРСИИ ПАРСЕРА ====================

async def parse_problem_async(contest_id: int, problem_id: str) -> Dict[str, Any]:
    """Асинхронный парсинг задачи (обертка над синхронным)"""
    try:
        loop = asyncio.get_event_loop()
        problem_data = await loop.run_in_executor(None, parse_problem_sync, contest_id, problem_id)
        return problem_data
    except Exception as e:
        print(f"Ошибка в асинхронном парсере: {e}")
        return None


async def get_problem_json(contest_id: int, problem_id: str) -> Dict[str, Any]:
    """Получить задачу в JSON формате"""
    print(f"🔍 Парсинг задачи {contest_id}{problem_id}...")

    problem_data = await parse_problem_async(contest_id, problem_id)

    if not problem_data:
        print(f"❌ Не удалось распарсить {contest_id}{problem_id}")
        # Fallback структура
        return {
            'metadata': {
                'contest_id': str(contest_id),
                'problem_id': problem_id,
                'title': f"Problem {problem_id}",
                'time_limit': '2 seconds',
                'memory_limit': '256 MB',
                'header': f"Problem {problem_id}<br>Ограничение по времени: 2 seconds | Ограничение по памяти: 256 MB"
            },
            'content': {
                'task': '',
                'input': '',
                'output': '',
                'note': ''
            },
            'tests': {},
            'raw': {
                'raw_text': '',
                'statement_paragraphs': [],
                'input_paragraphs': [],
                'output_paragraphs': [],
                'note_paragraphs': []
            },
            'status': 'error',
            'error': 'Failed to parse problem',
            'is_fallback': True
        }

    print(f"✅ Успешно распарсена {contest_id}{problem_id}: {problem_data.get('title', 'Без заголовка')}")
    print(f"📊 Найдено тестов: {len(problem_data['samples'])}")

    # Создаем JSON в формате React
    result = create_react_friendly_json(problem_data, contest_id, problem_id)

    # Добавляем статус
    if result:
        result['status'] = 'success'
        result['parsed_at'] = datetime.now().isoformat()

    return result


# ==================== УЛУЧШЕННЫЙ MISTRAL AI ПЕРЕВОДЧИК ====================

class EnhancedMistralTranslator:
    """Улучшенный переводчик задач с полным переводом всех полей"""

    def __init__(self):
        if not mistral_client:
            raise ValueError("Mistral AI не инициализирован")

    async def translate_full_problem(self, problem_data: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Перевести всю задачу полностью"""
        try:
            # Создаем глубокую копию
            import copy
            translated_problem = copy.deepcopy(problem_data)

            # Переводим каждое поле отдельно
            if target_language == "ru":
                # Заголовок
                if 'metadata' in translated_problem and 'title' in translated_problem['metadata']:
                    title = translated_problem['metadata']['title']
                    translated_title = await self._translate_title(title, target_language)
                    translated_problem['metadata']['title'] = translated_title
                    # Обновляем header
                    if 'header' in translated_problem['metadata']:
                        translated_problem['metadata']['header'] = translated_problem['metadata']['header'].replace(
                            title, translated_title)

                # Условие задачи
                if 'content' in translated_problem and 'task' in translated_problem['content']:
                    translated_task = await self._translate_text(translated_problem['content']['task'], target_language,
                                                                 "condition")
                    translated_problem['content']['task'] = translated_task

                # Входные данные
                if 'content' in translated_problem and 'input' in translated_problem['content']:
                    translated_input = await self._translate_text(translated_problem['content']['input'],
                                                                  target_language, "input_spec")
                    translated_problem['content']['input'] = translated_input

                # Выходные данные
                if 'content' in translated_problem and 'output' in translated_problem['content']:
                    translated_output = await self._translate_text(translated_problem['content']['output'],
                                                                   target_language, "output_spec")
                    translated_problem['content']['output'] = translated_output

                # Примечания
                if 'content' in translated_problem and 'note' in translated_problem['content']:
                    translated_note = await self._translate_text(translated_problem['content']['note'], target_language,
                                                                 "note")
                    translated_problem['content']['note'] = translated_note

                # Raw тексты
                if 'raw' in translated_problem:
                    # Параграфы условия
                    if 'statement_paragraphs' in translated_problem['raw']:
                        translated_paragraphs = []
                        for paragraph in translated_problem['raw']['statement_paragraphs']:
                            translated_para = await self._translate_text(paragraph, target_language, "paragraph")
                            translated_paragraphs.append(translated_para)
                        translated_problem['raw']['statement_paragraphs'] = translated_paragraphs

                    # Параграфы входных данных
                    if 'input_paragraphs' in translated_problem['raw']:
                        translated_paragraphs = []
                        for paragraph in translated_problem['raw']['input_paragraphs']:
                            translated_para = await self._translate_text(paragraph, target_language, "input_paragraph")
                            translated_paragraphs.append(translated_para)
                        translated_problem['raw']['input_paragraphs'] = translated_paragraphs

                    # Параграфы выходных данных
                    if 'output_paragraphs' in translated_problem['raw']:
                        translated_paragraphs = []
                        for paragraph in translated_problem['raw']['output_paragraphs']:
                            translated_para = await self._translate_text(paragraph, target_language, "output_paragraph")
                            translated_paragraphs.append(translated_para)
                        translated_problem['raw']['output_paragraphs'] = translated_paragraphs

                    # Параграфы примечаний
                    if 'note_paragraphs' in translated_problem['raw']:
                        translated_paragraphs = []
                        for paragraph in translated_problem['raw']['note_paragraphs']:
                            translated_para = await self._translate_text(paragraph, target_language, "note_paragraph")
                            translated_paragraphs.append(translated_para)
                        translated_problem['raw']['note_paragraphs'] = translated_paragraphs

                    # Raw text
                    if 'raw_text' in translated_problem['raw']:
                        translated_raw = await self._translate_text(translated_problem['raw']['raw_text'],
                                                                    target_language, "raw_text")
                        translated_problem['raw']['raw_text'] = translated_raw

                # Ограничения по времени
                if 'metadata' in translated_problem and 'time_limit' in translated_problem['metadata']:
                    time_limit = translated_problem['metadata']['time_limit']
                    if 'second' in time_limit.lower():
                        translated_problem['metadata']['time_limit'] = time_limit.replace('second', 'секунда').replace(
                            'seconds', 'секунд')

                # Ограничения по памяти
                if 'metadata' in translated_problem and 'memory_limit' in translated_problem['metadata']:
                    memory_limit = translated_problem['metadata']['memory_limit']
                    if 'mb' in memory_limit.lower():
                        translated_problem['metadata']['memory_limit'] = memory_limit.replace('MB', 'МБ')

            return translated_problem

        except Exception as e:
            print(f"❌ Ошибка полного перевода: {e}")
            return problem_data

    async def _translate_title(self, title: str, target_language: str) -> str:
        """Перевести заголовок задачи"""
        try:
            # Извлекаем букву задачи и название
            match = re.match(r'^([A-F])\.\s+(.+)$', title)
            if not match:
                return title

            problem_letter = match.group(1)
            english_title = match.group(2)

            prompt = f"""Переведи название задачи с Codeforces на {target_language}. 

Оригинальное название: "{english_title}"

Верни ТОЛЬКО переведенное название, без буквы задачи и без дополнительного текста."""

            response = mistral_client.chat.complete(
                model=APIConfig.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=APIConfig.MISTRAL_TEMPERATURE,
                max_tokens=100
            )

            translated_name = response.choices[0].message.content.strip()

            # Убираем кавычки если есть
            translated_name = translated_name.strip('"\'')

            return f"{problem_letter}. {translated_name}"

        except Exception as e:
            print(f"Ошибка перевода заголовка: {e}")
            return title

    async def _translate_text(self, text: str, target_language: str, context: str = "general") -> str:
        """Перевести текст с сохранением специальных элементов"""
        if not text or not text.strip():
            return text

        try:
            # Подготовка промпта в зависимости от контекста
            if context == "condition":
                instruction = "Ты - эксперт по спортивному программированию. Переведи условие задачи с Codeforces."
            elif context in ["input_spec", "output_spec"]:
                instruction = "Ты - технический переводчик. Переведи спецификацию входных/выходных данных задачи."
            elif context in ["note", "note_paragraph"]:
                instruction = "Ты - технический переводчик. Переведи примечание к задаче."
            else:
                instruction = "Ты - профессиональный технический переводчик."

            prompt = f"""{instruction}

ПЕРЕВЕДИ СЛЕДУЮЩИЙ ТЕКСТ НА {target_language.upper()}:

ВАЖНЫЕ ПРАВИЛА:
1. Сохрани ВСЕ математические формулы и обозначения БЕЗ ИЗМЕНЕНИЙ
2. Сохрани имена переменных (n, m, w, t, a_i и т.д.) БЕЗ ИЗМЕНЕНИЙ
3. Сохрани специальные термины типа "i-th" и переведи их правильно ("i-ый" для русского)
4. Сохрани все числовые значения и единицы измерения
5. Сохрани форматирование (абзацы, переносы строк)
6. Технические термины переведи точно: "input" → "входные данные", "output" → "выходные данные"

ТЕКСТ ДЛЯ ПЕРЕВОДА:
{text}

Верни ТОЛЬКО переведенный текст, без дополнительных объяснений."""

            response = mistral_client.chat.complete(
                model=APIConfig.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=APIConfig.MISTRAL_TEMPERATURE,
                max_tokens=min(len(text) * 2, APIConfig.MISTRAL_MAX_TOKENS)
            )

            translated = response.choices[0].message.content.strip()

            # Пост-обработка
            translated = self._post_process_translation(translated, text)

            return translated

        except Exception as e:
            print(f"Ошибка перевода текста ({context}): {e}")
            return text

    def _post_process_translation(self, translated: str, original: str) -> str:
        """Пост-обработка перевода для сохранения критических элементов"""
        # Сохраняем математические обозначения
        math_patterns = [
            (r'(\d+)\s*≤\s*([a-zA-Z_]+)\s*≤\s*(\d+)', r'\1 ≤ \2 ≤ \3'),
            (r'(\d+)\s*≤\s*([a-zA-Z_]+[₀₁₂₃₄₅₆₇₈₉]?)\s*≤\s*(\d+)', r'\1 ≤ \2 ≤ \3'),
            (r'([a-zA-Z_])\s*=\s*([^,;\n]+)', r'\1 = \2'),
            (r'([a-zA-Z_]+)\s*\+\s*([a-zA-Z_]+)', r'\1 + \2'),
            (r'([a-zA-Z_]+)\s*-\s*([a-zA-Z_]+)', r'\1 - \2'),
            (r'([a-zA-Z_]+)\s*\*\s*([a-zA-Z_]+)', r'\1 * \2'),
        ]

        for pattern, replacement in math_patterns:
            translated = re.sub(pattern, replacement, translated)

        # Сохраняем теги <br>
        if '<br>' in original:
            # Заменяем переносы строк на <br> если они были в оригинале
            lines = translated.split('\n')
            if len(lines) > 1:
                translated = '<br>'.join(lines)

        return translated

    async def analyze_translation_quality(self, original_problem: Dict[str, Any],
                                          translated_problem: Dict[str, Any],
                                          target_language: str) -> Dict[str, Any]:
        """Анализировать качество перевода"""
        try:
            # Подготавливаем данные для анализа
            original_fields = self._extract_fields_for_analysis(original_problem)
            translated_fields = self._extract_fields_for_analysis(translated_problem)

            prompt = f"""Ты - эксперт по оценке качества технических переводов.

Проанализируй качество перевода задачи с Codeforces с английского на {target_language}.

КОМПОНЕНТЫ ДЛЯ АНАЛИЗА:

1. ЗАГОЛОВОК:
   Оригинал: {original_fields.get('title', 'N/A')}
   Перевод: {translated_fields.get('title', 'N/A')}

2. УСЛОВИЕ ЗАДАЧИ:
   Оригинал: {original_fields.get('task_preview', 'N/A')}
   Перевод: {translated_fields.get('task_preview', 'N/A')}

3. ВХОДНЫЕ ДАННЫЕ:
   Оригинал: {original_fields.get('input_preview', 'N/A')}
   Перевод: {translated_fields.get('input_preview', 'N/A')}

4. ВЫХОДНЫЕ ДАННЫЕ:
   Оригинал: {original_fields.get('output_preview', 'N/A')}
   Перевод: {translated_fields.get('output_preview', 'N/A')}

5. ПРИМЕЧАНИЯ:
   Оригинал: {original_fields.get('note_preview', 'N/A')}
   Перевод: {translated_fields.get('note_preview', 'N/A')}

ОЦЕНИ ПО КАЖДОМУ КРИТЕРИЮ (0.0-1.0):
1. Точность перевода технических терминов
2. Сохранение математических формул и обозначений
3. Сохранение имен переменных
4. Естественность языка перевода
5. Полнота перевода (все ли компоненты переведены)

Ответь в формате JSON:
{{
    "overall_score": 0.95,
    "technical_terms_score": 0.9,
    "formulas_preservation_score": 1.0,
    "variables_preservation_score": 0.95,
    "language_naturalness_score": 0.9,
    "completeness_score": 1.0,
    "translated_components": ["title", "task", "input", "output", "note"],
    "missing_translations": [],
    "strengths": ["точность формул", "естественный язык"],
    "weaknesses": ["некоторые термины переведены неточно"],
    "improvement_suggestions": ["использовать более точные технические термины"]
}}"""

            response = mistral_client.chat.complete(
                model=APIConfig.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=APIConfig.MISTRAL_TEMPERATURE,
                max_tokens=APIConfig.MISTRAL_MAX_TOKENS
            )

            analysis_text = response.choices[0].message.content

            # Парсим JSON
            try:
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = self._create_fallback_analysis()
            except:
                analysis = self._create_fallback_analysis()

            return analysis

        except Exception as e:
            print(f"❌ Ошибка анализа качества: {e}")
            return self._create_fallback_analysis()

    def _extract_fields_for_analysis(self, problem_data: Dict[str, Any]) -> Dict[str, str]:
        """Извлечь поля для анализа"""
        fields = {}

        # Заголовок
        if 'metadata' in problem_data and 'title' in problem_data['metadata']:
            fields['title'] = problem_data['metadata']['title'][:100]

        # Условие (превью)
        if 'content' in problem_data and 'task' in problem_data['content']:
            task = problem_data['content']['task']
            fields['task_preview'] = task[:200] + "..." if len(task) > 200 else task

        # Входные данные (превью)
        if 'content' in problem_data and 'input' in problem_data['content']:
            input_spec = problem_data['content']['input']
            fields['input_preview'] = input_spec[:150] + "..." if len(input_spec) > 150 else input_spec

        # Выходные данные (превью)
        if 'content' in problem_data and 'output' in problem_data['content']:
            output_spec = problem_data['content']['output']
            fields['output_preview'] = output_spec[:150] + "..." if len(output_spec) > 150 else output_spec

        # Примечания (превью)
        if 'content' in problem_data and 'note' in problem_data['content']:
            note = problem_data['content']['note']
            fields['note_preview'] = note[:150] + "..." if len(note) > 150 else note

        return fields

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Создать fallback анализ"""
        return {
            "overall_score": 0.7,
            "technical_terms_score": 0.7,
            "formulas_preservation_score": 0.8,
            "variables_preservation_score": 0.9,
            "language_naturalness_score": 0.7,
            "completeness_score": 0.6,
            "translated_components": [],
            "missing_translations": [],
            "strengths": ["Базовый перевод выполнен"],
            "weaknesses": ["Требуется более точный анализ"],
            "improvement_suggestions": ["Проверить полноту перевода всех полей"]
        }


# ==================== MISTRAL AI ГЕНЕРАТОР КОНТЕСТОВ ====================

class MistralContestGenerator:
    """Генератор контестов с Mistral AI"""

    def __init__(self):
        if not mistral_client:
            raise ValueError("Mistral AI не инициализирован")

    async def generate_contest(self, difficulty: int, topic: str, problem_count: int,
                               user_query: str) -> List[Dict[str, Any]]:
        """Сгенерировать контест с помощью Mistral AI"""
        try:
            # Получаем информацию о сложности
            difficulty_info = ContestConfig.get_difficulty_info(difficulty)
            topic_info = ContestConfig.CF_TOPICS.get(topic, {"name": topic, "description": ""})

            prompt = f"""Ты - опытный тренер по спортивному программированию на Codeforces.

Пользователь запросил: "{user_query}"

Параметры контеста:
- Уровень сложности: {difficulty_info['label']} (рейтинг {difficulty_info['min_rating']}-{difficulty_info['max_rating']})
- Тема: {topic_info['name']}
- Количество задач: {problem_count}

Подбери реальные существующие задачи с Codeforces, которые:
1. Соответствуют указанной теме "{topic}"
2. Подходят по сложности (рейтинг {difficulty_info['min_rating']}-{difficulty_info['max_rating']})
3. Имеют логическую последовательность от простого к сложному
4. Развивают разные аспекты указанной темы
5. Имеют реальные URL на Codeforces

Верни ответ в формате JSON с массивом задач:
{{
    "problems": [
        {{
            "contest_id": 4,
            "problem_id": "A",
            "title": "Watermelon",
            "rating": 800,
            "reasoning": "Простая задача на проверку четности, подходит для начинающих",
            "relevance_score": 0.9,
            "url": "https://codeforces.com/problemset/problem/4/A"
        }},
        {{
            "contest_id": 500,
            "problem_id": "A",
            "title": "New Year Transportation",
            "rating": 1000,
            "reasoning": "Задача на обход графа, соответствует теме графов",
            "relevance_score": 0.85,
            "url": "https://codeforces.com/problemset/problem/500/A"
        }}
    ]
}}

Убедись, что задачи действительно существуют на Codeforces и URL корректны!"""

            response = mistral_client.chat.complete(
                model=APIConfig.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=APIConfig.MISTRAL_TEMPERATURE,
                max_tokens=APIConfig.MISTRAL_MAX_TOKENS
            )

            response_text = response.choices[0].message.content

            # Парсим JSON из ответа
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    problems = result.get("problems", [])
                else:
                    problems = []
            except:
                problems = []

            # Если Mistral не нашел задачи, используем fallback
            if not problems:
                problems = self._get_fallback_problems(topic, difficulty, problem_count)

            return problems

        except Exception as e:
            print(f"❌ Ошибка генерации контеста: {e}")
            return self._get_fallback_problems(topic, difficulty, problem_count)

    def _get_fallback_problems(self, topic: str, difficulty: int, problem_count: int) -> List[Dict[str, Any]]:
        """Получить fallback задачи"""
        fallback_problems = {
            "dp": [
                {"contest_id": 455, "problem_id": "A", "title": "Boredom", "rating": 1500,
                 "reasoning": "Классическая задача на динамическое программирование", "relevance_score": 0.8},
                {"contest_id": 489, "problem_id": "C", "title": "Given Length and Sum of Digits...", "rating": 1400,
                 "reasoning": "Задача на динамику по цифрам", "relevance_score": 0.7},
            ],
            "graphs": [
                {"contest_id": 500, "problem_id": "A", "title": "New Year Transportation", "rating": 1000,
                 "reasoning": "Задача на обход графа, подходит для начинающих", "relevance_score": 0.9},
                {"contest_id": 520, "problem_id": "B", "title": "Two Buttons", "rating": 1400,
                 "reasoning": "Задача на BFS по числам", "relevance_score": 0.8},
            ],
            "math": [
                {"contest_id": 1, "problem_id": "A", "title": "Theatre Square", "rating": 1000,
                 "reasoning": "Базовая математическая задача", "relevance_score": 0.9},
                {"contest_id": 4, "problem_id": "A", "title": "Watermelon", "rating": 800,
                 "reasoning": "Классическая задача на четность", "relevance_score": 0.9},
            ],
            "implementation": [
                {"contest_id": 4, "problem_id": "A", "title": "Watermelon", "rating": 800,
                 "reasoning": "Базовая задача на реализацию", "relevance_score": 0.9},
                {"contest_id": 71, "problem_id": "A", "title": "Way Too Long Words", "rating": 800,
                 "reasoning": "Задача на обработку строк", "relevance_score": 0.8},
            ],
            "greedy": [
                {"contest_id": 266, "problem_id": "A", "title": "Stones on the Table", "rating": 800,
                 "reasoning": "Простая жадная задача", "relevance_score": 0.9},
                {"contest_id": 58, "problem_id": "A", "title": "Chat room", "rating": 1000,
                 "reasoning": "Задача на жадное сопоставление", "relevance_score": 0.8},
            ]
        }

        problems = fallback_problems.get(topic, fallback_problems["implementation"])
        return problems[:problem_count]

    async def analyze_contest_relevance(self, contest_problems: List[Dict[str, Any]],
                                        user_query: str, topic: str, difficulty: int) -> Dict[str, Any]:
        """Проанализировать релевантность контеста"""
        try:
            problems_text = "\n".join([
                f"{i + 1}. {p.get('title', 'Unknown')} (рейтинг: {p.get('rating', 'N/A')}) - {p.get('reasoning', '')}"
                for i, p in enumerate(contest_problems)
            ])

            prompt = f"""Ты - эксперт по подготовке к спортивному программированию.

Проанализируй, насколько хорошо подобранные задачи соответствуют запросу пользователя.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: "{user_query}"
ТЕМА: {topic}
УРОВЕНЬ СЛОЖНОСТИ: {difficulty}

ПОДОБРАННЫЕ ЗАДАЧИ:
{problems_text}

Оцени:
1. Соответствие теме
2. Соответствие уровню сложности
3. Логическую последовательность задач
4. Баланс между разными аспектами темы
5. Общую полезность для тренировки

Ответь в формате JSON:
{{
    "overall_relevance_score": 0.9,
    "topic_match_score": 0.95,
    "difficulty_match_score": 0.85,
    "progression_score": 0.9,
    "balance_score": 0.8,
    "usefulness_score": 0.9,
    "strengths": ["отличное соответствие теме", "хорошая прогрессия сложности"],
    "weaknesses": ["недостаточно задач на продвинутые аспекты темы"],
    "recommendations": ["добавить задачу на конкретный аспект X", "убрать слишком простую задачу Y"]
}}"""

            response = mistral_client.chat.complete(
                model=APIConfig.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=APIConfig.MISTRAL_TEMPERATURE,
                max_tokens=APIConfig.MISTRAL_MAX_TOKENS
            )

            analysis_text = response.choices[0].message.content

            # Парсим JSON из ответа
            try:
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = self._create_fallback_analysis()
            except:
                analysis = self._create_fallback_analysis()

            return analysis

        except Exception as e:
            print(f"❌ Ошибка анализа релевантности: {e}")
            return self._create_fallback_analysis()

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Создать fallback анализ"""
        return {
            "overall_relevance_score": 0.7,
            "topic_match_score": 0.7,
            "difficulty_match_score": 0.7,
            "progression_score": 0.7,
            "balance_score": 0.7,
            "usefulness_score": 0.7,
            "strengths": ["Задачи подобраны"],
            "weaknesses": ["Требуется более точный анализ"],
            "recommendations": ["Проверить соответствие вручную"]
        }


# ==================== БАЗОВЫЕ ИНСТРУМЕНТЫ ====================

class BaseTool(ABC):
    def __init__(self):
        self.usage_count = 0

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass


class EnhancedMistralTranslatorTool(BaseTool):
    """Улучшенный переводчик задач с полным переводом"""

    def __init__(self):
        super().__init__()
        if mistral_client:
            self.translator = EnhancedMistralTranslator()
        else:
            self.translator = None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        self.usage_count += 1

        try:
            problem_json = kwargs.get("problem_json", {})
            target_language = kwargs.get("target_language", "ru")

            if not self.translator:
                return {
                    "success": False,
                    "error": "Mistral AI не инициализирован",
                    "data": self._create_fallback_translation(problem_json, target_language),
                    "execution_time": time.time() - start_time
                }

            # Переводим всю задачу
            translated_problem = await self.translator.translate_full_problem(problem_json, target_language)

            # Анализируем качество
            quality_analysis = await self.translator.analyze_translation_quality(
                problem_json, translated_problem, target_language
            )

            result = {
                "translated_problem": translated_problem,
                "target_language": target_language,
                "original_problem": problem_json,
                "quality_analysis": quality_analysis,
                "quality_score": quality_analysis.get("overall_score", 0.7),
                "translation_method": "enhanced_mistral_ai",
                "translation_complete": self._check_translation_completeness(translated_problem, problem_json)
            }

            return {
                "success": True,
                "data": result,
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            print(f"❌ Ошибка в улучшенном переводчике: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": self._create_fallback_translation(kwargs.get("problem_json", {}),
                                                          kwargs.get("target_language", "ru")),
                "execution_time": time.time() - start_time
            }

    def _check_translation_completeness(self, translated: Dict[str, Any], original: Dict[str, Any]) -> bool:
        """Проверить полноту перевода"""
        try:
            # Проверяем основные поля
            fields_to_check = [
                ('content', 'task'),
                ('content', 'input'),
                ('content', 'output'),
                ('metadata', 'title')
            ]

            for path in fields_to_check:
                original_value = original
                translated_value = translated

                for key in path:
                    if key in original_value:
                        original_value = original_value[key]
                    else:
                        original_value = None
                        break

                for key in path:
                    if key in translated_value:
                        translated_value = translated_value[key]
                    else:
                        translated_value = None
                        break

                # Если есть оригинал, но нет перевода или они одинаковые (не переведено)
                if original_value and translated_value and original_value == translated_value:
                    return False

            return True
        except:
            return False

    def _create_fallback_translation(self, problem_json: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Создать fallback перевод"""
        import copy
        translated_problem = copy.deepcopy(problem_json)

        if target_language == "ru":
            # Простой перевод заголовка
            if 'metadata' in translated_problem and 'title' in translated_problem['metadata']:
                title = translated_problem['metadata']['title']
                # Простая замена для Watermelon
                if "Watermelon" in title:
                    translated_problem['metadata']['title'] = title.replace("Watermelon", "Арбуз")

        return {
            "translated_problem": translated_problem,
            "target_language": target_language,
            "quality_score": 0.3,
            "is_fallback": True
        }


class MistralContestGeneratorTool(BaseTool):
    """Генератор контестов с Mistral AI"""

    def __init__(self):
        super().__init__()
        if mistral_client:
            self.generator = MistralContestGenerator()
        else:
            self.generator = None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        self.usage_count += 1

        try:
            difficulty = kwargs.get("difficulty", 3)
            topic = kwargs.get("topic", "implementation")
            problem_count = kwargs.get("problem_count", 5)
            user_query = kwargs.get("user_query", "")

            if not self.generator:
                return await self._generate_fallback_contest(difficulty, topic, problem_count)

            # Генерируем контест с помощью Mistral
            generated_problems = await self.generator.generate_contest(
                difficulty, topic, problem_count, user_query
            )

            # Парсим реальные задачи
            problems = []
            parsed_count = 0

            for problem_info in generated_problems:
                contest_id = problem_info.get("contest_id")
                problem_id = problem_info.get("problem_id")

                if contest_id and problem_id:
                    # Парсим задачу
                    problem_json = await get_problem_json(contest_id, problem_id)

                    parsed_successfully = (problem_json is not None and
                                           not problem_json.get('is_fallback', False))

                    if parsed_successfully:
                        parsed_count += 1

                    problems.append({
                        "contest_id": contest_id,
                        "problem_id": problem_id,
                        "title": problem_json['metadata']['title'] if problem_json else
                        problem_info.get('title', f"Problem {problem_id}"),
                        "difficulty_rating": problem_info.get('rating', 1200),
                        "topic": topic,
                        "description": problem_info.get('reasoning', ''),
                        "relevance_score": problem_info.get('relevance_score', 0.7),
                        "estimated_solve_time": 15 + (len(problems) * 5),
                        "url": f"https://codeforces.com/problemset/problem/{contest_id}/{problem_id}",
                        "problem_data": problem_json if problem_json else None,
                        "parsed_successfully": parsed_successfully
                    })

            # Анализируем релевантность
            relevance_analysis = await self.generator.analyze_contest_relevance(
                problems, user_query, topic, difficulty
            )

            # Создаем структуру контеста
            difficulty_labels = {1: "Новичок", 2: "Легкий", 3: "Средний", 4: "Сложный", 5: "Эксперт"}
            topic_names = ContestConfig.CF_TOPICS.get(topic, {"name": topic})

            contest_data = {
                "contest_title": f"{topic_names.get('name', topic)} - Контест",
                "description": f"Подборка задач по теме '{topic_names.get('name', topic)}'. Сложность: {difficulty_labels.get(difficulty, 'Средний')}",
                "difficulty": difficulty_labels.get(difficulty, "Средний"),
                "topic": topic_names.get('name', topic),
                "estimated_time_minutes": len(problems) * 25,
                "total_problems": len(problems),
                "successfully_parsed": parsed_count,
                "problems": problems,
                "relevance_analysis": relevance_analysis,
                "generation_method": "mistral_ai",
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "difficulty_numeric": difficulty,
                    "topic_original": topic,
                    "problem_count": problem_count,
                    "parsed_problems": parsed_count,
                    "is_fallback": parsed_count == 0
                }
            }

            return {
                "success": True,
                "data": contest_data,
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            print(f"❌ Ошибка в генераторе контестов: {e}")
            return await self._generate_fallback_contest(
                kwargs.get("difficulty", 3),
                kwargs.get("topic", "implementation"),
                kwargs.get("problem_count", 5)
            )

    async def _generate_fallback_contest(self, difficulty: int, topic: str, problem_count: int) -> Dict[str, Any]:
        """Создать fallback контест"""
        difficulty_labels = {1: "Новичок", 2: "Легкий", 3: "Средний", 4: "Сложный", 5: "Эксперт"}

        contest_data = {
            "contest_title": f"Резервный контест - Тема: {topic}",
            "description": "Базовый контест (режим fallback)",
            "difficulty": difficulty_labels.get(difficulty, "Средний"),
            "topic": topic,
            "estimated_time_minutes": problem_count * 20,
            "total_problems": problem_count,
            "successfully_parsed": 0,
            "problems": [
                {
                    "contest_id": 4,
                    "problem_id": "A",
                    "title": "Watermelon",
                    "difficulty_rating": 800,
                    "topic": "implementation",
                    "description": "Classic beginner problem",
                    "estimated_solve_time": 10,
                    "url": "https://codeforces.com/problemset/problem/4/A",
                    "parsed_successfully": False,
                    "note": "Fallback задача"
                }
            ],
            "relevance_analysis": {
                "overall_relevance_score": 0.5,
                "topic_match_score": 0.5,
                "difficulty_match_score": 0.5,
                "progression_score": 0.5,
                "balance_score": 0.5,
                "usefulness_score": 0.5,
                "strengths": ["Базовый контест создан"],
                "weaknesses": ["Не соответствует запросу точно"],
                "recommendations": ["Использовать Mistral AI для лучшего подбора"]
            },
            "generation_method": "fallback",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "difficulty_numeric": difficulty,
                "topic_original": topic,
                "problem_count": problem_count,
                "parsed_problems": 0,
                "is_fallback": True
            }
        }

        return {
            "success": True,
            "data": contest_data,
            "execution_time": 0.1
        }


# ==================== АНАЛИЗАТОР ЗАПРОСОВ ====================

class QueryAnalyzerTool(BaseTool):
    """Анализатор запросов"""

    async def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        self.usage_count += 1

        try:
            user_query = kwargs.get("user_query", "").lower()
            user_params = kwargs.get("user_params", {})

            # Определяем тип запроса
            request_type = "contest_generation"
            translation_keywords = ["перевод", "translate", "переведи", "translation"]
            contest_keywords = ["контест", "contest", "подбор", "задач", "тренировка", "задачи", "соревнование"]

            if any(kw in user_query for kw in translation_keywords):
                request_type = "translation"
            elif any(kw in user_query for kw in contest_keywords):
                request_type = "contest_generation"
            else:
                if "codeforces.com" in user_query or re.search(r'\d+[A-F]', user_query, re.IGNORECASE):
                    request_type = "translation"

            # Определяем язык
            target_language = user_params.get("target_language", "ru")
            if not target_language:
                if any(kw in user_query for kw in ["английский", "english", "en"]):
                    target_language = "en"
                elif any(kw in user_query for kw in ["русский", "russian", "ru"]):
                    target_language = "ru"

            # Определяем тему
            topic = user_params.get("topic", "implementation")
            topic_keywords = {
                "dp": ["дп", "динамическое", "динамика", "dp", "dynamic programming"],
                "graphs": ["граф", "графы", "graph", "dfs", "bfs", "dijkstra", "обход"],
                "math": ["математик", "math", "число", "числа", "геометр", "geometry", "алгебр"],
                "greedy": ["жад", "greedy", "жадный", "жадные"],
                "implementation": ["реализация", "implementation", "прост", "базов"],
                "strings": ["строк", "string", "подстрока", "substring", "строка"],
                "trees": ["дерево", "tree", "деревья", "дерева"],
                "binary_search": ["бинарный", "binary search", "бинпоиск", "двоичный"],
                "data_structures": ["структур", "структуры данных", "data structure", "очередь", "стек", "дерево"]
            }

            for topic_name, keywords in topic_keywords.items():
                if any(kw in user_query for kw in keywords):
                    topic = topic_name
                    break

            # Определяем сложность
            difficulty = user_params.get("difficulty", 3)
            if difficulty == 3:
                if any(kw in user_query for kw in ["нович", "начина", "легк", "easy", "простой"]):
                    difficulty = 1
                elif any(kw in user_query for kw in ["средн", "medium", "intermediate"]):
                    difficulty = 2
                elif any(kw in user_query for kw in ["сложн", "hard", "эксперт", "продвинут"]):
                    difficulty = 4
                elif any(kw in user_query for kw in ["эксперт", "expert", "мастер", "сложнейш"]):
                    difficulty = 5

            # Определяем количество задач
            problem_count = user_params.get("problem_count", 5)
            if problem_count == 5:
                numbers = re.findall(r'\b(\d+)\b', user_query)
                if numbers:
                    num = int(numbers[0])
                    if 1 <= num <= 10:
                        problem_count = num

            result = {
                "request_type": request_type,
                "parameters": {
                    "target_language": target_language,
                    "difficulty": difficulty,
                    "topic": topic,
                    "problem_count": problem_count
                },
                "confidence": 0.9,
                "reasoning": f"Определено: тип={request_type}, тема={topic}, сложность={difficulty}, язык={target_language}"
            }

            return {
                "success": True,
                "data": result,
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }


# ==================== УЛУЧШЕННЫЕ АГЕНТЫ ====================

class EnhancedTranslationAgent:
    """Улучшенный агент перевода с полным переводом всех полей"""

    def __init__(self):
        self.translator_tool = EnhancedMistralTranslatorTool() if mistral_client else None
        self.stats = {
            "total_requests": 0,
            "successful_translations": 0,
            "partial_translations": 0,
            "failed_translations": 0
        }

    def _extract_problem_id(self, query: str) -> Tuple[Optional[int], Optional[str]]:
        """Извлечь ID задачи из запроса"""
        patterns = [
            r'codeforces\.com/contest/(\d+)/problem/([A-Z])',
            r'codeforces\.com/problemset/problem/(\d+)/([A-Z])',
            r'(\d+)[\s\-/]?([A-F])',
            r'(\d+)\s*-\s*([A-F])',
            r'(\d+)/([A-F])'
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    contest_id = int(match.group(1))
                    problem_id = match.group(2).upper()
                    return contest_id, problem_id
                except:
                    continue

        return None, None

    async def run(self, user_query: str, user_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Запустить перевод задачи"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            print(f"\n🌍 ЗАПУСК УЛУЧШЕННОГО ПЕРЕВОДЧИКА")
            print(f"📝 Запрос: {user_query[:80]}...")

            # Извлекаем ID задачи
            contest_id, problem_id = self._extract_problem_id(user_query)

            if not contest_id or not problem_id:
                # Пробуем другой формат
                match = re.search(r'(\d+)\s*([A-F])', user_query, re.IGNORECASE)
                if match:
                    contest_id = int(match.group(1))
                    problem_id = match.group(2).upper()
                else:
                    return self._format_error_response(
                        "Не удалось извлечь ID задачи из запроса",
                        time.time() - start_time,
                        user_query
                    )

            # Определяем язык перевода
            target_language = "ru"
            if user_params and "target_language" in user_params:
                target_language = user_params["target_language"]
            elif "английск" in user_query.lower() or "english" in user_query.lower():
                target_language = "en"

            # Парсим задачу
            print(f"🔍 Парсинг задачи {contest_id}{problem_id}...")
            original_problem = await get_problem_json(contest_id, problem_id)

            if not original_problem or original_problem.get('is_fallback'):
                print(f"⚠️ Не удалось получить задачу, используем fallback")
                return self._format_fallback_response(target_language, contest_id, problem_id, start_time)

            # Выполняем перевод
            if self.translator_tool:
                print(f"🤖 Перевод на {target_language} с помощью Mistral AI...")
                translation_result = await self.translator_tool.execute(
                    problem_json=original_problem,
                    target_language=target_language
                )

                if translation_result.get("success"):
                    self.stats["successful_translations"] += 1
                    result_data = translation_result["data"]

                    # Проверяем полноту перевода
                    is_complete = result_data.get("translation_complete", False)
                    if not is_complete:
                        self.stats["partial_translations"] += 1
                        print(f"⚠️ Перевод выполнен частично")

                    return self._format_success_response(result_data, time.time() - start_time, is_complete)
                else:
                    self.stats["failed_translations"] += 1
                    print(f"❌ Ошибка перевода: {translation_result.get('error')}")

            # Fallback
            return self._format_fallback_response(target_language, contest_id, problem_id, start_time, original_problem)

        except Exception as e:
            self.stats["failed_translations"] += 1
            print(f"❌ Ошибка агента перевода: {e}")
            return self._format_error_response(str(e), time.time() - start_time, user_query)

    def _format_success_response(self, result_data: Dict[str, Any], execution_time: float, is_complete: bool) -> Dict[
        str, Any]:
        """Форматировать успешный ответ"""
        quality_score = result_data.get("quality_score", 0.7)

        response = {
            "success": True,
            "data": result_data,
            "metadata": {
                "agent_type": "enhanced_translation",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "translation_complete": is_complete,
                "quality_score": quality_score
            }
        }

        # Сообщение пользователю
        if quality_score >= 0.9:
            response["user_message"] = "✅ Перевод выполнен отлично! Все поля задачи переведены."
        elif quality_score >= 0.7:
            response["user_message"] = "✅ Перевод выполнен хорошо! Большинство полей переведены."
        elif quality_score >= 0.5:
            response["user_message"] = "⚠️ Перевод выполнен частично. Некоторые поля могут быть не переведены."
        else:
            response["user_message"] = "⚠️ Перевод выполнен с ограничениями. Используется fallback."

        return response

    def _format_fallback_response(self, target_language: str, contest_id: int, problem_id: str,
                                  start_time: float, original_problem: Dict[str, Any] = None) -> Dict[str, Any]:
        """Форматировать fallback ответ"""
        if not original_problem:
            original_problem = {
                'metadata': {
                    'contest_id': str(contest_id),
                    'problem_id': problem_id,
                    'title': f"Problem {problem_id}",
                },
                'content': {
                    'task': 'Не удалось загрузить задачу',
                    'input': '',
                    'output': '',
                    'note': ''
                }
            }

        import copy
        translated_problem = copy.deepcopy(original_problem)

        # Простой fallback перевод
        if target_language == "ru" and 'metadata' in translated_problem:
            metadata = translated_problem['metadata']
            if 'title' in metadata:
                metadata['title'] = f"Перевод: {metadata['title']}"

        result_data = {
            "translated_problem": translated_problem,
            "target_language": target_language,
            "original_problem": original_problem,
            "quality_score": 0.3,
            "is_fallback": True
        }

        response = {
            "success": True,
            "data": result_data,
            "metadata": {
                "agent_type": "enhanced_translation",
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "translation_complete": False,
                "quality_score": 0.3,
                "is_fallback": True
            },
            "user_message": "⚠️ Использован упрощенный перевод из-за технических ограничений."
        }

        self.stats["partial_translations"] += 1
        return response

    def _format_error_response(self, error: str, execution_time: float, user_query: str) -> Dict[str, Any]:
        """Форматировать ответ при ошибке"""
        response = {
            "success": False,
            "error": error,
            "metadata": {
                "agent_type": "enhanced_translation",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "is_error": True
            },
            "user_message": f"❌ Ошибка при переводе: {error[:100]}"
        }

        return response

    def get_status(self) -> Dict[str, Any]:
        return {
            "stats": self.stats,
            "translator_available": self.translator_tool is not None,
            "mistral_available": mistral_client is not None
        }


class EnhancedContestGeneratorAgent:
    """Улучшенный агент генерации контестов"""

    def __init__(self):
        self.generator_tool = MistralContestGeneratorTool() if mistral_client else None
        self.analyzer_tool = QueryAnalyzerTool()
        self.stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "partial_generations": 0,
            "failed_generations": 0
        }

    async def run(self, user_query: str, user_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Запустить генерацию контеста"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            print(f"\n🏆 ЗАПУСК УЛУЧШЕННОГО ГЕНЕРАТОРА КОНТЕСТОВ")
            print(f"📝 Запрос: {user_query[:80]}...")

            # Анализируем запрос
            analysis_result = await self.analyzer_tool.execute(
                user_query=user_query,
                user_params=user_params or {}
            )

            if not analysis_result.get("success"):
                return self._format_error_response(
                    "Не удалось проанализировать запрос",
                    time.time() - start_time,
                    user_query
                )

            analysis_data = analysis_result["data"]
            params = analysis_data.get("parameters", {})

            # Извлекаем параметры
            difficulty = params.get("difficulty", 3)
            topic = params.get("topic", "implementation")
            problem_count = min(max(params.get("problem_count", 5), ContestConfig.MIN_PROBLEMS),
                                ContestConfig.MAX_PROBLEMS)

            print(f"📊 Параметры: сложность={difficulty}, тема={topic}, задач={problem_count}")

            # Генерируем контест
            if self.generator_tool:
                print(f"🤖 Генерация контеста с помощью Mistral AI...")
                generation_result = await self.generator_tool.execute(
                    difficulty=difficulty,
                    topic=topic,
                    problem_count=problem_count,
                    user_query=user_query
                )

                if generation_result.get("success"):
                    self.stats["successful_generations"] += 1
                    result_data = generation_result["data"]

                    # Проверяем качество
                    relevance_score = result_data.get("relevance_analysis", {}).get("overall_relevance_score", 0)
                    if relevance_score < 0.6:
                        self.stats["partial_generations"] += 1
                        print(f"⚠️ Контест сгенерирован с ограничениями")

                    return self._format_success_response(result_data, time.time() - start_time, relevance_score)
                else:
                    self.stats["failed_generations"] += 1
                    print(f"❌ Ошибка генерации: {generation_result.get('error')}")

            # Fallback
            return await self._generate_fallback_contest(difficulty, topic, problem_count, start_time)

        except Exception as e:
            self.stats["failed_generations"] += 1
            print(f"❌ Ошибка агента генерации: {e}")
            return self._format_error_response(str(e), time.time() - start_time, user_query)

    async def _generate_fallback_contest(self, difficulty: int, topic: str, problem_count: int, start_time: float) -> \
    Dict[str, Any]:
        """Создать fallback контест"""
        difficulty_labels = {1: "Новичок", 2: "Легкий", 3: "Средний", 4: "Сложный", 5: "Эксперт"}

        contest_data = {
            "contest_title": f"Резервный контест - {topic}",
            "description": "Базовый контест (режим fallback)",
            "difficulty": difficulty_labels.get(difficulty, "Средний"),
            "topic": topic,
            "estimated_time_minutes": problem_count * 20,
            "total_problems": problem_count,
            "successfully_parsed": 0,
            "problems": [],
            "relevance_analysis": {
                "overall_relevance_score": 0.5,
                "is_fallback": True
            },
            "metadata": {
                "is_fallback": True
            }
        }

        response = {
            "success": True,
            "data": contest_data,
            "metadata": {
                "agent_type": "enhanced_contest_generator",
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "relevance_score": 0.5,
                "is_fallback": True
            },
            "user_message": "⚠️ Использован упрощенный контест из-за технических ограничений."
        }

        self.stats["partial_generations"] += 1
        return response

    def _format_success_response(self, result_data: Dict[str, Any], execution_time: float, relevance_score: float) -> \
    Dict[str, Any]:
        """Форматировать успешный ответ"""
        response = {
            "success": True,
            "data": result_data,
            "metadata": {
                "agent_type": "enhanced_contest_generator",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "relevance_score": relevance_score,
                "generation_method": result_data.get("generation_method", "unknown")
            }
        }

        # Сообщение пользователю
        if relevance_score >= 0.8:
            response["user_message"] = "✅ Контест сгенерирован отлично! Задачи хорошо соответствуют запросу."
        elif relevance_score >= 0.6:
            response["user_message"] = "✅ Контест сгенерирован хорошо! Задачи соответствуют запросу."
        elif relevance_score >= 0.4:
            response[
                "user_message"] = "⚠️ Контест сгенерирован с ограничениями. Некоторые задачи могут не полностью соответствовать запросу."
        else:
            response["user_message"] = "⚠️ Контест сгенерирован с ограничениями. Используется fallback."

        return response

    def _format_error_response(self, error: str, execution_time: float, user_query: str) -> Dict[str, Any]:
        """Форматировать ответ при ошибке"""
        response = {
            "success": False,
            "error": error,
            "metadata": {
                "agent_type": "enhanced_contest_generator",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "is_error": True
            },
            "user_message": f"❌ Ошибка при генерации контеста: {error[:100]}"
        }

        return response

    def get_status(self) -> Dict[str, Any]:
        return {
            "stats": self.stats,
            "generator_available": self.generator_tool is not None,
            "mistral_available": mistral_client is not None
        }


# ==================== FASTAPI ИНТЕГРАЦИЯ ====================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid


class AgentRequest(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: str
    execution_time: float
    agent_state: Dict[str, Any]
    agent_type: str
    raw_response: Optional[Dict[str, Any]] = None


# Инициализация агентов
translation_agent = EnhancedTranslationAgent()
contest_generator_agent = EnhancedContestGeneratorAgent()

app = FastAPI(
    title="Codeforces Enhanced Agents API v9.0",
    description="Полная система с новым парсером, переводчиком и генератором контестов",
    version="9.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_problem_id_from_string(problem_str: str) -> Tuple[Optional[int], Optional[str]]:
    """Извлечь ID задачи из строки"""
    patterns = [
        r'(\d+)[\s\-/]?([A-F])',
        r'(\d+)\s*-\s*([A-F])',
        r'(\d+)/([A-F])',
        r'cf-(\d+)-([A-F])',
        r'cf_(\d+)_([A-F])'
    ]

    for pattern in patterns:
        match = re.search(pattern, problem_str, re.IGNORECASE)
        if match:
            try:
                contest_id = int(match.group(1))
                problem_id = match.group(2).upper()
                return contest_id, problem_id
            except:
                continue

    return None, None


@app.get("/")
async def root():
    return {
        "service": "Codeforces Enhanced Agents API v9.0",
        "version": "9.0.0",
        "features": [
            "Новый парсер с извлечением тестов",
            "Полный перевод всех полей задачи",
            "Генерация контестов с Mistral AI",
            "Сохранение математических формул и переменных",
            "Анализ качества перевода и релевантности"
        ],
        "mistral_status": "✅ Доступен" if mistral_client else "❌ Недоступен",
        "endpoints": {
            "parser": "GET /parser/{problem_id}",
            "translation": "POST /translate",
            "contest_generation": "POST /generate_contest",
            "status": "GET /status"
        }
    }


@app.get("/parser/{problem_id}")
async def parse_problem_endpoint(problem_id: str):
    """Парсинг задачи Codeforces по ID"""
    try:
        print(f"\n🔍 ЗАПРОС НА ПАРСИНГ: {problem_id}")

        contest_id, problem_letter = extract_problem_id_from_string(problem_id)

        if not contest_id or not problem_letter:
            match = re.match(r'^(\d+)([A-F])$', problem_id, re.IGNORECASE)
            if match:
                contest_id = int(match.group(1))
                problem_letter = match.group(2).upper()
            else:
                raise HTTPException(status_code=400,
                                    detail=f"Неверный формат ID задачи: {problem_id}")

        print(f"📊 Парсинг задачи {contest_id}{problem_letter}...")

        # Используем синхронный парсинг для этого endpoint
        problem_data = parse_problem_sync(contest_id, problem_letter)

        if not problem_data:
            raise HTTPException(status_code=404, detail=f"Не удалось распарсить задачу {contest_id}{problem_letter}")

        result = create_react_friendly_json(problem_data, contest_id, problem_letter)

        if not result:
            raise HTTPException(status_code=500, detail="Ошибка при создании JSON структуры")

        result['status'] = 'success'
        result['parsed_at'] = datetime.now().isoformat()
        result['problem_id_raw'] = problem_id

        print(f"✅ Задача {contest_id}{problem_letter} успешно распарсена")
        print(f"📊 Найдено тестов: {len(problem_data['samples'])}")

        return {
            "success": True,
            "data": result,
            "metadata": {
                "contest_id": contest_id,
                "problem_id": problem_letter,
                "parsed_at": datetime.now().isoformat(),
                "samples_count": len(problem_data['samples'])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ОШИБКА ПАРСЕРА: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге задачи: {str(e)}")


@app.post("/translate", response_model=AgentResponse)
async def translate_problem(request: AgentRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()

        print(f"\n🌍 ЗАПРОС НА УЛУЧШЕННЫЙ ПЕРЕВОД:")
        print(f"   Запрос: {request.query}")
        if request.parameters:
            print(f"   Параметры: {request.parameters}")

        result = await translation_agent.run(request.query, request.parameters)
        execution_time = time.time() - start_time

        response = AgentResponse(
            success=True,
            data=result.get("data"),
            error=result.get("error"),
            session_id=session_id,
            execution_time=execution_time,
            agent_state=translation_agent.get_status(),
            agent_type="enhanced_translation",
            raw_response=result
        )

        print(f"✅ ОТВЕТ ОТ /translate (время: {execution_time:.2f}с)")

        # Выводим информацию о качестве
        if result.get("success") and "data" in result:
            data = result["data"]
            quality_score = data.get("quality_score", 0)
            is_complete = result.get("metadata", {}).get("translation_complete", False)

            print(f"   🎯 Качество перевода: {quality_score:.1%}")
            print(f"   📊 Полнота: {'✅ Полный' if is_complete else '⚠️ Частичный'}")

            if 'quality_analysis' in data:
                analysis = data['quality_analysis']
                strengths = analysis.get('strengths', [])
                if strengths:
                    print(f"   👍 {strengths[0]}")

        return response

    except Exception as e:
        print(f"❌ ОШИБКА В /translate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_contest", response_model=AgentResponse)
async def generate_contest(request: AgentRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()

        print(f"\n🏆 ЗАПРОС НА ГЕНЕРАЦИЮ КОНТЕСТА:")
        print(f"   Запрос: {request.query}")
        if request.parameters:
            print(f"   Параметры: {request.parameters}")

        result = await contest_generator_agent.run(request.query, request.parameters)
        execution_time = time.time() - start_time

        response = AgentResponse(
            success=True,
            data=result.get("data"),
            error=result.get("error"),
            session_id=session_id,
            execution_time=execution_time,
            agent_state=contest_generator_agent.get_status(),
            agent_type="enhanced_contest_generator",
            raw_response=result
        )

        print(f"✅ ОТВЕТ ОТ /generate_contest (время: {execution_time:.2f}с)")

        # Выводим информацию о контесте
        if result.get("success") and "data" in result:
            data = result["data"]
            title = data.get("contest_title", "N/A")
            problems = data.get("problems", [])
            relevance_score = data.get("relevance_analysis", {}).get("overall_relevance_score", 0)

            print(f"   🏆 Контест: {title}")
            print(f"   📚 Задач: {len(problems)}")
            print(f"   🎯 Релевантность: {relevance_score:.1%}")

            if problems:
                for i, problem in enumerate(problems[:3]):  # Показываем первые 3
                    parsed = "✅" if problem.get("parsed_successfully") else "❌"
                    print(f"   {i + 1}. {problem.get('problem_id', '?')} {parsed}")

        return response

    except Exception as e:
        print(f"❌ ОШИБКА В /generate_contest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    return {
        "success": True,
        "agents": {
            "translation": translation_agent.get_status(),
            "contest_generator": contest_generator_agent.get_status()
        },
        "mistral_ai": {
            "available": mistral_client is not None,
            "model": APIConfig.MISTRAL_MODEL if mistral_client else "N/A"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 ЗАПУСК CODEFORCES ENHANCED AGENTS API v9.0")
    print("=" * 80)
    print("✅ Новый парсер с извлечением тестов")
    print(f"✅ Mistral AI: {'✅ Доступен' if mistral_client else '❌ Недоступен'}")
    print("✅ Полный перевод всех полей задачи")
    print("✅ Генерация контестов с интеллектуальным подбором")
    print("✅ Сохранение математических формул и переменных")
    print("=" * 80)
    print("🔍 Парсер: GET /parser/4-A")
    print("🌍 Переводчик: POST /translate")
    print("🏆 Генератор: POST /generate_contest")
    print("📊 Статус: GET /status")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )