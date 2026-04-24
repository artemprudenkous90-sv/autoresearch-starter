# AutoResearch Starter

Автономный цикл ML-экспериментов — вдохновлён проектом Андрея Карпати (март 2026).

Агент сам генерирует гипотезы, запускает эксперименты, делает commit при улучшении и откатывается при регрессии.

## Быстрый старт

```bash
git clone https://github.com/artemprudenkous90-sv/autoresearch-starter
cd autoresearch-starter
pip install -r requirements.txt

# Проверь что всё работает
python train.py --epochs 5
# Последняя строка: METRIC: val_loss=X.XXXX
```

## Запуск авторесерча

Открой папку в Claude Code и напиши:

```
запусти авторесерч
```

или

```
start autoresearch
```

Агент:
1. Прочитает `research_directions.md` — список гипотез для проверки
2. Запустит `python train.py` с текущим baseline
3. Будет итеративно пробовать гипотезы, коммитя только улучшения

## Структура

```
autoresearch-starter/
├── train.py                  # Обучающий скрипт (GPU-ready, 4090+)
├── research_directions.md    # Гипотезы для проверки
├── experiment_log.md         # История экспериментов
├── requirements.txt
└── .claude/
    └── skills/
        └── autoresearch/
            └── SKILL.md      # Навык для Claude Code (автоустановка)
```

## Метрика

Скрипт обязательно выводит последней строкой:
```
METRIC: val_loss=0.4231
```

Авторесерч парсит эту строку и решает: commit (если лучше) или revert (если хуже).

## Адаптация под свою задачу

1. Замени `train.py` своим скриптом — главное чтобы он печатал `METRIC: <name>=<value>` последней строкой
2. Обнови `research_directions.md` своими гипотезами
3. Запусти авторесерч

## Требования

- Python 3.10+
- PyTorch 2.0+ (CUDA автоматически если есть GPU)
- Claude Code с установленным навыком `autoresearch` (уже в `.claude/skills/`)
