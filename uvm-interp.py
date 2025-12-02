# Этап 3. Интерпретатор и операции с памятью
#
# Цель: создать цикл интерпретации, реализовать модель памяти УВМ и
# выполнить базовые команды.
# Требования:
# 1. Интерпретатор должен принимать на вход аргументы командной строки:
#    – Путь к бинарному файлу с ассемблированной программой.
#    – Путь к файлу, куда будет сохранен дамп памяти после выполнения
#      программы.
#    – Диапазон адресов памяти для вывода дампа.
# 2. Для дампа с содержимым памяти должен использоваться формат JSON.
# 3. Реализовать модель памяти УВМ (например, в виде массивов). Память
#    команд и память данных должны быть разделены.
# 4. Реализовать основной цикл интерпретатора: чтение команды из бинарного
#    файла, перевод команды в промежуточное представление, выполнение.
# 5. Реализовать команды загрузки константы, а также чтение и запись в память.
# 6. Написать и выполнить тестовую программу, которая копирует массив с
#    одного адреса на другой, чтобы проверить корректность работы.
# 7. Результат выполнения этапа сохранить в репозиторий стандартно
#    оформленным коммитом.

import argparse
import json
from collections import defaultdict

# --- Модель памяти и состояния УВМ ---

# Память данных (адресуемая)
# defaultdict(int) автоматически создает ячейку со значением 0 при первом доступе
data_memory = defaultdict(int)

# Регистры (64 регистра, как в спецификации)
# Инициализируем все нулями
registers = [0] * 64

# Память команд (для загрузки байт-кода)
instruction_memory = []

# --- Декодеры инструкций ---
# Преобразуют байты обратно в понятные команды

def decode_ldc(instr_bytes):
    """Декодирует инструкцию ldc."""
    word = int.from_bytes(instr_bytes, 'little')
    # A (opcode) = word & 0x7F (не используем, т.к. уже знаем команду)
    const = (word >> 7) & 0x3FFFF  # 18 бит
    addr = (word >> 25) & 0x3F      # 6 бит
    return {'op': 'ldc', 'const': const, 'addr': addr}

def decode_read(instr_bytes):
    """Декодирует инструкцию read."""
    word = int.from_bytes(instr_bytes, 'little')
    offset = (word >> 7) & 0x7F     # 7 бит
    addr_c = (word >> 14) & 0x3F    # 6 бит
    addr_d = (word >> 20) & 0x3F    # 6 бит
    return {'op': 'read', 'offset': offset, 'addr_src': addr_c, 'addr_dst': addr_d}

def decode_write(instr_bytes):
    """Декодирует инструкцию write."""
    word = int.from_bytes(instr_bytes, 'little')
    addr_b = (word >> 7) & 0x3F     # 6 бит
    addr_c = (word >> 13) & 0x3F    # 6 бит
    return {'op': 'write', 'addr_dst': addr_b, 'addr_src': addr_c}

# Словарь, связывающий опкоды с их размером и функцией декодирования
# Опкод: (размер в байтах, функция-декодер)
opcodes = {
    101: (4, decode_ldc),
    73:  (4, decode_read),
    5:   (3, decode_write),
    # Опкод 75 (rsh) будет добавлен на следующих этапах
}

# --- Исполнители инструкций ---
# Выполняют логику команды, изменяя состояние УВМ

def exec_ldc(instr):
    """Выполняет загрузку константы в регистр."""
    registers[instr['addr']] = instr['const']
    print(f"  exec: ldc const={instr['const']} to reg[{instr['addr']}] -> value: {registers[instr['addr']]}")

def exec_read(instr):
    """Выполняет чтение из памяти."""
    base_addr = registers[instr['addr_src']]
    mem_addr = base_addr + instr['offset']
    value = data_memory[mem_addr]
    registers[instr['addr_dst']] = value
    print(f"  exec: read from mem[{mem_addr}] (reg[{instr['addr_src']}]={base_addr} + offset={instr['offset']}) -> value: {value}")
    print(f"        write value to reg[{instr['addr_dst']}]")


def exec_write(instr):
    """Выполняет запись в память."""
    value = registers[instr['addr_src']]
    dest_addr_reg_val = registers[instr['addr_dst']]
    data_memory[dest_addr_reg_val] = value
    print(f"  exec: write value {value} (from reg[{instr['addr_src']}]) to mem[{dest_addr_reg_val}] (addr from reg[{instr['addr_dst']}])")


# Словарь, связывающий имена операций с функциями-исполнителями
executors = {
    'ldc': exec_ldc,
    'read': exec_read,
    'write': exec_write,
}

# --- Основной цикл интерпретатора ---

def run_interpreter(binary_path, dump_path, dump_range):
    """
    Загружает, декодирует и выполняет программу из бинарного файла.
    """
    # 1. Загрузка программы в память команд
    with open(binary_path, 'rb') as f:
        instruction_memory.extend(f.read())

    print(f"Program loaded: {len(instruction_memory)} bytes.")
    print("-" * 20)

    # 2. Основной цикл (fetch-decode-execute)
    pc = 0  # Program Counter - счетчик команд
    while pc < len(instruction_memory):
        opcode = instruction_memory[pc] & 0x7F  # Первые 7 бит

        if opcode not in opcodes:
            print(f"Error: Unknown opcode {opcode} at address {pc}")
            break

        instr_size, decoder = opcodes[opcode]
        
        # Проверка, не выходим ли мы за пределы памяти команд
        if pc + instr_size > len(instruction_memory):
            print(f"Error: Incomplete instruction at address {pc}")
            break

        # Fetch (извлечение)
        instr_bytes = instruction_memory[pc : pc + instr_size]
        
        # Decode (декодирование)
        instr = decoder(instr_bytes)
        print(f"pc={pc:03d}: Decoding {instr['op']} ({instr_bytes.hex()}) -> {instr}")

        # Execute (выполнение)
        if instr['op'] in executors:
            executors[instr['op']](instr)
        else:
            print(f"  exec: No executor for {instr['op']}")

        pc += instr_size
        print("-" * 20)

    print("Execution finished.")

    # 3. Сохранение дампа памяти
    if dump_path and dump_range:
        start, end = map(int, dump_range.split('-'))
        memory_dump = {
            addr: data_memory[addr]
            for addr in range(start, end + 1)
            if addr in data_memory
        }
        
        with open(dump_path, 'w') as f:
            json.dump(memory_dump, f, indent=4)
        
        print(f"Memory dump ({start}-{end}) saved to {dump_path}")


def main():
    """
    Главная функция, обрабатывающая аргументы командной строки.
    """
    parser = argparse.ArgumentParser(description="UVM Interpreter")
    parser.add_argument("binary_path", help="Path to the assembled binary file.")
    parser.add_argument("dump_path", help="Path to save the memory dump JSON file.")
    parser.add_argument(
        "--dump-range",
        default="0-255",
        help="Memory address range for the dump (e.g., '0-100')."
    )
    args = parser.parse_args()

    run_interpreter(args.binary_path, args.dump_path, args.dump-range)


if __name__ == "__main__":
    main()
