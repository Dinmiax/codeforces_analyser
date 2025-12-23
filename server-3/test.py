#!/usr/bin/env python3
"""
🎯 ТЕСТЕР API С MISTRAL AI
"""

import requests
import json
import time
from datetime import datetime


class SmartAPITester:
    """Умный тестер с поддержкой Mistral AI"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.results = []

    def run_smart_tests(self):
        """Запустить умные тесты"""
        print("🎯 ТЕСТИРОВАНИЕ API С MISTRAL AI")
        print("=" * 80)

        self.test_basic_endpoints()
        self.test_translation_agent_with_mistral()
        self.test_contest_generator_with_mistral()
        self.analyze_results()
        self.generate_report()

    def test_basic_endpoints(self):
        """Тест базовых endpoints"""
        print("\n📊 БАЗОВЫЕ ENDPOINTS:")
        print("-" * 40)

        endpoints = [
            ("/", "Корневой endpoint"),
            ("/status", "Статус агентов"),
        ]

        for endpoint, description in endpoints:
            print(f"\n{description}:")
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )

                if response.status_code == 200:
                    print(f"  ✅ HTTP 200")
                    data = response.json()

                    if endpoint == "/status":
                        mistral_status = data.get('mistral_ai', {}).get('available', False)
                        print(f"  🤖 Mistral AI: {'✅ Доступен' if mistral_status else '❌ Недоступен'}")

                        agents = data.get('agents', {})
                        for agent_name, agent_info in agents.items():
                            tools = agent_info.get('tools_available', [])
                            print(f"  👷 {agent_name}: {len(tools)} инструментов")

                else:
                    print(f"  ❌ HTTP {response.status_code}")

            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

    def test_translation_agent_with_mistral(self):
        """Тест агента-переводчика с Mistral AI"""
        print("\n\n🌍 ТЕСТИРОВАНИЕ ПЕРЕВОДЧИКА С MISTRAL AI:")
        print("=" * 80)

        test_cases = [
            {
                "name": "1. Перевод Watermelon (4A)",
                "payload": {
                    "query": "Переведи задачу https://codeforces.com/problemset/problem/4/A",
                    "parameters": {"target_language": "ru"}
                }
            },
            {
                "name": "2. Перевод на английский",
                "payload": {
                    "query": "Переведи задачу 231A на английский",
                    "parameters": {"target_language": "en"}
                }
            },
            {
                "name": "3. Перевод с анализом качества",
                "payload": {
                    "query": "переведи задачу про арбуз с анализом",
                }
            }
        ]

        for test_case in test_cases:
            print(f"\n{test_case['name']}")
            print(f"📤 Запрос: {test_case['payload']['query'][:80]}...")

            result = self._send_request_with_analysis("/translate", test_case)
            self.results.append(result)

            time.sleep(2)  # Задержка между запросами

    def test_contest_generator_with_mistral(self):
        """Тест генератора контестов с Mistral AI"""
        print("\n\n🏆 ТЕСТИРОВАНИЕ ГЕНЕРАТОРА КОНТЕСТОВ С MISTRAL AI:")
        print("=" * 80)

        test_cases = [
            {
                "name": "1. Контест по графам для начинающих",
                "payload": {
                    "query": "Создай контест по графам для начинающих",
                    "parameters": {"difficulty": 1, "problem_count": 3}
                }
            },
            {
                "name": "2. Контест по ДП средней сложности",
                "payload": {
                    "query": "Контест по динамическому программированию",
                    "parameters": {"difficulty": 3, "topic": "dp", "problem_count": 4}
                }
            },
            {
                "name": "3. Контест для подготовки к Div2",
                "payload": {
                    "query": "Подбери задачи для подготовки к Div2",
                }
            }
        ]

        for test_case in test_cases:
            print(f"\n{test_case['name']}")
            print(f"📤 Запрос: {test_case['payload']['query'][:80]}...")

            result = self._send_request_with_analysis("/generate_contest", test_case)
            self.results.append(result)

            time.sleep(2)

    def _send_request_with_analysis(self, endpoint, test_case):
        """Отправить запрос с анализом ответа"""
        start_time = time.time()

        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=test_case["payload"],
                timeout=60  # Увеличиваем таймаут для Mistral AI
            )

            execution_time = time.time() - start_time

            print(f"  ⏱️  Время: {execution_time:.2f}с")
            print(f"  📡 Статус: {response.status_code}")

            result = {
                "endpoint": endpoint,
                "test_name": test_case["name"],
                "execution_time": execution_time,
                "status_code": response.status_code,
                "success": False
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result["raw_response"] = data
                    result["success"] = data.get("success", False)

                    # Выводим ключевую информацию
                    if endpoint == "/translate":
                        self._analyze_translation_response(data)
                    else:
                        self._analyze_contest_response(data)

                except json.JSONDecodeError as e:
                    print(f"  ❌ Невалидный JSON: {e}")
                    result["error"] = f"JSON decode error: {e}"
            else:
                print(f"  ❌ HTTP {response.status_code}")
                result["error"] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            print(f"  ❌ ТАЙМАУТ (60 секунд)")
            result = {
                "endpoint": endpoint,
                "test_name": test_case["name"],
                "execution_time": 60,
                "status_code": 0,
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"  ❌ ОШИБКА ЗАПРОСА: {e}")
            result = {
                "endpoint": endpoint,
                "test_name": test_case["name"],
                "execution_time": time.time() - start_time,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }

        return result

    def _analyze_translation_response(self, data):
        """Анализировать ответ переводчика"""
        if data.get("success"):
            print(f"  ✅ УСПЕШНО")

            response_data = data.get("data", {})

            # Информация о переводе
            target_lang = response_data.get("target_language", "N/A")
            quality_score = response_data.get("quality_score", 0)
            method = response_data.get("translation_method", "unknown")

            print(f"  🌍 Язык: {target_lang}")
            print(f"  ⭐ Качество: {quality_score:.1%}")
            print(f"  🔧 Метод: {method}")

            # Анализ качества
            quality_analysis = response_data.get("quality_analysis", {})
            if quality_analysis:
                overall = quality_analysis.get("overall_score", 0)
                print(f"  📊 Оценка анализа: {overall:.1%}")

                strengths = quality_analysis.get("strengths", [])
                if strengths:
                    print(f"  👍 Сильные стороны: {strengths[0]}")

            # Информация о задаче
            translated = response_data.get("translated_problem", {})
            if translated:
                metadata = translated.get("metadata", {})
                title = metadata.get("title", "N/A")
                print(f"  📝 Задача: {title[:50]}...")

                # Проверяем, был ли перевод
                if "Перевод:" in title or "Translated:" in title:
                    print(f"  ✅ Перевод выполнен")
                else:
                    print(f"  ⚠️  Возможно, перевод не выполнен")

            # Fallback проверка
            if response_data.get("is_fallback"):
                print(f"  ⚠️  Использован fallback режим")

        else:
            error = data.get("error", "Unknown error")
            print(f"  ❌ ОШИБКА: {error[:200]}")

    def _analyze_contest_response(self, data):
        """Анализировать ответ генератора контестов"""
        if data.get("success"):
            print(f"  ✅ УСПЕШНО")

            response_data = data.get("data", {})

            # Основная информация
            title = response_data.get("contest_title", "N/A")
            difficulty = response_data.get("difficulty", "N/A")
            topic = response_data.get("topic", "N/A")
            total = response_data.get("total_problems", 0)
            parsed = response_data.get("successfully_parsed", 0)
            method = response_data.get("generation_method", "unknown")

            print(f"  🏆 Контест: {title}")
            print(f"  📊 Сложность: {difficulty}")
            print(f"  🎯 Тема: {topic}")
            print(f"  📚 Задач: {total} (спарсено: {parsed})")
            print(f"  🔧 Метод: {method}")

            # Анализ релевантности
            relevance = response_data.get("relevance_analysis", {})
            if relevance:
                score = relevance.get("overall_relevance_score", 0)
                print(f"  🎯 Релевантность: {score:.1%}")

                strengths = relevance.get("strengths", [])
                if strengths:
                    print(f"  👍 {strengths[0]}")

                recommendations = relevance.get("recommendations", [])
                if recommendations:
                    print(f"  💡 Рекомендация: {recommendations[0]}")

            # Список задач
            problems = response_data.get("problems", [])
            if problems:
                print(f"  📋 Задачи:")
                for i, problem in enumerate(problems[:3]):  # Показываем первые 3
                    pid = problem.get("problem_id", "?")
                    title = problem.get("title", "Unknown")[:30]
                    rating = problem.get("difficulty_rating", "N/A")
                    parsed = "✅" if problem.get("parsed_successfully") else "❌"
                    print(f"     {i + 1}. {pid}: {title}... ({rating}) {parsed}")

                if len(problems) > 3:
                    print(f"     ... и еще {len(problems) - 3} задач")

            # Fallback проверка
            if response_data.get("is_fallback"):
                print(f"  ⚠️  Использован fallback режим")

        else:
            error = data.get("error", "Unknown error")
            print(f"  ❌ ОШИБКА: {error[:200]}")

    def analyze_results(self):
        """Анализ результатов"""
        print("\n\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
        print("=" * 80)

        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))

        print(f"📈 СТАТИСТИКА:")
        print(f"  • Всего тестов: {total}")
        print(f"  • Успешных: {successful}")
        print(f"  • Успешность: {(successful / total * 100 if total > 0 else 0):.1f}%")

        if total > 0:
            avg_time = sum(r["execution_time"] for r in self.results) / total
            print(f"  • Среднее время: {avg_time:.2f}с")

    def generate_report(self):
        """Генерация отчета"""
        print("\n\n📋 ФИНАЛЬНЫЙ ОТЧЕТ:")
        print("=" * 80)

        # Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mistral_test_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "base_url": self.base_url,
                    "results": self.results
                }, f, indent=2, ensure_ascii=False, default=str)

            print(f"💾 Результаты сохранены в: {filename}")
        except Exception as e:
            print(f"⚠️  Не удалось сохранить результаты: {e}")

        print("\n" + "=" * 80)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 80)


def main():
    """Основная функция"""
    print("🎯 ТЕСТЕР API CODEFORCES AGENTS С MISTRAL AI")
    print("Версия 7.0 - Интеллектуальный перевод и генерация контестов")
    print("=" * 80)

    tester = SmartAPITester("http://localhost:8000")
    tester.run_smart_tests()


if __name__ == "__main__":
    main()