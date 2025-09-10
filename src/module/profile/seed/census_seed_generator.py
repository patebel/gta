import random

import openpyxl

from model.seed import CensusSeed
from util.logging import log_warning


class SeedGeneratorCensus:
    def __init__(self, census_path):
        workbook = openpyxl.load_workbook(census_path)
        self.gender_list = self._init_gender(workbook)
        self.age_groups = self._init_age_groups(workbook)
        self.age_group_labour_force_participation = self._init_age_group_labour_force_participation(workbook)
        self.age_group_professional_position = self._init_age_group_professional_position(workbook)
        self.professional_position_monthly_net_income = self._init_professional_position_monthly_net_income(workbook)
        self.professional_position_main_occupational_group = self._init_professional_position_main_occupational_group(
            workbook)
        self.age_household_size = self._init_age_household_size(workbook)
        self.household_size_household_income = self._init_household_size_household_income(workbook)
        self.age_group_work_type = self._init_age_group_work_type(workbook)
        self.age_group_education_type = self._init_age_group_education_type(workbook, self.age_groups)
        self.labour_force_participation_age_group_main_income = self._init_labour_force_participation_age_group_main_income(
            workbook)

    def _init_gender(self, workbook):
        tab11 = workbook['Tab1.1']

        male = 'Männlich'
        male_count = int(tab11['B24'].value)
        female = 'Weiblich'
        female_count = int(tab11['B41'].value)
        gender_list = [(male, male_count), (female, female_count)]
        return gender_list

    def _init_age_groups(self, workbook):
        tab11 = workbook['Tab1.1']
        age_groups = []
        # Iterate over cells A8 to A21 and B8 to B21
        for row in range(8, 22):
            age = tab11['A' + str(row)].value.rstrip()
            count = int(tab11['B' + str(row)].value)
            age_groups.append((age, count))
        return age_groups

    def _init_age_group_labour_force_participation(self, workbook):
        tab11 = workbook['Tab1.1']
        age_group_labour_force_participation = {}
        # Iterate over cells A8 to A21 and B8 to B21
        for row in range(8, 22):
            age = tab11['A' + str(row)].value.rstrip()
            age_group_labour_force_participation.update({age: []})
            for labor_force_participation, column in [('Erwerbstätig', 'D'), ('Erwerbslos', 'E'),
                                                      ('Nichterwerbsperson', 'F')]:
                count = tab11[column + str(row)].value
                count = self.clean_count(count)

                age_group_labour_force_participation[age].append((labor_force_participation, count))
        return age_group_labour_force_participation

    def _init_age_group_professional_position(self, workbook):
        tab21 = workbook['Tab2.1']

        age_group_professional_position = {}
        for row in range(9, 16):
            age = tab21['A' + str(row)].value.rstrip()
            if '-' not in age:
                age_group_professional_position.update({age: []})
                for professional_position, column in [('Selbstständiger ohne Beschäftige(n)', 'D'),
                                                      ('Selbstständiger mit Beschäftige(n)', 'E'),
                                                      ('Beamte/Beamtin', 'G'),
                                                      ('Angestellte/-r', 'H'), ('Arbeiter/-in', 'I'),
                                                      ('Auszubildende/-r', 'J')]:
                    count = tab21[column + str(row)].value
                    count = self.clean_count(count)

                    age_group_professional_position[age].append((professional_position, count))
            else:
                age_1 = f'{age[0:2]} - {int(age[0:2]) + 5}'
                age_2 = f'{int(age[0:2]) + 5} - {int(age[0:2]) + 10}'
                age_group_professional_position.update({age_1: [], age_2: []})
                for professional_position, column in [('Selbstständiger ohne Beschäftige(n)', 'D'),
                                                      ('Selbstständiger mit Beschäftige(n)', 'E'),
                                                      ('Beamte/Beamtin', 'G'),
                                                      ('Angestellte/-r', 'H'), ('Arbeiter/-in', 'I'),
                                                      ('Auszubildende/-r', 'J')]:
                    count = tab21[column + str(row)].value
                    count = self.clean_count(count)

                    age_group_professional_position[age_1].append((professional_position, count))
                    age_group_professional_position[age_2].append((professional_position, count))

        return age_group_professional_position

    def _init_professional_position_monthly_net_income(self, workbook):
        tab23 = workbook['Tab2.3']

        professional_position_monthly_net_income = {}
        for row in range(10, 21):
            income = tab23['A' + str(row)].value
            for professional_position, column in [('Selbstständiger ohne Beschäftige(n)', 'D'),
                                                  ('Selbstständiger mit Beschäftige(n)', 'E'), ('Beamte/Beamtin', 'G'),
                                                  ('Angestellte/-r', 'H'), ('Arbeiter/-in', 'I'),
                                                  ('Auszubildende/-r', 'J')]:
                count = tab23[column + str(row)].value
                count = self.clean_count(count)

                if professional_position_monthly_net_income.get(professional_position) == None:
                    professional_position_monthly_net_income.update({professional_position: []})

                professional_position_monthly_net_income[professional_position].append((income, count))
        return professional_position_monthly_net_income

    def _init_professional_position_main_occupational_group(self, workbook):
        tab24 = workbook['Tab2.4']

        professional_position_main_occupational_group = {}
        for row in range(8, 55):
            main_occupational_group = tab24['A' + str(row)].value.rstrip()
            for professional_position, column in [('Selbstständiger ohne Beschäftige(n)', 'D'),
                                                  ('Selbstständiger mit Beschäftige(n)', 'E'), ('Beamte/Beamtin', 'G'),
                                                  ('Angestellte/-r', 'H'), ('Arbeiter/-in', 'I'),
                                                  ('Auszubildende/-r', 'J')]:
                count = tab24[column + str(row)].value
                count = self.clean_count(count)

                if professional_position_main_occupational_group.get(professional_position) == None:
                    professional_position_main_occupational_group.update({professional_position: []})

                professional_position_main_occupational_group[professional_position].append(
                    (main_occupational_group, count))
        return professional_position_main_occupational_group

    def _init_age_household_size(self, workbook):
        tab31 = workbook['Tab3.1']

        age_household_size = {}

        age_1 = 'unter 15'
        age_2 = '15 - 20'
        row_to_split = 10
        age_household_size.update({age_1: [], age_2: []})
        for household_size, column in [('Einpersonenhaushalt', 'C'), ('Mehrpersonenhaushalt mit 2 Personen', 'E'),
                                       ('Mehrpersonenhaushalt mit 3 Personen', 'F'),
                                       ('Mehrpersonenhaushalt mit 4 Personen', 'G'),
                                       ('Mehrpersonenhaushalt mit 5 und mehr Personen', 'H')]:
            count = tab31[column + str(row_to_split)].value
            count = self.clean_count(count)
            age_household_size[age_1].append((household_size, count))
            age_household_size[age_2].append((household_size, count))

        for row in range(11, 22):
            age = tab31['A' + str(row)].value.rstrip()
            age_household_size.update({age: []})
            for household_size, column in [('Einpersonenhaushalt', 'C'), ('Mehrpersonenhaushalt mit 2 Personen', 'E'),
                                           ('Mehrpersonenhaushalt mit 3 Personen', 'F'),
                                           ('Mehrpersonenhaushalt mit 4 Personen', 'G'),
                                           ('Mehrpersonenhaushalt mit 5 und mehr Personen', 'H')]:
                count = tab31[column + str(row)].value
                count = self.clean_count(count)

                age_household_size[age].append((household_size, count))

        age = '75 und älter'
        age_household_size.update({age: []})

        for household_size, column in [('Einpersonenhaushalt', 'C'), ('Mehrpersonenhaushalt mit 2 Personen', 'E'),
                                       ('Mehrpersonenhaushalt mit 3 Personen', 'F'),
                                       ('Mehrpersonenhaushalt mit 4 Personen', 'G'),
                                       ('Mehrpersonenhaushalt mit 5 und mehr Personen', 'H')]:
            count = 0
            for row in range(22, 25):
                count += self.clean_count(tab31[column + str(row)].value)
            age_household_size[age].append((household_size, count))
        return age_household_size

    def _init_household_size_household_income(self, workbook):
        tab41 = workbook['Tab4.1']
        household_size_household_income = {}
        for household_size, column in [('Einpersonenhaushalt', 'C'), ('Mehrpersonenhaushalt mit 2 Personen', 'E'),
                                       ('Mehrpersonenhaushalt mit 3 Personen', 'F'),
                                       ('Mehrpersonenhaushalt mit 4 Personen', 'G'),
                                       ('Mehrpersonenhaushalt mit 5 und mehr Personen', 'H')]:
            household_size_household_income[household_size] = []
            for row in range(10, 21):
                household_income = tab41['A' + str(row)].value.rstrip()
                count = tab41[column + str(row)].value
                count = self.clean_count(count)

                household_size_household_income[household_size].append((household_income, count))

        return household_size_household_income

    def _init_age_group_work_type(self, workbook):
        tab26 = workbook['Tab2.6']

        age_group_work_type = {}
        for row in range(9, 16):
            age = tab26['A' + str(row)].value.rstrip()
            if '-' not in age:
                age_group_work_type.update({age: []})
                for work_type, column in [('Vollzeit', 'C'), ('Teilzeit', 'D')]:
                    count = tab26[column + str(row)].value
                    count = self.clean_count(count)

                    age_group_work_type[age].append((work_type, count))
            else:
                age_1 = f'{age[0:2]} - {int(age[0:2]) + 5}'
                age_2 = f'{int(age[0:2]) + 5} - {int(age[0:2]) + 10}'
                age_group_work_type.update({age_1: [], age_2: []})
                for work_type, column in [('Vollzeit', 'C'), ('Teilzeit', 'D')]:
                    count = tab26[column + str(row)].value
                    count = self.clean_count(count)

                    age_group_work_type[age_1].append((work_type, count))
                    age_group_work_type[age_2].append((work_type, count))

        return age_group_work_type

    def _init_age_group_education_type(self, workbook, age_groups):
        tab18 = workbook['Tab1.8']
        age_education_type = {}
        for column in ['H', 'I', 'J', 'K', 'L']:
            age = tab18[str(column) + '4'].value.rstrip()
            age_education_type.update({age: []})
            education_count = 0
            for education_type, row in [('allgemeinbildende Schule', '9'),
                                        ('berufliche Schule', '15'),
                                        ('Hochschule/Berufsakademie', '17')]:
                count = tab18[str(column) + row].value
                count = self.clean_count(count)
                education_count += count
                age_education_type[age].append((education_type, count))

            total_age_group_count = next(count for age_group, count in age_groups if age_group == age)
            age_education_type[age].append((None, total_age_group_count - education_count))

        age = 'unter 15'
        age_education_type.update({age: []})
        education_count = 0
        for education_type, row in [('allgemeinbildende Schule', '9'),
                                    ('Kindertagesbetreuung', '8')]:
            under_15_count = 0
            for column in ['D', 'E', 'F', 'G']:
                count = tab18[column + row].value
                count = self.clean_count(count)
                under_15_count += count

            education_count += under_15_count
            age_education_type[age].append((education_type, under_15_count))

        total_age_group_count = next(count for age_group, count in age_groups if age_group == age)
        age_education_type[age].append((None, total_age_group_count - education_count))

        for age_group, count in age_groups:
            if age_group not in age_education_type:
                age_education_type.update({age_group: [(None, count)]})

        return age_education_type

    def _init_labour_force_participation_age_group_main_income(self, workbook):
        tab12 = workbook['Tab1.2']
        result = {}
        labour_force_participations = [
            ('Erwerbstätig', list(range(20, 25))),
            ('Erwerbslos', list(range(26, 31))),
            ('Nichterwerbsperson', list(range(32, 37)))]
        columns = ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

        for labour_force_participation, rows in labour_force_participations:
            result[labour_force_participation] = {}
            for column in columns:
                main_income = tab12[column + '4'].value.rstrip()
                for row in rows:
                    age_group = tab12['A' + str(row)].value.rstrip()

                    count = tab12[column + str(row)].value
                    count = self.clean_count(count)
                    if '15 -' in age_group:
                        start_age = int(age_group[0:2])
                        for replacement_age_group in [f'{start_age} - {start_age + 5}',
                                                      f'{start_age + 5} - {start_age + 10}']:

                            if replacement_age_group not in result[labour_force_participation]:
                                result[labour_force_participation][replacement_age_group] = []

                            result[labour_force_participation][replacement_age_group].append((main_income, count))
                    elif '-' in age_group:
                        start_age = int(age_group[0:2])
                        for replacement_age_group in [f'{start_age} - {start_age + 5}',
                                                      f'{start_age + 5} - {start_age + 10}',
                                                      f'{start_age + 10} - {start_age + 15}',
                                                      f'{start_age + 15} - {start_age + 20}', ]:

                            if replacement_age_group not in result[labour_force_participation]:
                                result[labour_force_participation][replacement_age_group] = []

                            result[labour_force_participation][replacement_age_group].append((main_income, count))
                    elif '65' in age_group:
                        for replacement_age_group in ['65 - 70', '70 - 75', '75 und älter']:

                            if replacement_age_group not in result[labour_force_participation]:
                                result[labour_force_participation][replacement_age_group] = []

                            result[labour_force_participation][replacement_age_group].append((main_income, count))
                    else:
                        if age_group not in result[labour_force_participation]:
                            result[labour_force_participation][age_group] = []

                        result[labour_force_participation][age_group].append((main_income, count))
        return result

    def clean_count(self, count):
        if count in ['X', '/']:
            count = 0
        elif type(count) != int:
            count = int(count.replace('(', '').replace(')', ''))
        return count

    # Functions
    def random_attribute(self, category_list):
        total_probability = sum(prob for _, prob in category_list)
        random_value = random.uniform(0, total_probability)
        cumulative_probability = 0
        for value, prob in category_list:
            cumulative_probability += prob
            if random_value < cumulative_probability:
                return value
        log_warning(f'Random value {random_value} is less than cumulative probability {cumulative_probability} '
                    f'for the category:\n{category_list}')
        return None

    def draw_attributes(self):
        result = {}

        gender = self.random_attribute(self.gender_list)
        age_group = self.random_attribute(self.age_groups)
        labour_force_participation = self.random_attribute(self.age_group_labour_force_participation[age_group])
        household_size = self.random_attribute(self.age_household_size[age_group])
        household_income = self.random_attribute(self.household_size_household_income[household_size])
        main_income = self.random_attribute(
            self.labour_force_participation_age_group_main_income[labour_force_participation][age_group])

        result.update({
            "Geschlecht": gender,
            "Altersgruppe": age_group,
            "Erwerbsbeteiligung": labour_force_participation,
            "Haushaltsgröße": household_size,
            "Überwiegender persönlicher Lebensunterhalt": main_income,
            "Haushaltsnettoeinkommen": household_income,
        })

        education_type = self.random_attribute(self.age_group_education_type[age_group])
        if education_type:
            result.update({
                "Art der aktuell besuchten Bildungseinrichtung": education_type,
            })

        if labour_force_participation == 'Erwerbstätig':
            professional_position = self.random_attribute(self.age_group_professional_position[age_group])
            if professional_position:
                work_type = self.random_attribute(self.age_group_work_type[age_group])

                monthly_net_income = self.random_attribute(
                    self.professional_position_monthly_net_income[professional_position])
                main_occupational_group = self.random_attribute(
                    self.professional_position_main_occupational_group[professional_position])

                result.update({
                    "Stellung im Beruf": professional_position,
                    "Art der ausgeübten Tätigkeit": work_type,
                    "Monatliches Nettoeinkommen": monthly_net_income,
                    "Hauptberufsgruppe": main_occupational_group,
                })

        return result

    def generate(self, ga_id):
        attributes = self.draw_attributes()
        return CensusSeed(ga_id, attributes)

    def generate_seeds(self, num):
        seeds = []
        for i in range(num):
            attributes = self.draw_attributes()
            seed = CensusSeed(i, attributes)
            seeds.append(seed)
        return seeds
