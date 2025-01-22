import csv
import sys

number = 0
class State:
    """
    Представляет состояние автомата.
    """
    def __init__(self):
        global number
        self.name = f"q{number}"
        number += 1
        self.transitions = {}  # Переходы {символ: множество состояний}
        self.epsilon_transitions = set()  # Епсилон-переходы


class NFA:
    """
    Представляет недетерминированный конечный автомат (НКА).
    """
    def __init__(self, start, accept):
        self.start = start  # Начальное состояние
        self.accept = accept  # Конечное состояние

    @staticmethod
    def from_symbol(symbol):
        """Создает НКА для одиночного символа."""
        start = State()
        accept = State()
        start.transitions[symbol] = {accept}
        return NFA(start, accept)

    @staticmethod
    def concatenate(nfa1, nfa2):
        """Конкатенация двух НКА."""
        nfa1.accept.epsilon_transitions.add(nfa2.start)
        return NFA(nfa1.start, nfa2.accept)

    @staticmethod
    def union(nfa1, nfa2):
        """Объединение двух НКА."""
        start = State()
        accept = State()
        start.epsilon_transitions.update({nfa1.start, nfa2.start})
        nfa1.accept.epsilon_transitions.add(accept)
        nfa2.accept.epsilon_transitions.add(accept)
        return NFA(start, accept)

    @staticmethod
    def kleene_star(nfa):
        """Клини-звезда для НКА."""
        start = State()
        accept = State()
        start.epsilon_transitions.update({nfa.start, accept})
        nfa.accept.epsilon_transitions.update({nfa.start, accept})
        return NFA(start, accept)

    @staticmethod
    def plus(nfa):
        """Операция "+" (один или более раз)."""
        return NFA.concatenate(nfa, NFA.kleene_star(nfa))


def parse_regex_to_nfa(regex):
    """
    Разбирает регулярное выражение в НКА, используя алгоритм Томпсона.
    Поддерживает +, *, |, () и неявную конкатенацию.
    """
    stack = []
    operators = []

    def apply_operator():
        operator = operators.pop()
        if operator == '*':
            nfa = stack.pop()
            stack.append(NFA.kleene_star(nfa))
        elif operator == '+':
            nfa = stack.pop()
            stack.append(NFA.plus(nfa))
        elif operator == '|':
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            stack.append(NFA.union(nfa1, nfa2))
        elif operator == '.':
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            stack.append(NFA.concatenate(nfa1, nfa2))

    def precedence(op):
        if op == '*':
            return 3
        if op == '+':
            return 3
        if op == '.':
            return 2
        if op == '|':
            return 1
        return 0

    explicit_concat = ""
    for i in range(len(regex)):
        explicit_concat += regex[i]
        if i + 1 < len(regex):
            if (regex[i].isalnum() or regex[i] == ')') and \
                    (regex[i + 1].isalnum() or regex[i + 1] in '('):
                explicit_concat += '.'
            elif regex[i] in '*+' and (regex[i + 1].isalnum() or regex[i + 1] == '('):
                explicit_concat += '.'

    for char in explicit_concat:
        if char.isalnum():
            stack.append(NFA.from_symbol(char))
        elif char == '(':
            operators.append(char)
        elif char == ')':
            while operators and operators[-1] != '(':
                apply_operator()
            operators.pop()
        elif char in '*+|.':
            while (operators and operators[-1] != '(' and
                   precedence(operators[-1]) >= precedence(char)):
                apply_operator()
            operators.append(char)

    while operators:
        apply_operator()

    return stack.pop()


def traverse_states_with_transitions(state, visited, states_transitions):
    if state in visited:
        return
    visited.add(state)

    for symbol, next_states in state.transitions.items():
        for next_state in next_states:
            states_transitions.append((state.name, symbol, next_state.name))
            traverse_states_with_transitions(next_state, visited, states_transitions)

    for epsilon_state in state.epsilon_transitions:
        states_transitions.append((state.name, 'ε', epsilon_state.name))
        traverse_states_with_transitions(epsilon_state, visited, states_transitions)


def export_nfa_to_file(nfa, output_filename):
    """Экспортирует НКА в файл в формате CSV в требуемом формате."""
    states_transitions = []
    visited = set()
    traverse_states_with_transitions(nfa.start, visited, states_transitions)

    all_states = {nfa.start.name} | {t[0] for t in states_transitions} | {t[2] for t in states_transitions}
    input_symbols = {t[1] for t in states_transitions}

    with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        header1 = [''] + ["F" if state == nfa.accept.name else "" for state in sorted(all_states)]
        writer.writerow(header1)
        header2 = [''] + sorted(all_states)
        writer.writerow(header2)

        for symbol in sorted(input_symbols):
            row = [symbol]
            for state in sorted(all_states):
                next_states = [t[2] for t in states_transitions if t[0] == state and t[1] == symbol]
                row.append(','.join(next_states) if next_states else '')
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: ./regexToNFA output.csv \"regex\"")
        sys.exit(1)

    output_file = sys.argv[1]
    regex = sys.argv[2]

    nfa = parse_regex_to_nfa(regex)
    export_nfa_to_file(nfa, output_file)
    print(f"НКА для регулярного выражения '{regex}' экспортирован в '{output_file}'")
