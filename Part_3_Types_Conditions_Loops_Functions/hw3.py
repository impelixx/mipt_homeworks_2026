#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

CMD_INCOME = "income"
CMD_COST = "cost"
CMD_STATS = "stats"

DATE_LEN = 10
MONTHS_IN_YEAR = 12
FEBRUARY = 2
INCOME_ARGS = 3
MAX_LEN_OF_SPLIT_LINE = 3
COST_ARGS = 4
STATS_ARGS = 2

Income = tuple[int, int, int, float]
Cost = tuple[int, int, int, str, float]
Date = tuple[int, int, int]

THIRTY_DAY_MONTHS = (4, 6, 9, 11)

Stats = tuple[float, float, float, float, dict[str, float]]
IncomeStats = tuple[float, float]
CostStats = tuple[float, float, dict[str, float]]


def is_leap_year(year: int) -> bool:
    """
    Определяет сколько дней в году

    :param int year: Проверяемый год
    :return: True, если 366, иначе False.
    :rtype: bool
    """
    by_four = year % 4 == 0
    by_hundred = year % 100 == 0
    by_four_hundred = year % 400 == 0
    return by_four and (not by_hundred or by_four_hundred)


def _is_valid_date_format(date_string: str) -> bool:
    """
    Чекер на правильность формата даты

    :param str date_string: строка
    :return: True, если формат даты правильный, иначе False.
    :rtype: bool
    """
    if len(date_string) != DATE_LEN:
        return False
    split_by_dash = date_string.split("-")
    if len(split_by_dash) != MAX_LEN_OF_SPLIT_LINE:
        return False

    first, second, third = split_by_dash
    lengths = (len(first), len(second), len(third))
    return lengths == (2, 2, 4)


def _days_in_month(month: int, year: int) -> int:
    """
    количество дней в месяце для заданного года

    :param int month: Месяц
    :param int year: Год
    :return: Количество дней в месяце для заданного года
    :rtype: int
    """
    if month in THIRTY_DAY_MONTHS:
        return 30
    if month == FEBRUARY:
        return 29 if is_leap_year(year) else 28
    return 31


def _is_real_date(day: int, month: int, year: int) -> bool:
    """
    Чекер на существование даты
    :param int day: День
    :param int month: Месяц
    :param int year: Год
    :return: True, если дата существует, иначе False.
    :rtype: bool
    """
    month_is_valid = 1 <= month <= MONTHS_IN_YEAR
    if not month_is_valid:
        return False
    return 1 <= day <= _days_in_month(month, year)


