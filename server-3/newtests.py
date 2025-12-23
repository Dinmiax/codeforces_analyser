#!/usr/bin/env python3
"""
🎯 ТЕСТЕР API С MISTRAL AI И РАСШИРЕННЫМИ МЕТРИКАМИ
"""

import requests
import json
import time
from datetime import datetime
import statistics
from typing import List, Dict, Any
import numpy as np


class EnhancedAPITester:
    """Умный тестер с поддержкой Mistral AI и расширенными метриками"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.translation_results = []
        self.contest_results = []
        self.parser_results = []
        self.metrics = {
            'translation': {},
            'contest': {},
            'parser': {}
        }

    def load_test_cases_from_json(self, filename="test_cases.json"):
        """Загрузить тесткейсы из JSON файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Файл {filename} не найден, используем встроенные тесткейсы")
            return self._get_default_test_cases()

    def _get_default_test_cases(self):
        """Встроенные тесткейсы на случай отсутствия файла"""
        return {
            "translation": [
                {
                    "id": "trans_1",
                    "name": "Watermelon (4A) - Русский",
                    "query": "Переведи задачу https://codeforces.com/problemset/problem/4/A",
                    "parameters": {"target_language": "ru"},
                    "expected": {"success": True, "has_translation": True}
                },
                {
                    "id": "trans_2",
                    "name": "Watermelon (4A) - Английский",
                    "query": "Переведи задачу 4A на английский",
                    "parameters": {"target_language": "en"},
                    "expected": {"success": True, "has_translation": True}
                },
                {
                    "id": "trans_3",
                    "name": "Way Too Long Words (71A)",
                    "query": "переведи задачу 71A",
                    "parameters": {"target_language": "ru"},
                    "expected": {"success": True, "has_translation": True}
                },
                {
                    "id": "trans_4",
                    "name": "Team (231A) - Полный перевод",
                    "query": "Полный перевод задачи 231A",
                    "parameters": {"target_language": "ru"},
                    "expected": {"success": True, "has_translation": True}
                },
                {
                    "id": "trans_5",
                    "name": "Некорректный URL",
                    "query": "переведи задачу https://codeforces.com/problemset/problem/999999/Z",
                    "parameters": {"target_language": "ru"},
                    "expected": {"success": False}
                }
            ],
            "contest": [
                {
                    "id": "contest_1",
                    "name": "Контест по графам для начинающих",
                    "query": "Создай контест по графам для начинающих",
                    "parameters": {"difficulty": 1, "problem_count": 3},
                    "expected": {"success": True, "min_problems": 2}
                },
                {
                    "id": "contest_2",
                    "name": "Контест по ДП средней сложности",
                    "query": "Контест по динамическому программированию",
                    "parameters": {"difficulty": 3, "topic": "dp", "problem_count": 4},
                    "expected": {"success": True, "min_problems": 3}
                },
                {
                    "id": "contest_3",
                    "name": "Подготовка к Div2",
                    "query": "Подбери задачи для подготовки к Div2",
                    "expected": {"success": True, "min_problems": 4}
                },
                {
                    "id": "contest_4",
                    "name": "Математические задачи",
                    "query": "Задачи по математике для продвинутых",
                    "parameters": {"difficulty": 4, "topic": "math", "problem_count": 5},
                    "expected": {"success": True, "min_problems": 4}
                },
                {
                    "id": "contest_5",
                    "name": "Жадные алгоритмы",
                    "query": "контест по жадным алгоритмам",
                    "parameters": {"topic": "greedy"},
                    "expected": {"success": True, "min_problems": 3}
                }
            ],
            "parser": [
                {
                    "id": "parser_1",
                    "name": "Простая задача (4A)",
                    "problem_id": "4-A",
                    "expected": {"success": True, "has_tests": True}
                },
                {
                    "id": "parser_2",
                    "name": "Средняя задача (231A)",
                    "problem_id": "231-A",
                    "expected": {"success": True, "has_tests": True}
                },
                {
                    "id": "parser_3",
                    "name": "Сложная задача (1C)",
                    "problem_id": "1-C",
                    "expected": {"success": True, "has_tests": True}
                },
                {
                    "id": "parser_4",
                    "name": "Некорректный ID",
                    "problem_id": "999999-Z",
                    "expected": {"success": False}
                },
                {
                    "id": "parser_5",
                    "name": "Задача с математикой (118A)",
                    "problem_id": "118-A",
                    "expected": {"success": True, "has_tests": True}
                }
            ]
        }

    def run_comprehensive_tests(self):
        """Запустить комплексные тесты"""
        print("🎯 ТЕСТИРОВАНИЕ API CODEFORCES AGENTS С РАСШИРЕННЫМИ МЕТРИКАМИ")
        print("=" * 100)

        # Загружаем тесткейсы
        test_cases = self.load_test_cases_from_json()

        # Запускаем тесты для каждого агента
        print(f"\n{'📊 ТЕСТИРОВАНИЕ ПАРСЕРА':<50} | {'📝':<10} | {'⏱️':<10} | {'🎯':<10} | {'📈':<10}")
        print("-" * 100)
        for test_case in test_cases.get("parser", [])[:50]:  # Ограничиваем 50 тестами
            self.test_parser_endpoint(test_case)
            time.sleep(0.5)  # Задержка между запросами

        print(f"\n{'🌍 ТЕСТИРОВАНИЕ ПЕРЕВОДЧИКА':<50} | {'📝':<10} | {'⏱️':<10} | {'🎯':<10} | {'📈':<10}")
        print("-" * 100)
        for test_case in test_cases.get("translation", [])[:50]:
            self.test_translation_agent(test_case)
            time.sleep(1)  # Большая задержка для Mistral AI

        print(f"\n{'🏆 ТЕСТИРОВАНИЕ ГЕНЕРАТОРА КОНТЕСТОВ':<50} | {'📝':<10} | {'⏱️':<10} | {'🎯':<10} | {'📈':<10}")
        print("-" * 100)
        for test_case in test_cases.get("contest", [])[:50]:
            self.test_contest_generator(test_case)
            time.sleep(1.5)  # Самая большая задержка

        # Анализируем результаты
        self.calculate_metrics()
        self.generate_detailed_report()

    def test_parser_endpoint(self, test_case):
        """Тестировать парсер"""
        endpoint = f"/parser/{test_case['problem_id']}"
        result = self._execute_test(endpoint, test_case, "parser")
        self.parser_results.append(result)

    def test_translation_agent(self, test_case):
        """Тестировать переводчика"""
        result = self._execute_test("/translate", test_case, "translation", is_post=True)
        self.translation_results.append(result)

    def test_contest_generator(self, test_case):
        """Тестировать генератор контестов"""
        result = self._execute_test("/generate_contest", test_case, "contest", is_post=True)
        self.contest_results.append(result)

    def _execute_test(self, endpoint, test_case, agent_type, is_post=False):
        """Выполнить тест и вернуть результаты"""
        start_time = time.time()
        success = False
        error = None
        quality_score = 0
        additional_metrics = {}

        try:
            if is_post:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={"query": test_case["query"], "parameters": test_case.get("parameters", {})},
                    timeout=90  # Увеличиваем таймаут для сложных операций
                )
            else:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=30
                )

            execution_time = time.time() - start_time
            status_code = response.status_code

            if response.status_code in [200, 201]:
                data = response.json()
                success = data.get("success", False)

                # Извлекаем дополнительные метрики
                quality_score = self._extract_quality_score(data, agent_type)
                additional_metrics = self._extract_additional_metrics(data, agent_type)

                # Проверяем ожидания
                expected = test_case.get("expected", {})
                meets_expectations = self._check_expectations(data, expected, agent_type)

                # Форматируем вывод
                self._print_test_result(
                    test_case["name"],
                    success,
                    execution_time,
                    quality_score,
                    meets_expectations,
                    agent_type
                )

            else:
                success = False
                error = f"HTTP {status_code}"
                execution_time = time.time() - start_time

                self._print_test_result(
                    test_case["name"],
                    success,
                    execution_time,
                    quality_score,
                    False,
                    agent_type,
                    error=error
                )

        except requests.exceptions.Timeout:
            execution_time = time.time() - start_time
            success = False
            error = "Timeout"
            self._print_test_result(
                test_case["name"],
                success,
                execution_time,
                quality_score,
                False,
                agent_type,
                error=error
            )

        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error = str(e)
            self._print_test_result(
                test_case["name"],
                success,
                execution_time,
                quality_score,
                False,
                agent_type,
                error=error
            )

        return {
            "test_id": test_case.get("id", "unknown"),
            "name": test_case["name"],
            "agent_type": agent_type,
            "endpoint": endpoint,
            "success": success,
            "execution_time": execution_time,
            "quality_score": quality_score,
            "error": error,
            "additional_metrics": additional_metrics,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_quality_score(self, data, agent_type):
        """Извлечь оценку качества из ответа"""
        if agent_type == "translation":
            response_data = data.get("data", {})
            return response_data.get("quality_score", 0)
        elif agent_type == "contest":
            response_data = data.get("data", {})
            relevance = response_data.get("relevance_analysis", {})
            return relevance.get("overall_relevance_score", 0)
        elif agent_type == "parser":
            return 1.0 if data.get("success") else 0.0
        return 0.0

    def _extract_additional_metrics(self, data, agent_type):
        """Извлечь дополнительные метрики"""
        metrics = {}

        if agent_type == "translation":
            response_data = data.get("data", {})
            metrics.update({
                "target_language": response_data.get("target_language", "unknown"),
                "translation_method": response_data.get("translation_method", "unknown"),
                "translation_complete": response_data.get("translation_complete", False),
                "is_fallback": response_data.get("is_fallback", False)
            })

            # Метрики из анализа качества
            quality_analysis = response_data.get("quality_analysis", {})
            if quality_analysis:
                metrics.update({
                    "technical_terms_score": quality_analysis.get("technical_terms_score", 0),
                    "formulas_preservation_score": quality_analysis.get("formulas_preservation_score", 0),
                    "variables_preservation_score": quality_analysis.get("variables_preservation_score", 0),
                    "language_naturalness_score": quality_analysis.get("language_naturalness_score", 0),
                    "completeness_score": quality_analysis.get("completeness_score", 0)
                })

        elif agent_type == "contest":
            response_data = data.get("data", {})
            metrics.update({
                "total_problems": response_data.get("total_problems", 0),
                "successfully_parsed": response_data.get("successfully_parsed", 0),
                "generation_method": response_data.get("generation_method", "unknown"),
                "is_fallback": response_data.get("is_fallback", False)
            })

            # Метрики из анализа релевантности
            relevance_analysis = response_data.get("relevance_analysis", {})
            if relevance_analysis:
                metrics.update({
                    "topic_match_score": relevance_analysis.get("topic_match_score", 0),
                    "difficulty_match_score": relevance_analysis.get("difficulty_match_score", 0),
                    "progression_score": relevance_analysis.get("progression_score", 0),
                    "balance_score": relevance_analysis.get("balance_score", 0),
                    "usefulness_score": relevance_analysis.get("usefulness_score", 0)
                })

        elif agent_type == "parser":
            response_data = data.get("data", {})
            metrics.update({
                "samples_count": response_data.get("metadata", {}).get("samples_count", 0),
                "has_tests": response_data.get("metadata", {}).get("samples_count", 0) > 0,
                "parsed_successfully": data.get("success", False)
            })

        return metrics

    def _check_expectations(self, data, expected, agent_type):
        """Проверить соответствие ожиданиям"""
        if not expected:
            return True

        success_match = data.get("success", False) == expected.get("success", True)

        if agent_type == "translation":
            if expected.get("has_translation"):
                response_data = data.get("data", {})
                translated = response_data.get("translated_problem", {})
                metadata = translated.get("metadata", {})
                title = metadata.get("title", "")
                return success_match and "Перевод:" in title or "Translated:" in title

        elif agent_type == "contest":
            if expected.get("min_problems"):
                response_data = data.get("data", {})
                total_problems = response_data.get("total_problems", 0)
                return success_match and total_problems >= expected["min_problems"]

        elif agent_type == "parser":
            if expected.get("has_tests"):
                response_data = data.get("data", {})
                samples_count = response_data.get("metadata", {}).get("samples_count", 0)
                return success_match and samples_count > 0

        return success_match

    def _print_test_result(self, name, success, exec_time, quality, expectations, agent_type, error=None):
        """Напечатать результат теста"""
        # Цветовая кодировка
        success_symbol = "✅" if success else "❌"
        expectations_symbol = "✓" if expectations else "✗"

        # Форматирование времени
        time_str = f"{exec_time:.2f}s"
        if exec_time > 10:
            time_str = f"⚠️{exec_time:.1f}s"

        # Форматирование качества
        quality_str = f"{quality:.1%}" if quality > 0 else "N/A"

        # Индикатор типа агента
        agent_icon = "🔍" if agent_type == "parser" else "🌍" if agent_type == "translation" else "🏆"

        # Вывод
        name_trunc = name[:45] + "..." if len(name) > 45 else name.ljust(48)
        print(
            f"{agent_icon} {name_trunc} | {success_symbol:^8} | {time_str:^8} | {quality_str:^8} | {expectations_symbol:^8}",
            end="")

        if error:
            error_short = error[:15] + "..." if len(error) > 15 else error
            print(f" | ❌ {error_short}")
        else:
            print()

    def calculate_metrics(self):
        """Рассчитать метрики для всех агентов"""
        print(f"\n{'📊 РАСЧЕТ МЕТРИК':<50} | {'📈':<10} | {'📉':<10} | {'📋':<10} | {'🎯':<10}")
        print("-" * 100)

        # Метрики для парсера
        if self.parser_results:
            self._calculate_agent_metrics("parser", self.parser_results)

        # Метрики для переводчика
        if self.translation_results:
            self._calculate_agent_metrics("translation", self.translation_results)

        # Метрики для генератора контестов
        if self.contest_results:
            self._calculate_agent_metrics("contest", self.contest_results)

        # Общие метрики
        self._calculate_overall_metrics()

    def _calculate_agent_metrics(self, agent_type, results):
        """Рассчитать метрики для конкретного агента"""
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        if not results:
            return

        # Базовые метрики
        total_count = len(results)
        success_count = len(successful_results)
        success_rate = success_count / total_count if total_count > 0 else 0

        # Временные метрики
        execution_times = [r["execution_time"] for r in results if r["execution_time"] > 0]
        if execution_times:
            min_time = min(execution_times)
            max_time = max(execution_times)
            avg_time = statistics.mean(execution_times)
            median_time = statistics.median(execution_times)
            std_time = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        else:
            min_time = max_time = avg_time = median_time = std_time = 0

        # Метрики качества
        quality_scores = [r["quality_score"] for r in successful_results if r["quality_score"] > 0]
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            max_quality = max(quality_scores)
            min_quality = min(quality_scores)
            median_quality = statistics.median(quality_scores)
        else:
            avg_quality = max_quality = min_quality = median_quality = 0

        # Дополнительные метрики для каждого агента
        additional_metrics = {}
        if agent_type == "translation" and successful_results:
            translation_complete = sum(1 for r in successful_results
                                       if r.get("additional_metrics", {}).get("translation_complete", False))
            fallback_used = sum(1 for r in successful_results
                                if r.get("additional_metrics", {}).get("is_fallback", False))

            additional_metrics = {
                "translation_complete_rate": translation_complete / success_count if success_count > 0 else 0,
                "fallback_usage_rate": fallback_used / success_count if success_count > 0 else 0
            }

        elif agent_type == "contest" and successful_results:
            avg_problems = statistics.mean([r.get("additional_metrics", {}).get("total_problems", 0)
                                            for r in successful_results])
            avg_parsed = statistics.mean([r.get("additional_metrics", {}).get("successfully_parsed", 0)
                                          for r in successful_results])
            parse_success_rate = avg_parsed / avg_problems if avg_problems > 0 else 0

            additional_metrics = {
                "avg_problems_per_contest": avg_problems,
                "parse_success_rate": parse_success_rate
            }

        elif agent_type == "parser" and successful_results:
            avg_tests = statistics.mean([r.get("additional_metrics", {}).get("samples_count", 0)
                                         for r in successful_results])
            tests_present = sum(1 for r in successful_results
                                if r.get("additional_metrics", {}).get("has_tests", False))
            tests_presence_rate = tests_present / success_count if success_count > 0 else 0

            additional_metrics = {
                "avg_tests_per_problem": avg_tests,
                "tests_presence_rate": tests_presence_rate
            }

        # Сохраняем метрики
        self.metrics[agent_type] = {
            "total_tests": total_count,
            "successful_tests": success_count,
            "success_rate": success_rate,
            "execution_time": {
                "min": min_time,
                "max": max_time,
                "average": avg_time,
                "median": median_time,
                "std_dev": std_time
            },
            "quality": {
                "min": min_quality,
                "max": max_quality,
                "average": avg_quality,
                "median": median_quality
            },
            "additional_metrics": additional_metrics,
            "error_breakdown": self._analyze_errors(failed_results)
        }

        # Вывод метрик
        agent_name = "ПАРСЕР" if agent_type == "parser" else \
            "ПЕРЕВОДЧИК" if agent_type == "translation" else "ГЕНЕРАТОР КОНТЕСТОВ"

        print(
            f"{agent_name:<45} | {success_rate:>8.1%} | {avg_time:>8.2f}s | {avg_quality:>8.1%} | {len(failed_results):>8}")

    def _analyze_errors(self, failed_results):
        """Анализ ошибок"""
        error_types = {}
        for result in failed_results:
            error = result.get("error", "unknown")
            error_types[error] = error_types.get(error, 0) + 1

        return error_types

    def _calculate_overall_metrics(self):
        """Рассчитать общие метрики"""
        print(f"\n{'📈 ОБЩИЕ МЕТРИКИ':<50} | {'🔢':<10} | {'⚡':<10} | {'⭐':<10} | {'📋':<10}")
        print("-" * 100)

        # Суммируем все результаты
        all_results = self.parser_results + self.translation_results + self.contest_results
        total_count = len(all_results)

        if total_count == 0:
            print("❌ Нет данных для анализа")
            return

        # Общая статистика
        successful_results = [r for r in all_results if r["success"]]
        success_count = len(successful_results)
        overall_success_rate = success_count / total_count

        # Время выполнения по всем тестам
        all_execution_times = [r["execution_time"] for r in all_results if r["execution_time"] > 0]
        if all_execution_times:
            overall_avg_time = statistics.mean(all_execution_times)
            overall_median_time = statistics.median(all_execution_times)

            # Производительность по агентам
            parser_times = [r["execution_time"] for r in self.parser_results if r["execution_time"] > 0]
            translation_times = [r["execution_time"] for r in self.translation_results if r["execution_time"] > 0]
            contest_times = [r["execution_time"] for r in self.contest_results if r["execution_time"] > 0]

            avg_by_agent = {
                "parser": statistics.mean(parser_times) if parser_times else 0,
                "translation": statistics.mean(translation_times) if translation_times else 0,
                "contest": statistics.mean(contest_times) if contest_times else 0
            }

            fastest_agent = min(avg_by_agent.items(), key=lambda x: x[1])[0]
            slowest_agent = max(avg_by_agent.items(), key=lambda x: x[1])[0]
        else:
            overall_avg_time = overall_median_time = 0
            fastest_agent = slowest_agent = "N/A"

        # Качество по агентам
        parser_quality = [r["quality_score"] for r in self.parser_results if r["success"] and r["quality_score"] > 0]
        translation_quality = [r["quality_score"] for r in self.translation_results if
                               r["success"] and r["quality_score"] > 0]
        contest_quality = [r["quality_score"] for r in self.contest_results if r["success"] and r["quality_score"] > 0]

        avg_quality_by_agent = {
            "parser": statistics.mean(parser_quality) if parser_quality else 0,
            "translation": statistics.mean(translation_quality) if translation_quality else 0,
            "contest": statistics.mean(contest_quality) if contest_quality else 0
        }

        best_quality_agent = max(avg_quality_by_agent.items(), key=lambda x: x[1])[0]
        worst_quality_agent = min(avg_quality_by_agent.items(), key=lambda x: x[1])[0]

        # Форматируем названия агентов
        agent_names = {
            "parser": "ПАРСЕР",
            "translation": "ПЕРЕВОДЧИК",
            "contest": "ГЕНЕРАТОР КОНТЕСТОВ"
        }

        # Выводим общие метрики
        print(f"{'Общая успешность':<45} | {overall_success_rate:>8.1%} | {'':<8} | {'':<8} | {'':<8}")
        print(
            f"{'Среднее время выполнения':<45} | {overall_avg_time:>8.2f}s | {overall_median_time:>8.2f}s | {'':<8} | {'':<8}")
        print(
            f"{'Самый быстрый агент':<45} | {agent_names.get(fastest_agent, fastest_agent):>8} | {'':<8} | {'':<8} | {'':<8}")
        print(
            f"{'Самый медленный агент':<45} | {agent_names.get(slowest_agent, slowest_agent):>8} | {'':<8} | {'':<8} | {'':<8}")
        print(
            f"{'Лучшее качество':<45} | {agent_names.get(best_quality_agent, best_quality_agent):>8} | {'':<8} | {avg_quality_by_agent.get(best_quality_agent, 0):>8.1%} | {'':<8}")
        print(
            f"{'Худшее качество':<45} | {agent_names.get(worst_quality_agent, worst_quality_agent):>8} | {'':<8} | {avg_quality_by_agent.get(worst_quality_agent, 0):>8.1%} | {'':<8}")

    def generate_detailed_report(self):
        """Генерация детального отчета"""
        print(f"\n{'📋 ДЕТАЛЬНЫЙ ОТЧЕТ':<50}")
        print("=" * 100)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_report_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": len(self.parser_results) + len(self.translation_results) + len(self.contest_results),
                "parser_tests": len(self.parser_results),
                "translation_tests": len(self.translation_results),
                "contest_tests": len(self.contest_results)
            },
            "metrics": self.metrics,
            "detailed_results": {
                "parser": self.parser_results,
                "translation": self.translation_results,
                "contest": self.contest_results
            }
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            print(f"💾 Отчет сохранен в: {filename}")

            # Выводим ключевые выводы
            print(f"\n{'🔑 КЛЮЧЕВЫЕ ВЫВОДЫ':<50}")
            print("=" * 100)

            for agent_type in ["parser", "translation", "contest"]:
                if agent_type in self.metrics:
                    metrics = self.metrics[agent_type]
                    agent_name = "ПАРСЕР" if agent_type == "parser" else \
                        "ПЕРЕВОДЧИК" if agent_type == "translation" else "ГЕНЕРАТОР КОНТЕСТОВ"

                    print(f"\n{agent_name}:")
                    print(f"  • Успешность: {metrics['success_rate']:.1%}")
                    print(f"  • Среднее время: {metrics['execution_time']['average']:.2f}с")
                    print(f"  • Среднее качество: {metrics['quality']['average']:.1%}")

                    if agent_type == "translation" and "additional_metrics" in metrics:
                        add_metrics = metrics["additional_metrics"]
                        if "translation_complete_rate" in add_metrics:
                            print(f"  • Полные переводы: {add_metrics['translation_complete_rate']:.1%}")
                        if "fallback_usage_rate" in add_metrics:
                            print(f"  • Использование fallback: {add_metrics['fallback_usage_rate']:.1%}")

                    elif agent_type == "contest" and "additional_metrics" in metrics:
                        add_metrics = metrics["additional_metrics"]
                        if "avg_problems_per_contest" in add_metrics:
                            print(f"  • Среднее задач в контесте: {add_metrics['avg_problems_per_contest']:.1f}")
                        if "parse_success_rate" in add_metrics:
                            print(f"  • Успешных парсингов: {add_metrics['parse_success_rate']:.1%}")

                    elif agent_type == "parser" and "additional_metrics" in metrics:
                        add_metrics = metrics["additional_metrics"]
                        if "avg_tests_per_problem" in add_metrics:
                            print(f"  • Среднее тестов на задачу: {add_metrics['avg_tests_per_problem']:.1f}")
                        if "tests_presence_rate" in add_metrics:
                            print(f"  • Задач с тестами: {add_metrics['tests_presence_rate']:.1%}")

        except Exception as e:
            print(f"⚠️  Не удалось сохранить отчет: {e}")

        print("\n" + "=" * 100)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 100)


def main():
    """Основная функция"""
    print("🎯 ТЕСТЕР API CODEFORCES AGENTS С РАСШИРЕННЫМИ МЕТРИКАМИ")
    print("Версия 8.0 - Комплексное тестирование с 50 тесткейсами на агента")
    print("=" * 100)

    # Запускаем тесты
    tester = EnhancedAPITester("http://localhost:8000")
    tester.run_comprehensive_tests()


if __name__ == "__main__":
    main()