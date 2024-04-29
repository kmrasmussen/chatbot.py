import sys

def read_multiline_input():
    lines = []
    while True:
        line = input()
        if line.strip() == "EOF":  # User can type "EOF" to indicate end of input
            break
        lines.append(line)
    return '\n'.join(lines)

print("Paste your multi-line input below:")
multi_line_input = read_multiline_input()
print("Multi-line input received:")
print(multi_line_input)
