def high_economic_filter(persons_data):
    return persons_data[(persons_data['oek_status'] == 4) | (persons_data['oek_status'] == 5)]


def medium_economic_filter(persons_data):
    return persons_data[persons_data['oek_status'] == 3]


def low_economic_filter(persons_data):
    return persons_data[(persons_data['oek_status'] == 2) | (persons_data['oek_status'] == 1)]


def full_time_or_learning_filter(persons_data):
    return persons_data[(persons_data['HP_TAET'] == 1) | (persons_data['HP_TAET'] == 9)]


def part_time_filter(persons_data):
    return persons_data[(persons_data['HP_TAET'] == 2) | (persons_data['HP_TAET'] == 3)]


def working_other_filter(persons_data):
    return persons_data[(persons_data['HP_TAET'] == 4) | (persons_data['HP_TAET'] == 5)]


def child_or_pupil_filter(persons_data):
    return persons_data[
        (persons_data['HP_TAET'] == 6) | (persons_data['HP_TAET'] == 7) | (persons_data['HP_TAET'] == 8)]


def student_filter(persons_data):
    return persons_data[persons_data['oek_status'] == 10]


def not_working_filter(persons_data):
    return persons_data[
        (persons_data['HP_TAET'] == 11) | (persons_data['HP_TAET'] == 13) | (persons_data['HP_TAET'] == 14) | (
                persons_data['HP_TAET'] == 15)]


def retired_filter(persons_data):
    return persons_data[persons_data['HP_TAET'] == 12]
