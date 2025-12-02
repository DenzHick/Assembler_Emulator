import yaml
import argparse
import sys

def asm_ldc(const, addr):
    op_a = 101
    op_b = const
    op_c = addr
    cmd = (op_c << 25) | (op_b << 7) | op_a
    return cmd.to_bytes(4, "little")

def asm_read(offset, addr1, addr2):
    op_a = 73
    op_b = offset
    op_c = addr1
    op_d = addr2
    cmd = (op_d << 20) | (op_c << 14) | (op_b << 7) | op_a
    return cmd.to_bytes(4, "little")

def asm_write(addr1, addr2):
    op_a = 5
    op_b = addr1
    op_c = addr2
    cmd = (op_c << 13) | (op_b << 7) | op_a
    return cmd.to_bytes(3, "little")

def asm_rsh(addr1, offset1, offset2, addr2, addr3):
    op_a = 75
    op_b = addr1
    op_c = offset1
    op_d = offset2
    op_e = addr2
    op_f = addr3
    cmd = (op_f << 33) | (op_e << 27) | (op_d << 20) | (op_c << 13) | (op_b << 7) | op_a
    return cmd.to_bytes(5, "little")

def asm(program):
    binary_code = b""
    for instruction in program:
        op = instruction["op"]
        if op == "ldc":
            binary_code += asm_ldc(instruction["const"], instruction["addr"])
        elif op == "read":
            binary_code += asm_read(instruction["offset"], instruction["addr1"], instruction["addr2"])
        elif op == "write":
            binary_code += asm_write(instruction["addr1"], instruction["addr2"])
        elif op == "rsh":
            binary_code += asm_rsh(instruction["addr1"], instruction["offset1"], instruction["offset2"], instruction["addr2"], instruction["addr3"])
        else:
            raise ValueError(f"Unknown instruction: {op}")
    return binary_code

def main():
    parser = argparse.ArgumentParser(description="UVM Assembler")
    parser.add_argument("input_file", help="Path to the source assembly file (e.g., uvm-input.yaml)")
    parser.add_argument("output_file", help="Path to the binary output file (e.g., uvm-output.bin)")
    parser.add_argument("--test", action="store_true", help="Enable test mode to print intermediate representation")
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r') as file:
            source = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}", file=sys.stderr)
        sys.exit(1)

    program = source.get('program')
    if not program:
        print("Error: 'program' key not found in the input file.", file=sys.stderr)
        sys.exit(1)

    if args.test:
        print("--- Intermediate Representation ---")
        for instruction in program:
            print(instruction)
        print("---------------------------------")

    try:
        binary_result = asm(program)
    except ValueError as e:
        print(f"Assembly Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output_file, "wb") as f:
        f.write(binary_result)

    print(f"Assembly successful. Output written to {args.output_file} ({len(binary_result)} bytes).")

    if args.test:
        print("\n--- Verification against specification tests ---")
        ldc_test = asm_ldc(const=29, addr=12)
        print(f"ldc(29, 12) -> {[hex(b) for b in ldc_test]} (Expected: ['0xe5', '0xe', '0x0', '0x18'])")
        read_test = asm_read(offset=46, addr1=50, addr2=50)
        print(f"read(46, 50, 50) -> {[hex(b) for b in read_test]} (Expected: ['0x49', '0x97', '0x2c', '0x3'])")
        write_test = asm_write(addr1=38, addr2=47)
        print(f"write(38, 47) -> {[hex(b) for b in write_test]} (Expected: ['0x5', '0xf3', '0x5'])")
        rsh_test = asm_rsh(addr1=6, offset1=36, offset2=35, addr2=19, addr3=11)
        print(f"rsh(6, 36, 35, 19, 11) -> {[hex(b) for b in rsh_test]} (Expected: ['0x4b', '0x83', '0x34', '0x9a', '0x16'])")

if __name__ == '__main__':
    main()
