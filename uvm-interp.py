# Этап 4. Реализация арифметико-логического устройства (АЛУ)
#
# Цель: завершить реализацию интерпретатора, добавив поддержку
# вычислительных операций.
# Требования:
# 1. Реализовать выполнение команды побитовый арифметический сдвиг вправо.
# 2. Для реализованной команды написать и выполнить тестовую программу,
#    которая демонстрирует корректные вычисления с сохранением результата в
#    память для проверки.
# 3. Результат выполнения этапа сохранить в репозиторий стандартно
#    оформленным коммитом.

import argparse
import json
from collections import defaultdict

data_memory = defaultdict(int)
registers = [0] * 64
instruction_memory = []

def decode_ldc(instr_bytes):
    word = int.from_bytes(instr_bytes, 'little')
    const = (word >> 7) & 0x3FFFF
    addr = (word >> 25) & 0x3F
    return {'op': 'ldc', 'const': const, 'addr': addr}

def decode_read(instr_bytes):
    word = int.from_bytes(instr_bytes, 'little')
    offset = (word >> 7) & 0x7F
    addr_c = (word >> 14) & 0x3F
    addr_d = (word >> 20) & 0x3F
    return {'op': 'read', 'offset': offset, 'addr_src': addr_c, 'addr_dst': addr_d}

def decode_write(instr_bytes):
    word = int.from_bytes(instr_bytes, 'little')
    addr_b = (word >> 7) & 0x3F
    addr_c = (word >> 13) & 0x3F
    return {'op': 'write', 'addr_dst': addr_b, 'addr_src': addr_c}

def decode_rsh(instr_bytes):
    word = int.from_bytes(instr_bytes, 'little')
    addr_b = (word >> 7) & 0x3F
    offset_c = (word >> 13) & 0x7F
    offset_d = (word >> 20) & 0x7F
    addr_e = (word >> 27) & 0x3F
    addr_f = (word >> 33) & 0x3F
    return {
        'op': 'rsh',
        'addr_b': addr_b,
        'offset_c': offset_c,
        'offset_d': offset_d,
        'addr_e': addr_e,
        'addr_f': addr_f,
    }

opcodes = {
    101: (4, decode_ldc),
    73:  (4, decode_read),
    5:   (3, decode_write),
    75:  (5, decode_rsh),
}

def exec_ldc(instr):
    registers[instr['addr']] = instr['const']
    print(f"  exec: ldc const={instr['const']} to reg[{instr['addr']}] -> value: {registers[instr['addr']]}")

def exec_read(instr):
    base_addr = registers[instr['addr_src']]
    mem_addr = base_addr + instr['offset']
    value = data_memory[mem_addr]
    registers[instr['addr_dst']] = value
    print(f"  exec: read from mem[{mem_addr}] (reg[{instr['addr_src']}]={base_addr} + offset={instr['offset']}) -> value: {value}")
    print(f"        write value to reg[{instr['addr_dst']}]")

def exec_write(instr):
    value = registers[instr['addr_src']]
    dest_addr_reg_val = registers[instr['addr_dst']]
    data_memory[dest_addr_reg_val] = value
    print(f"  exec: write value {value} (from reg[{instr['addr_src']}]) to mem[{dest_addr_reg_val}] (addr from reg[{instr['addr_dst']}])")

def exec_rsh(instr):
    op1 = registers[instr['addr_f']]
    
    op2_base_addr = registers[instr['addr_e']]
    op2_mem_addr = op2_base_addr + instr['offset_c']
    op2 = data_memory[op2_mem_addr]
    
    result = op1 >> op2
    
    result_base_addr = registers[instr['addr_b']]
    result_mem_addr = result_base_addr + instr['offset_d']
    data_memory[result_mem_addr] = result
    
    print(f"  exec: rsh op1(reg[{instr['addr_f']}])={op1}, op2(mem[{op2_mem_addr}])={op2}")
    print(f"        result: {op1} >> {op2} = {result}")
    print(f"        store result to mem[{result_mem_addr}]")

executors = {
    'ldc': exec_ldc,
    'read': exec_read,
    'write': exec_write,
    'rsh': exec_rsh,
}

def run_interpreter(binary_path, dump_path, dump_range):
    global data_memory, registers, instruction_memory
    data_memory = defaultdict(int)
    registers = [0] * 64
    instruction_memory = []

    with open(binary_path, 'rb') as f:
        instruction_memory.extend(f.read())

    print(f"Program loaded: {len(instruction_memory)} bytes.")
    print("-" * 20)

    pc = 0
    while pc < len(instruction_memory):
        opcode = instruction_memory[pc] & 0x7F

        if opcode not in opcodes:
            print(f"Error: Unknown opcode {opcode} at address {pc}")
            break

        instr_size, decoder = opcodes[opcode]
        
        if pc + instr_size > len(instruction_memory):
            print(f"Error: Incomplete instruction at address {pc}")
            break

        instr_bytes = instruction_memory[pc : pc + instr_size]
        instr = decoder(instr_bytes)
        print(f"pc={pc:03d}: Decoding {instr['op']} ({instr_bytes.hex()}) -> {instr}")

        if instr['op'] in executors:
            executors[instr['op']](instr)
        else:
            print(f"  exec: No executor for {instr['op']}")

        pc += instr_size
        print("-" * 20)

    print("Execution finished.")

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
    parser = argparse.ArgumentParser(description="UVM Interpreter")
    parser.add_argument("binary_path", help="Path to the assembled binary file.")
    parser.add_argument("dump_path", help="Path to save the memory dump JSON file.")
    parser.add_argument(
        "--dump-range",
        default="0-255",
        help="Memory address range for the dump (e.g., '0-100')."
    )
    args = parser.parse_args()

    run_interpreter(args.binary_path, args.dump_path, args.dump_range)

if __name__ == "__main__":
    main()
