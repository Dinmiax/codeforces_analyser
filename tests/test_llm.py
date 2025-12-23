import requests
import json
import time
import statistics
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import os

class OllamaTester:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def generate_response(self, 
                         prompt: str, 
                         model: str = "gemma3:270m",
                         stream: bool = False) -> Dict:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 512
            }
        }
        start_time = time.time()
        response = self.session.post(url, json=payload)
        end_time = time.time()
        if response.status_code != 200:
            raise Exception(f"Ошибка запроса: {response.status_code}")
        response_data = response.json()
        response_time = end_time - start_time
        return {
            "response": response_data.get("response", ""),
            "response_time": response_time,
            "total_duration": response_data.get("total_duration", 0) / 1e9,
            "load_duration": response_data.get("load_duration", 0) / 1e9,
            "prompt_eval_count": response_data.get("prompt_eval_count", 0),
            "eval_count": response_data.get("eval_count", 0),
            "eval_duration": response_data.get("eval_duration", 0) / 1e9
        }
    
    def test_single_request(self, 
                           prompt: str, 
                           model: str = "gemma3:270m") -> Dict:
        print(f"\nТест: '{prompt[:50]}...'")
        result = self.generate_response(prompt, model)
        print(f"Время ответа: {result['response_time']:.2f} сек")
        print(f"Общее время обработки: {result['total_duration']:.2f} сек")
        print(f"Количество токенов ответа: {result['eval_count']}")
        print(f"Скорость генерации: {result['eval_count']/result['eval_duration']:.1f} токенов/сек")
        print(f"Ответ: {result['response'][:200]}...")
        return result
    
    def test_performance(self, 
                        prompts: List[str], 
                        model: str = "gemma3:270m",
                        iterations: int = 3) -> Dict:
        all_results = []
        for i, prompt in enumerate(prompts):
            print(f"\n{'='*50}")
            print(f"Тест {i+1}/{len(prompts)}: {prompt[:80]}...")
            iteration_results = []
            for iter_num in range(iterations):
                print(f"  Итерация {iter_num+1}/{iterations}")
                result = self.generate_response(prompt, model)
                iteration_results.append(result)
                time.sleep(0.5)
            response_times = [r['response_time'] for r in iteration_results]
            eval_counts = [r['eval_count'] for r in iteration_results]
            prompt_stats = {
                "prompt": prompt,
                "avg_response_time": statistics.mean(response_times),
                "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "avg_eval_count": statistics.mean(eval_counts),
                "avg_speed": statistics.mean([r['eval_count']/r['eval_duration'] 
                                            for r in iteration_results if r['eval_duration'] > 0]),
                "all_results": iteration_results
            }
            all_results.append(prompt_stats)
        return self._analyze_performance(all_results)
    
    def test_quality(self, 
                    test_cases: List[Dict], 
                    model: str = "gemma3:270m") -> Dict:
        results = []
        for test_case in test_cases:
            prompt = test_case["prompt"]
            expected_keywords = test_case.get("expected_keywords", [])
            must_not_contain = test_case.get("must_not_contain", [])
            result = self.generate_response(prompt, model)

            response = result["response"].lower()
            keywords_found = []
            for keyword in expected_keywords:
                if keyword.lower() in response:
                    keywords_found.append(keyword)
            unwanted_found = []
            for unwanted in must_not_contain:
                if unwanted.lower() in response:
                    unwanted_found.append(unwanted)
            quality_score = len(keywords_found) / len(expected_keywords) if expected_keywords else 1.0
            case_result = {
                "prompt": prompt,
                "response": result["response"],
                "response_time": result["response_time"],
                "quality_score": quality_score,
                "keywords_found": keywords_found,
                "keywords_missing": [k for k in expected_keywords if k not in keywords_found],
                "unwanted_found": unwanted_found,
                "contains_unwanted": len(unwanted_found) > 0
            }
            results.append(case_result)
        return self._analyze_quality(results)
    
    def _analyze_performance(self, results: List[Dict]) -> Dict:
        response_times = [r['avg_response_time'] for r in results]
        speeds = [r['avg_speed'] for r in results]
        analysis = {
            "total_tests": len(results),
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "avg_generation_speed": statistics.mean(speeds),
            "min_speed": min(speeds),
            "max_speed": max(speeds),
            "detailed_results": results
        }
        print(f"\n{'='*50}")
        print("ИТОГИ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print(f"Среднее время ответа: {analysis['avg_response_time']:.2f} сек")
        print(f"Диапазон: {analysis['min_response_time']:.2f} - {analysis['max_response_time']:.2f} сек")
        print(f"Скорость генерации: {analysis['avg_generation_speed']:.1f} токенов/сек")
        return analysis
    
    def _analyze_quality(self, results: List[Dict]) -> Dict:
        quality_scores = [r['quality_score'] for r in results]
        response_times = [r['response_time'] for r in results]
        analysis = {
            "total_tests": len(results),
            "avg_quality_score": statistics.mean(quality_scores),
            "min_quality_score": min(quality_scores),
            "max_quality_score": max(quality_scores),
            "failed_keywords": sum(len(r['keywords_missing']) for r in results),
            "unwanted_content_cases": sum(1 for r in results if r['contains_unwanted']),
            "avg_response_time": statistics.mean(response_times),
            "detailed_results": results
        }
        print(f"\n{'='*50}")
        print("ИТОГИ КАЧЕСТВА:")
        print(f"Средний балл качества: {analysis['avg_quality_score']:.2%}")
        print(f"Пропущено ключевых слов: {analysis['failed_keywords']}")
        print(f"Найдено нежелательного контента: {analysis['unwanted_content_cases']}")
        return analysis
    
    def plot_results(self, performance_results: Dict, quality_results: Dict = None):
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        times = [r['avg_response_time'] for r in performance_results['detailed_results']]
        axes[0, 0].bar(range(len(times)), times)
        axes[0, 0].set_title('Время ответа по промптам')
        axes[0, 0].set_xlabel('Промпт')
        axes[0, 0].set_ylabel('Время (сек)')
        axes[0, 0].axhline(y=performance_results['avg_response_time'], 
                          color='r', linestyle='--', label='Среднее')
        speeds = [r['avg_speed'] for r in performance_results['detailed_results']]
        axes[0, 1].bar(range(len(speeds)), speeds)
        axes[0, 1].set_title('Скорость генерации по промптам')
        axes[0, 1].set_xlabel('Промпт')
        axes[0, 1].set_ylabel('Токенов/сек')

        axes[0, 1].axhline(y=performance_results['avg_generation_speed'], 
                          color='r', linestyle='--', label='Среднее')
        if quality_results:
            quality_scores = [r['quality_score'] for r in quality_results['detailed_results']]
            axes[1, 0].bar(range(len(quality_scores)), quality_scores)
            axes[1, 0].set_title('Качество ответов по тестам')
            axes[1, 0].set_xlabel('Тест')
            axes[1, 0].set_ylabel('Балл качества')
            axes[1, 0].axhline(y=quality_results['avg_quality_score'], 
                              color='r', linestyle='--', label='Среднее')
            response_times = [r['response_time'] for r in quality_results['detailed_results']]
            axes[1, 1].hist(response_times, bins=10, edgecolor='black')
            axes[1, 1].set_title('Распределение времени ответа')
            axes[1, 1].set_xlabel('Время (сек)')
            axes[1, 1].set_ylabel('Частота')
        plt.tight_layout()
        output_dir = '/mnt/data'
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, 'llm_test_results.png')
        plt.savefig(out_path)
        print(f"Графики сохранены в: {out_path}")