def _parse_date_numbers(parts: list[str]) -> Date | None:
    """
    Даты из списка строк

    :param list[str] parts: Список строк
    :return: Кортеж формата (день, месяц, год) или None, если ошибка.
    :rtype: tuple[int, int, int] | None
    """
    day_text, month_text, year_text = parts
    if not day_text.isdigit() or not month_text.isdigit() or not year_text.isdigit():
        return None

    return int(day_text), int(month_text), int(year_text)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсер даты формата DD-MM-YYYY из строки

    :param str maybe_dt: строка
    :return: typle формата (день, месяц, год) или None, если ошибка
    :rtype: tuple[int, int, int] | None
    """
    if not _is_valid_date_format(maybe_dt):
        return None

    parts = maybe_dt.split("-")
    parsed_date = _parse_date_numbers(parts)
    if parsed_date is None:
        return None

    if not _is_real_date(parsed_date[0], parsed_date[1], parsed_date[2]):
        return None
    return parsed_date


def _is_decimal_number(text: str) -> bool:
    """
    Чекер на десятичное число

    :param str text: строка
    :return: True, если строка - десятичное число, иначе False.
    :rtype: bool
    """
    if "." not in text:
        return text.isdigit()

    left, right = text.split(".", 1)
    has_parts = bool(left) and bool(right)
    contains_only_digits = left.isdigit() and right.isdigit()
    return has_parts and contains_only_digits


def parse_price(maybe_amount: str) -> float | None:
    """
    Парсер цены

    :param str maybe_amount: строка
    :return: Значение цены или None, если неправильно.
    :rtype: float | None
    """
    if maybe_amount.startswith("-"):
        return None

    normalized = maybe_amount.replace(",", ".")
    normalized = normalized.removeprefix("+")
    if not normalized or normalized.count(".") > 1:
        return None

    if not _is_decimal_number(normalized):
        return None

    amount = float(normalized)
    return amount if amount > 0 else None


def check_date(lhs: Date, rhs: Date) -> bool:
    """
    Проверяет, что даты нормально расположены

    :param tuple[int, int, int] lhs: Дата lhs в формате (день, месяц, год)
    :param tuple[int, int, int] rhs: Дата rhs в формате (день, месяц, год)
    :return: True, если lhs не позже rhs, иначе False.
    :rtype: bool
    """
    fst = (lhs[2], lhs[1], lhs[0])
    snd = (rhs[2], rhs[1], rhs[0])
    return fst <= snd


def money_formater(value: float) -> str:
    """
    Форматирует сумму денег в строку

    :param float value: Сумма денег
    :return: Отформатированная строка.
    :rtype: str
    """
    if value.is_integer():
        return str(int(value))
    formatted = f"{value:.2f}"
    return formatted.rstrip("0").rstrip(".")


def _income_totals(incomes: list[Income], cur_date: Date) -> IncomeStats:
    """
    находит суммарный доход и доход за месяц для заданной даты

    :param list[Income] incomes: Список доходов
    :param tuple[int, int, int] cur_date: Дата для статистики
    :return: Кортеж формата (суммарный доход, доход за месяц)
    :rtype: tuple[float, float]
    """
    query_month_year = (cur_date[1], cur_date[2])
    total_income = float(0)
    month_income = float(0)

    for income in incomes:
        if not check_date(_income_date(income), cur_date):
            continue
        amount = income[3]
        total_income += amount
        if (income[1], income[2]) == query_month_year:
            month_income += amount

    return total_income, month_income


def _income_date(income: Income) -> Date:
    """
    Возвращает дату из дохода.

    :param tuple[int, int, int, str, float] income: Доход
    :return: Дата дохода
    :rtype: tuple[int, int, int]
    """
    return income[0], income[1], income[2]


def _cost_date(cost: Cost) -> Date:
    """
    хелпер для получения даты из расходов

    :param tuple[int, int, int, str, float] cost: Расход
    :return: Дата расхода
    :rtype: tuple[int, int, int]
    """
    return cost[0], cost[1], cost[2]


def _cost_totals(costs: list[Cost], cur_date: Date) -> CostStats:
    """
    Хелпер для нахождения всего что связано c раходами в сумме

    :param list[Cost] costs: расходы
    :param tuple[int, int, int] cur_date: Дата
    :return: Кортеж формата (суммарный расход, расход за месяц, детализация по категориям)
    :rtype: tuple[float, float, dict[str, float]]
    """
    month_and_total_cost = [float(0), float(0)]
    categories: dict[str, float] = {}

    for cost in costs:
        if not check_date(_cost_date(cost), cur_date):
            continue
        month_and_total_cost[0] += cost[4]
        current_cost_date = (cost[1], cost[2])
        if current_cost_date != (cur_date[1], cur_date[2]):
            continue
        month_and_total_cost[1] += cost[4]
        cat = cost[3]
        categories.setdefault(cat, float(0))
        categories[cat] += cost[4]

    return month_and_total_cost[0], month_and_total_cost[1], categories


def _compose_stats(income_stats: IncomeStats, cost_stats: CostStats) -> Stats:
    """
    Объединяет стату

    :param tuple[float, float] income_stats: Кортеж формата (суммарный доход, доход за месяц)
    :param tuple[float, float, dict[str, float]] cost_stats: Кортеж (суммарный расход, расход за месяц, детализация)
    :return: Кортеж (суммарный доход, суммарный расход, доход за месяц, расход за месяц, детализация)
    :rtype: tuple[float, float, float, float, dict[str, float]]
    """
    income_total, income_month = income_stats
    cost_total, cost_month, categories = cost_stats
    return income_total, cost_total, income_month, cost_month, categories


def collect_stats(incomes: list[Income], costs: list[Cost], cur_date: Date) -> Stats:
    """
    Хелпер для статы на указанную дату

    :param list[Income] incomes: доходы
    :param list[Cost] costs: расходы
    :param tuple[int, int, int] cur_date: Дата
    :return: Стата за дату
    :rtype: tuple[float, float, float, float, dict[str, float]]
    """
    income_stats = _income_totals(incomes, cur_date)
    cost_stats = _cost_totals(costs, cur_date)
    return _compose_stats(income_stats, cost_stats)


def _profit_line(month_diff: float) -> str:
    """
    Хелпер для строки c прибылью/убытком

    :param float month_diff: разница между плюсом и минусом
    :return: Инфа o разнице
    :rtype: str
    """
    if month_diff >= 0:
        return f"B этом месяце прибыль составила {month_diff:.2f} рублей"
    return f"B этом месяце убыток составил {abs(month_diff):.2f} рублей"


def _build_details_lines(categories: dict[str, float]) -> list[str]:
    """
    Хелпер для детализации по категориям в статистике

    :param dict[str, float] categories: Словарь c категориями и их значениями
    :return: Список строк
    :rtype: list[str]
    """
    lines = ["", "Детализация (категория: сумма):"]
    for index, category_name in enumerate(sorted(categories), start=1):
        value = money_formater(categories[category_name])
        lines.append(f"{index}. {category_name}: {value}")
    return lines


def _stats_header(date_text: str, stats: Stats) -> list[str]:
    """
    Хелпер для заголовка в статистике

    :param str date_text: Дата заданная строкой
    :param tuple[float, float, float, float, dict[str, float]] stats: Стата
    :return: Список строк для заголовка статы
    """
    month_diff = stats[2] - stats[3]
    total_capital = stats[0] - stats[1]
    return [
        f"Ваша статистика по состоянию на {date_text}:",
        f"Суммарный капитал: {total_capital:.2f} рублей",
        _profit_line(month_diff),
        f"Доходы: {stats[2]:.2f} рублей",
        f"Расходы: {stats[3]:.2f} рублей",
    ]


def build_stats_output(
    parts: list[str],
    cur_date: Date,
    incomes: list[Income],
    costs: list[Cost],
) -> list[str]:
    """
    Простенький форматер для статы

    :param list[str] parts: Части stats
    :param tuple[int, int, int] cur_date: Дата
    :param list[Income] incomes: доходы
    :param list[Cost] costs: расходы
    :return: Список на вывод
    :rtype: list[str]
    """
    stats = collect_stats(incomes, costs, cur_date)
    lines = _stats_header(parts[1], stats)
    lines.extend(_build_details_lines(stats[4]))
    return lines


def handle_income(parts: list[str], incomes: list[Income]) -> None:
    """
    Хендлит income

    :param list[str] parts: Части команды income
    :param list[Income] incomes: Список доходов для добавления нового дохода
    """
    if len(parts) != INCOME_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_price(parts[1])
    if amount is None:
        print(NONPOSITIVE_VALUE_MSG)
        return

    date_tuple = extract_date(parts[2])
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return

    day, month, year = date_tuple
    incomes.append((day, month, year, amount))
    print(OP_SUCCESS_MSG)


def handle_cost(parts: list[str], costs: list[Cost]) -> None:
    """
    Хендлит cost

    :param list[str] parts: Части cost
    :param list[Cost] costs: Список расходов для добавления нового расхода
    """
    if len(parts) != COST_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return

    category = parts[1]
    if not category or "." in category or "," in category:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_price(parts[2])
    if amount is None:
        print(NONPOSITIVE_VALUE_MSG)
        return

    date_tuple = extract_date(parts[3])
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return

    costs.append((*date_tuple, category, amount))
    print(OP_SUCCESS_MSG)


def handle_stats(parts: list[str], incomes: list[Income], costs: list[Cost]) -> None:
    """
    Хендлит stats

    :param list[str] parts: Чacти stats
    :param list[Income] incomes: Список доходов
    :param list[Cost] costs: Список расходов
    """
    if len(parts) != STATS_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return

    cur_date = extract_date(parts[1])
    if cur_date is None:
        print(INCORRECT_DATE_MSG)
        return

    print("\n".join(build_stats_output(parts, cur_date, incomes, costs)))


def process_command(parts: list[str], incomes: list[Income], costs: list[Cost]) -> None:
    """
    Раскидывает команды по соответствующим обработчикам.

    :param list[str] parts: Части команды
    :param list[Income] incomes: Список доходов
    :param list[Cost] costs: Список расходов
    """
    command = parts[0]
    if command == CMD_INCOME:
        handle_income(parts, incomes)
        return
    if command == CMD_COST:
        handle_cost(parts, costs)
        return
    if command == CMD_STATS:
        handle_stats(parts, incomes, costs)
        return
    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    """
    Сердце программы, считывает команды и хендлит их, пока не будет пустой строки
    """
    incomes: list[Income] = []
    costs: list[Cost] = []

    while True:
        line = input().strip()

        if not line:
            break
        parts = line.split()
        process_command(parts, incomes, costs)


if __name__ == "__main__":
    main()
