import json
import time
from datasketch import HyperLogLog

LOG_FILE = "lms-stage-access.log"


def read_ip_addresses(path: str):
    """Генерація IP-адрес з лог-файлу, ігноруючи некоректні рядки."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    log_entry = json.loads(line)
                    remote_address = log_entry.get("remote_addr")
                    if remote_address:
                        yield remote_address
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Помилка: файл '{path}' не знайдено.")
        return


def count_unique_ip_address_set(path: str) -> int | None:
    """Підрахунок унікальних IP через структуру set (точний метод)."""
    ip_addresses = read_ip_addresses(path)
    if ip_addresses is None:
        return None
    return len(set(ip_addresses))


def count_unique_ip_address_hll(path: str, precision: int = 14) -> int | None:
    """Підрахунок унікальних IP через HyperLogLog (наближений метод)."""
    hll = HyperLogLog(p=precision)
    ip_addresses = read_ip_addresses(path)
    if ip_addresses is None:
        return None
    for ip in ip_addresses:
        hll.update(ip.encode("utf-8"))
    return int(hll.count())


# --- Метод 1: Точний підрахунок ---
start = time.perf_counter()
exact_count = count_unique_ip_address_set(LOG_FILE)
exact_time = time.perf_counter() - start

# --- Метод 2: HyperLogLog ---
start = time.perf_counter()
hll_count = count_unique_ip_address_hll(LOG_FILE)
hll_time = time.perf_counter() - start

if exact_count is None or hll_count is None:
    print("Неможливо виконати порівняння. Перевірте файл логів.")
    exit(1)

# --- Похибка HLL ---
error = (abs(exact_count - hll_count) / exact_count * 100) if exact_count > 0 else 0

# --- Вивід у форматі завдання ---
print("\nРезультати порівняння:")
print(f"{'':30}{'Точний підрахунок':>20}{'HyperLogLog':>15}")
print(f"{'Унікальні елементи':30}{exact_count:>20.1f}{hll_count:>15.1f}")
print(f"{'Час виконання (сек.)':30}{exact_time:>20.2f}{hll_time:>15.2f}")
print(f"{'Похибка (%)':30}{'0.00':>20}{error:>15.2f}")