import csv
import sys
from collections import deque

number = 0
class State:
    def __init__(self):
        global number
        self.name = f"q{number}"
        number += 1
        self.transitions = {}
        self.epsilon_transitions = set()

class NFA:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept

    @staticmethod
    def from_symbol(symbol):
        start = State()
        accept = State()
        start.transitions[symbol] = {accept}
        return NFA(start, accept)

    @staticmethod
    def concatenate(nfa1, nfa2):
        nfa1.accept.epsilon_transitions.add(nfa2.start)
        return NFA(nfa1.start, nfa2.accept)

    @staticmethod
    def union(nfa1, nfa2):
        start = State()
        accept = State()
        start.epsilon_transitions.update({nfa1.start, nfa2.start})
        nfa1.accept.epsilon_transitions.add(accept)
        nfa2.accept.epsilon_transitions.add(accept)
        return NFA(start, accept)

    @staticmethod
    def kleene_star(nfa):
        # start = State()
        # accept = State()
        # start.epsilon_transitions.add(nfa.start)
        # start.epsilon_transitions.add(accept)
        # nfa.accept.epsilon_transitions.add(accept)
        # nfa.accept.epsilon_transitions.add(nfa.start)

        nfa.start.epsilon_transitions.add(nfa.accept)
        nfa.accept.epsilon_transitions.add(nfa.start)

        return NFA(nfa.start, nfa.accept)

    @staticmethod
    def plus(nfa):
        return NFA.concatenate(nfa, NFA.kleene_star(nfa))


def parse_regex_to_nfa(regex):
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


def traverse_states_with_transitions(state, states_transitions):
    visited = set()
    queue = deque([state])
    visited.add(state)

    while queue:
        current_state = queue.popleft()

        for symbol, next_states in current_state.transitions.items():
            for next_state in next_states:
                states_transitions.append((current_state.name, symbol, next_state.name))
                if next_state not in visited:
                    queue.append(next_state)
                    visited.add(next_state)

        for epsilon_state in current_state.epsilon_transitions:
            states_transitions.append((current_state.name, 'ε', epsilon_state.name))
            if epsilon_state not in visited:
                queue.append(epsilon_state)
                visited.add(epsilon_state)


def export_nfa_to_file(nfa, output_filename):
    states_transitions = []
    traverse_states_with_transitions(nfa.start, states_transitions)

    all_states = {nfa.start.name} | {t[0] for t in states_transitions} | {t[2] for t in states_transitions}
    input_symbols = {t[1] for t in states_transitions if t[1] != 'ε'}

    sorted_states = sorted(all_states)
    if nfa.start.name in sorted_states:
        sorted_states.remove(nfa.start.name)
        sorted_states.insert(0, nfa.start.name)

    with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        header1 = [''] + ["F" if state == nfa.accept.name else "" for state in sorted_states]
        writer.writerow(header1)
        header2 = [''] + sorted_states
        writer.writerow(header2)

        for symbol in sorted(input_symbols | {'ε'}):
            row = [symbol]
            for state in sorted_states:
                next_states = [t[2] for t in states_transitions if t[0] == state and t[1] == symbol]
                row.append(','.join(next_states) if next_states else '')
            writer.writerow(row)


if __name__ == "__main__":
    # if len(sys.argv) != 3:
    #     print("Использование: ./regexToNFA output.csv \"regex\"")
    #     sys.exit(1)

    output_file = sys.argv[1]
    regex = sys.argv[2]
    # regex = "((((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(rw*e|(r|r)))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|r))((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|w))*((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(q(q(rw*e|(i|w))|ew*e)|(u(rw*e|(i|w))|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(tw*e|t)))|(((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(rw*e|(r|r)))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(q(q(rw*e|(i|w))|ew*e)|(u(rw*e|(i|w))|ir)))|((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(rw*e|(i|w)))))(((((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|((q(rw*e|(r|r))|(ew*e|q))|tw*e))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|((qr|q)|(r|e))))((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|w))*((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(q(q(rw*e|(i|w))|ew*e)|(u(rw*e|(i|w))|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(tw*e|t)))|((((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|((q(rw*e|(r|r))|(ew*e|q))|tw*e))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|(q(q(rw*e|(i|w))|ew*e)|(u(rw*e|(i|w))|ir)))|(((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(i|w))|ew*e)|i(rw*e|(i|w)))|((q(rw*e|(i|w))|ew*e)|(tw*e|r)))))*(((((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|((q(rw*e|(r|r))|(ew*e|q))|tw*e))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|((qr|q)|(r|e))))((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|w))*((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*iw|t)|((((q(r|w)|q)|r)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|((q(rw*e|(r|r))|(ew*e|q))|tw*e))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*iw|(w|y)))|((((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(rw*e|(r|r)))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|r))((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|(q(qr|q)|(ur|ir)))|(y(i(q(r|w)|q)|(i(r|w)|i))*(i(qr|q)|(ir|t))|w))*((y(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|tw*e)((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*iw|t)|((r|w)(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(rw*e|(r|r)))((q(q(r|w)|q)|(u(r|w)|i))(i(q(r|w)|q)|(i(r|w)|i))*(i(q(rw*e|(r|r))|(ew*e|q))|(i(rw*e|(r|r))|w))|(q(q(rw*e|(r|r))|(ew*e|q))|u(rw*e|(r|r))))*iw)"

    nfa = parse_regex_to_nfa(regex)
    export_nfa_to_file(nfa, output_file)
