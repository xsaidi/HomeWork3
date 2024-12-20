# HomeWork3

# Учебный Конфигурационный Транслятор

## Описание

Этот проект представляет собой инструмент командной строки для работы с учебным конфигурационным языком. Инструмент преобразует текст из входного формата в выходной формат YAML. Также он проверяет синтаксис входного текста и выдает сообщения об ошибках в случае их обнаружения.

## Функциональность

1. **Обработка входного текста**: 
   - Поддержка однострочных комментариев с использованием символа `%`.
   - Поддержка массивов в формате `[ значение значение ... ]`.
   - Работа с именами, числами, строками и выражениями.

2. **Константы и вычисления**:
   - Объявление констант с помощью конструкции `def имя := значение;`.
   - Вычисление выражений на этапе трансляции в префиксной форме, например `$+ имя 1$`.
   - Поддержка арифметических операций (`+`, `-`, `*`) и функции `chr()`.

3. **Генерация выходного формата**:
   - Выходные данные представляются в формате YAML.
   - Поддержка Unicode символов.


## Использование

### Синтаксис входного языка

#### Комментарии
Однострочные комментарии начинаются с `%`:

% Это комментарий

#### Массивы
Массивы задаются в квадратных скобках:

[1 2 3]

#### Константы
Объявление констант:

def PI := 3.14;

#### Выражения
Примеры выражений:

def X := $ + 10 5$;
def Y := $chr 65$;

#### Пример конфигурации

% Константы
def GREETING := q(Hello, World!);
def PI := 3.1415;
def RADIUS := 10;
def AREA := $ * PI $* RADIUS RADIUS$$;

% Основные данные
name = q(Circle);
data = [AREA PI];

### Запуск программы

1. Сохраните входной текст в файл формата `.txt`, например, `input.txt`.
2. Запустите программу, передав файл через стандартный ввод:
   ```bash
   python main.py < input.txt

Программа выведет преобразованный YAML в стандартный вывод.

Пример результата

Входной файл: input.txt

% Пример
def A := 10;
def B := $ * A 2$;
key = [A B];

Вывод в формате YAML:

key:
- 10
- 20

Примеры использования

Пример 1: Геометрия

Входной файл: geometry.txt

def PI := 3.1415;
def R := 5;
def CIRCLE_AREA := $* PI $* R R$$;
shape = q(Circle);
area = CIRCLE_AREA;

Вывод:

shape: Circle
area: 78.53750000000001

Пример 2: Приветствие

Входной файл: greeting.txt

def GREETING := q(Hello, World!);
message = GREETING;

Вывод:

message: Hello, World!

Пример 3: Массив данных

Входной файл: array.txt

def A := 1;
def B := 2;
values = [A B $+ A B$];

Вывод:

values:
- 1
- 2
- 3

Требования
	•	Python 3.6+
	•	Модуль PyYAML для генерации YAML:

pip install pyyaml



Тестирование

Для запуска тестов используйте следующие шаги:
	1.	Сохраните тестовые примеры в файлы.
	2.	Запустите программу и проверьте выходные данные на соответствие ожидаемым.
