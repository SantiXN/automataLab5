import csv
import sys
import re


def minimize_moore(moore_filename, output_filename):
    transitions, outputs, states, input_symbols = read_moore(moore_filename)
    transitions, states = remove_unreachable_states_moore(transitions, states, input_symbols)

    groups = {}
    for state, output in outputs.items():
        if output not in groups:
            groups[output] = []
        groups[output].append(state)
    groups_map = {}
    for number, group in enumerate(groups.values(), start=1):
        for member in group:
            groups_map[member] = f'a{number}'

    is_changed = True
    while is_changed:
        is_changed = False
        state_to_transitions = {}

        for state in states:
            for input_symbol in input_symbols:
                transition = transitions[input_symbol][state]
                to_group = groups_map[transition]
                if state not in state_to_transitions.keys():
                    state_to_transitions[state] = []
                state_to_transitions[state].append(to_group)

        new_groups_map = create_new_groups(state_to_transitions, groups_map)

        if len(set(groups_map.values())) != len(set(new_groups_map.values())):
            is_changed = True
            groups_map = new_groups_map
        else:
            transitions, outputs = build_minimized_moore(transitions, outputs, new_groups_map)

    print_moore(output_filename, transitions, outputs, list(outputs.keys()), input_symbols)


def remove_unreachable_states_moore(transitions, states, input_symbols):
    reachable_states = set()
    states_to_visit = {states[0]}

    while states_to_visit:
        current_state = states_to_visit.pop()
        reachable_states.add(current_state)

        for input_symbol in input_symbols:
            if current_state in transitions[input_symbol]:
                next_state = transitions[input_symbol][current_state]
                if next_state not in reachable_states:
                    states_to_visit.add(next_state)

    for input_symbol in input_symbols:
        for state in list(transitions[input_symbol].keys()):
            if state not in reachable_states:
                del transitions[input_symbol][state]

    states = [state for state in states if state in reachable_states]
    return transitions, states


def build_minimized_moore(transitions, outputs, new_groups_map):
    new_transitions = {}
    new_outputs = {}

    for z, state_map in transitions.items():
        new_state_map = {}
        for state, next_state in state_map.items():
            new_state = new_groups_map[state]
            new_next_state = new_groups_map[next_state]

            if new_state not in new_state_map:
                new_state_map[new_state] = new_next_state

        new_transitions[z] = new_state_map

    for state, output in outputs.items():
        if state in new_groups_map.keys():
            new_outputs[new_groups_map[state]] = output

    return new_transitions, new_outputs


def create_new_groups(state_to_transitions, groups_map):
    transitions_to_group = {}
    new_groups_map = {}
    for state, ts in state_to_transitions.items():
        group = groups_map[state]

        transitions_key = tuple(ts)

        unique_key = (transitions_key, group)

        if unique_key in transitions_to_group:
            existing_group = transitions_to_group[unique_key]
            new_groups_map[state] = existing_group
        else:
            new_group_name = f'a{len(transitions_to_group) + 1}'
            transitions_to_group[unique_key] = new_group_name
            new_groups_map[state] = new_group_name

    return new_groups_map

def print_moore(output_filename, transitions, outputs, states, input_symbols):
    with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        header1 = [''] + list(outputs.values())
        writer.writerow(header1)
        header2 = [''] + states
        writer.writerow(header2)

        for input_symbol in input_symbols:
            row = [input_symbol]
            for state in states:
                next_states = transitions[input_symbol].get(state, [])
                row.append(','.join(next_states) if next_states else '')
            writer.writerow(row)