def run_comprehensive_test():
    tester = OllamaTester()
    performance_prompts = [
        "Объясни идею бинарного поиска и его асимптотику за 4–5 предложений.",
        "Дана последовательность. Опиши алгоритм поиска максимальной подстроки с суммой ≥ K.",
        "Что такое динамическое программирование? Приведи типичный пример задачи.",
        "Объясни разницу между O(n log n) и O(n^2) на примере сортировок.",
        "Что такое НОД и как его находят алгоритмом Евклида?",
        "Объясни идею алгоритма Дейкстры и его временную сложность.",
        "В чем разница между DFS и BFS и где каждый применяется?",
        "Что такое жадный алгоритм? Приведи пример.",
        "Опиши алгоритм бинарного поиска и условия его применимости.",
        "Что такое динамическое программирование и когда его используют?",
        "Объясни, как работает сортировка слиянием.",
        "Чем quicksort отличается от heapsort?",
        "Опиши алгоритм поиска компонент связности в графе.",
        "Что такое топологическая сортировка?",
        "Как работает алгоритм Евклида?",
        "Что такое дерево отрезков и какие операции оно поддерживает?",
        "Для чего используется Fenwick tree?",
        "Объясни, что такое хеш-таблица и коллизии.",
        "В чем разница между стеком и очередью?",
        "Что такое приоритетная очередь?",
        "Как работает DSU с эвристиками?",
        "Что такое декартово дерево?",
        "Опиши структуру данных sparse table.",
        "Когда лучше использовать multiset?",
        "Чем map отличается от unordered_map?",
        "Объясни DP на примере задачи о рюкзаке.",
        "Что такое оптимизация по префиксам в DP?",
        "Когда применяют DP по битмаскам?",
        "В чем идея LIS за O(n log n)?",
        "Опиши DP для подсчета количества путей на решетке.",
        "Что такое переходы состояний в DP?",
        "Чем отличается рекурсивное DP от итеративного?",
        "Что такое мемоизация?",
        "Когда DP неприменимо?",
        "Как оценить сложность DP?",
        "Что такое минимальное остовное дерево?",
        "Чем алгоритм Крускала отличается от Прима?",
        "Как найти мосты в графе?",
        "Что такое точки сочленения?",
        "Как проверить граф на двудольность?",
        "Как работает алгоритм Флойда–Уоршелла?",
        "Что такое SCC и как их находят?",
        "Когда BFS дает кратчайший путь?",
        "Что такое поток в сети?",
        "Где применяется max-flow?",
        "Что такое простые числа?",
        "Как работает решето Эратосфена?",
        "Что такое НОД и НОК?",
        "Как найти обратный элемент по модулю?",
        "Сформулируй малую теорему Ферма.",
        "Что такое бинарное возведение в степень?",
        "Когда число имеет модульную инверсию?",
        "Что такое функция Эйлера?",
        "Как быстро проверить число на простоту?",

        "Что такое китайская теорема об остатках?",
        "Что такое биномиальный коэффициент?",
        "В чем разница между сочетаниями и перестановками?",
        "Что такое принцип включения-исключения?",
        "Сформулируй закон больших чисел.",
        "Что такое математическое ожидание?",
        "Чем дисперсия отличается от стандартного отклонения?",
        "Что такое случайная величина?",
        "Когда события независимы?",
        "Что такое геометрическое распределение?",
        "Приведи пример условной вероятности.",
        "Как определить ориентацию трех точек?",
        "Что такое векторное произведение в 2D?",
        "Как проверить пересечение отрезков?",
        "Что такое выпуклая оболочка?",
        "Опиши алгоритм Грэхема.",
        "В чем идея алгоритма Джарвиса?",
        "Как вычислить площадь многоугольника?",
        "Что такое полярный угол?",
        "Как найти расстояние от точки до прямой?",
        "Когда точки лежат на одной прямой?",
        "Что означает O(n log n)?",
        "Чем отличается O от Ω?",
        "Что такое амортизированная сложность?",
        "Как сравнивать алгоритмы по асимптотике?",
        "Когда O(n^2) допустимо?",
        "Что такое худший случай?",
        "Почему log n появляется в деревьях?",
        "Как влияет константа в асимптотике?",
        "Когда важна память, а не время?",
        "Что такое trade-off?",
        "Объясни, почему BFS на невзвешенном графе находит кратчайшие пути.",
        "Почему DP часто быстрее полного перебора?",
        "Когда жадный алгоритм дает оптимум?",
        "Почему нельзя использовать Дейкстру с отрицательными весами?",
        "Почему сортировка сравнением не бывает быстрее O(n log n)?"
    ]
    quality_test_cases = [
        {
            "prompt": "Опиши алгоритм Дейкстры и его асимптотику.",
            "expected_keywords": ["граф", "кратчайший", "очередь", "приоритет", "O"],
            "must_not_contain": ["отрицательный"]
        },
        {
            "prompt": "Что такое дерево отрезков и для каких задач оно используется?",
            "expected_keywords": ["отрезков", "запрос", "диапазон", "log"],
            "must_not_contain": ["O(n^2)"]
        },
        {
            "prompt": "Чем отличается BFS от DFS?",
            "expected_keywords": ["очередь", "стек", "глубину", "ширину"],
            "must_not_contain": ["поток"]
        },
        {
            "prompt": "Что такое простое число?",
            "expected_keywords": ["делится", "1", "само", "два"],
            "must_not_contain": ["любое"]
        },
        {
            "prompt": "Опиши решето Эратосфена.",
            "expected_keywords": ["простых", "массив", "кратные"],
            "must_not_contain": ["деление"]
        },
        {
            "prompt": "Опиши алгоритм Кнута–Морриса–Пратта.",
            "expected_keywords": ["префикс", "функция", "строка", "O(n)"],
            "must_not_contain": ["O(n^2)"]
        },
        {
            "prompt": "Что такое topological sort и когда он существует?",
            "expected_keywords": ["ориентированный", "ациклический", "DAG"],
            "must_not_contain": ["цикл"]
        },
        {
            "prompt": "Опиши идею алгоритма Флойда–Уоршелла.",
            "expected_keywords": ["все пары", "кратчайшие", "динамическое"],
            "must_not_contain": ["O(n log n)"]
        },
        {
            "prompt": "Что такое декартово дерево?",
            "expected_keywords": ["куча", "BST", "приоритет"],
            "must_not_contain": ["граф"]
        },
        {
            "prompt": "Для чего используется DSU?",
            "expected_keywords": ["система", "непересекающихся", "объединение"],
            "must_not_contain": ["очередь"]
        },
        {
            "prompt": "Что такое DP по битмаскам?",
            "expected_keywords": ["бит", "подмножество", "состояние"],
            "must_not_contain": ["жадный"]
        },
        {
            "prompt": "Опиши задачу о рюкзаке.",
            "expected_keywords": ["вес", "ценность", "максимум"],

            "must_not_contain": ["сортировка"]
        },
        {
            "prompt": "Что такое обратный элемент по модулю?",
            "expected_keywords": ["модулю", "НОД", "1"],
            "must_not_contain": ["вещественное"]
        },
        {
            "prompt": "Сформулируй малую теорему Ферма.",
            "expected_keywords": ["простое", "p", "mod"],
            "must_not_contain": ["составное"]
        },
        {
            "prompt": "Как определить ориентацию трёх точек на плоскости?",
            "expected_keywords": ["векторное", "произведение", "знак"],
            "must_not_contain": ["косинус"]
        },
        {
            "prompt": "Что такое выпуклая оболочка?",
            "expected_keywords": ["многоугольник", "все точки", "внутри"],
            "must_not_contain": ["произвольный"]
        },
        {
            "prompt": "Что такое дисперсия?",
            "expected_keywords": ["квадрат", "отклонение", "математического"],
            "must_not_contain": ["медиана"]
        },
        {
            "prompt": "Сформулируй закон больших чисел.",
            "expected_keywords": ["сходимость", "вероятность", "среднее"],
            "must_not_contain": ["детерминированный"]
        },
        {
            "prompt": "Как за O(n) найти количество подотрезков с суммой 0?",
            "expected_keywords": ["префиксные", "суммы", "словарь"],
            "must_not_contain": ["O(n^2)"]
        },
        {
            "prompt": "Как найти мосты в графе?",
            "expected_keywords": ["tin", "fup", "DFS"],
            "must_not_contain": ["BFS"]
        }
    ]
    print("="*60)
    print("ТЕСТИРОВАНИЕ LLM (OLLAMA)")
    print("="*60)
    print("\n1. ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("-"*60)
    perf_results = tester.test_performance(
        prompts=performance_prompts,
        model="gemma3:270m",
        iterations=2
    )
    print("\n2. ТЕСТ КАЧЕСТВА")
    print("-"*60)
    quality_results = tester.test_quality(
        test_cases=quality_test_cases,
        model="gemma3:270m"
    )
    print("\n3. ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ")
    tester.plot_results(perf_results, quality_results)
    print("\n" + "="*60)
    print("СВОДНЫЙ ОТЧЕТ")
    print("="*60)
    print(f"Производительность:")
    print(f"  • Среднее время ответа: {perf_results['avg_response_time']:.2f} сек")
    print(f"  • Скорость генерации: {perf_results['avg_generation_speed']:.1f} токенов/сек")
    if quality_results:
        print(f"\nКачество:")
        print(f"  • Средний балл качества: {quality_results['avg_quality_score']:.2%}")
        print(f"  • Тестов с проблемами: {quality_results['unwanted_content_cases']}")
    return {
        "performance": perf_results,
        "quality": quality_results
    }


if __name__ == "__main__":
    tester = OllamaTester()
    print("Быстрый тест одного запроса:")
    result = tester.test_single_request(
        prompt="Объясни, идею корневой декомпозиции, в двух предложениях",
        model="gemma3:270m"
    )
    results = run_comprehensive_test()