def read_moore(moore_filename):
    transitions = {}
    input_symbols = []
    outputs = {}

    with open(moore_filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        headers = next(reader)
        output_symbols = headers[1:]
        states_row = next(reader)
        states = states_row[1:]

        for state, output_symbol in zip(states, output_symbols):
            outputs[state] = output_symbol

        for row in reader:
            input_symbol = row[0]
            input_symbols.append(input_symbol)
            transitions[input_symbol] = {}
            for i, state in enumerate(states):
                next_state = row[i + 1]
                transitions[input_symbol][state] = next_state

    return transitions, outputs, states, input_symbols

def read_moore2(moore_filename):
    transitions = {}
    input_symbols = []
    outputs = {}

    with open(moore_filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        headers = next(reader)
        output_symbols = headers[1:]
        states_row = next(reader)
        states = states_row[1:]

        for state, output_symbol in zip(states, output_symbols):
            outputs[state] = output_symbol

        for row in reader:
            input_symbol = row[0]
            input_symbols.append(input_symbol)
            transitions[input_symbol] = {}
            for i, state in enumerate(states):
                next_state = row[i + 1]
                # Разделяем состояния по запятой и создаем список
                next_states_list = next_state.split(',') if next_state else []
                transitions[input_symbol][state] = next_states_list

    return transitions, outputs, states, input_symbols






def compute_epsilon_closure(states, transitions):
    epsilon_closure = {}

    for state in states:
        # Инициализируем замыкание текущим состоянием
        closure = set([state])
        stack = [state]

        # Пока есть состояния для обработки
        while stack:
            current = stack.pop()
            # Если есть переходы по 'ε', добавляем их в closure
            if 'ε' in transitions and current in transitions['ε']:
                for next_state in transitions['ε'][current]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)

        # Сохраняем замыкание в виде строки
        epsilon_closure[state] = ','.join(sorted(closure))

    return epsilon_closure


def has_final_state(states_str, outputs):
    states = states_str.split(',')
    for state in states:
        if state in outputs and outputs[state] == 'F':
            return True
    return False


def unique_sorted_states(states_set):
    # Преобразуем множество строк в список
    states_list = set()
    for states in states_set:
        # Разделяем каждую строку по запятой и добавляем в множество
        states_list.update(states.split(','))

    # Сортируем состояния по номеру
    sorted_states = sorted(states_list, key=lambda x: (int(x[1:]), x))

    # Объединяем отсортированные состояния в одну строку
    result = ','.join(sorted_states)
    return result


def get_dfa_outputs(dfa_states, dfa_final_states):
    outputs = {state: '' for state in dfa_states}
    for state in dfa_states:
        if state in dfa_final_states:
            outputs[state] = "F"

    return outputs


def rename_states(states, transitions, outputs):
    # Создаем словарь для сопоставления старых названий с новыми
    state_mapping = {state: f's{i}' for i, state in enumerate(states)}

    # Создаем новый список состояний
    new_states = list(state_mapping.values())

    # Заменяем названия состояний в outputs
    new_outputs = {state_mapping[state]: value for state, value in outputs.items()}

    # Заменяем названия состояний в transitions
    new_transitions = {}
    for symbol, state_dict in transitions.items():
        new_transitions[symbol] = {}
        for state, next_states in state_dict.items():
            # Заменяем состояния в ключах и значениях
            new_key = state_mapping.get(state, state)  # Получаем новое название или оставляем старое
            new_next_states = [state_mapping.get(next_state, next_state) for next_state in next_states]
            new_transitions[symbol][new_key] = new_next_states

    return new_states, new_transitions, new_outputs


def nfa_to_dfa(input_file, output_file):
    transitions, outputs, states, input_symbols = read_moore2(input_file)
    if 'ε' in input_symbols:
        input_symbols.remove('ε')

    epsilon_closure = compute_epsilon_closure(states, transitions)
    print(epsilon_closure)

    dfa_transitions = {symbol: {} for symbol in input_symbols}
    dfa_states = []
    dfa_start_state = epsilon_closure[states[0]]
    dfa_final_states = set()

    stack = [dfa_start_state]
    visited = set()

    while stack:
        current_dfa_state = stack.pop()
        if current_dfa_state in visited:
            continue
        visited.add(current_dfa_state)
        dfa_states.append(current_dfa_state)

        if has_final_state(current_dfa_state, outputs):
            dfa_final_states.add(current_dfa_state)

        # Обрабатываем переходы для всех символов кроме 'ε'
        for symbol in input_symbols:
            next_states = set()
            for nfa_state in current_dfa_state.split(','):
                if symbol in transitions and nfa_state in transitions[symbol]:
                    next_states.update(transitions[symbol][nfa_state])

            epsilon_closure_next_states = set()
            for state in next_states:
                epsilon_closure_next_states.add(epsilon_closure[state])
            sorted_states = unique_sorted_states(epsilon_closure_next_states)
            if sorted_states and sorted_states not in visited:
                stack.append(sorted_states)

            if current_dfa_state not in dfa_transitions[symbol]:
                dfa_transitions[symbol][current_dfa_state] = []
            dfa_transitions[symbol][current_dfa_state].append(sorted_states)

    dfa_outputs = get_dfa_outputs(dfa_states, dfa_final_states)

    dfa_states, dfa_transitions, dfa_outputs = rename_states(dfa_states, dfa_transitions, dfa_outputs)

    print_moore(output_file, dfa_transitions, dfa_outputs, dfa_states, input_symbols)


def main():
    if len(sys.argv) != 3:
        print("Использование:")
        print("program <output.csv> <regular_expression>")
        sys.exit(1)

    output_file = sys.argv[1]
    regular_expression = sys.argv[2]




if __name__ == "__main__":
    main()
