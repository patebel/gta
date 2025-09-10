import numpy as np
import pandas as pd

from model.seed import MiD2017Seed

seed_config = {
    'bland': 11,
    'attribute_variables': [  # 'P_VAUTO', 'vpedrad',
        'HP_SEX', 'HP_ALTER',
        'HP_TAET', 'P_PENDLER', 'P_HOFF1', 'P_HOFF2', 'P_MIG',
        'P_BIL',  # 'gesein', 'mobein',
        'hhgr_gr', 'anzauto_gr3', 'hheink_gr2', 'oek_status',
        'hhtyp2', 'mobtyp'],
    'additional_variables': ['HP_ID', 'H_ID', 'P_ID',
                             'P_GEW',
                             'ST_MONAT', 'ST_JAHR', 'ST_WOTAG', 'ST_WOCHE',
                             # Maybe add "übliche Nutzungen" eg 37 - 45
                             # Maybe Zufriedenheit, gerne eg 113 -120
                             # Stichtag:
                             # Evtl
                             'P_STWG1', 'P_RBW',
                             # Besser
                             'anzwege3', 'anzkm',
                             'persmin1'
                             ],
    'variables_mapping_path': 'data/census/B1_Standard-Datensatzpaket/Codepl„ne/MiD2017_Codepl„ne_B1_Standard.xlsx'
}


class SeedGeneratorMiD:
    def __init__(self, census_path, seed_config=seed_config):
        data = pd.read_csv(census_path, sep=';')
        # Filter data to desired region
        data = data[data['BLAND'] == seed_config['bland']]
        data['P_GEW'] = data['P_GEW'].str.replace(',', '.').astype(float)

        variables_mapping_path = seed_config['variables_mapping_path']
        code_label_mapping = code_label_mapping_from_excel(variables_mapping_path)

        attribute_variables = seed_config['attribute_variables']
        additional_variables = seed_config['additional_variables']

        # Process each row: store (attributes, additional_data, P_GEW)
        self.original_data = data.apply(
            lambda row: (
                get_variable_labels_for(row, attribute_variables, code_label_mapping),
                get_variable_labels_for(row, additional_variables, code_label_mapping),
                row['P_GEW']
            ),
            axis=1
        ).tolist()

    def generate_seeds(self, num_agents: int) -> list[MiD2017Seed]:
        """
        Generate exactly num_agents agents using a Truncate, Replicate, Sample (TRS) approach.
        The method truncates the fractional part of each scaled weight, then samples the remaining
        agents based on the fractional parts (probabilistic sampling).
        """
        seeds = []
        total_weight = sum(p for (_, _, p) in self.original_data)
        print(total_weight)
        scale = num_agents / total_weight if total_weight > 0 else 1

        # Store agents with integer parts and fractional remainders
        integer_counts = []
        fractional_parts = []

        for attributes, additional_data, weight in self.original_data:
            scaled_weight = weight * scale
            int_part = int(np.floor(scaled_weight))
            frac_part = scaled_weight - int_part
            integer_counts.append((attributes, additional_data, int_part))
            fractional_parts.append((attributes, additional_data, frac_part))

        # Add agents from integer part
        agent_id = 0
        for attributes, additional_data, count in integer_counts:
            for _ in range(count):
                seeds.append(MiD2017Seed(agent_id, attributes, additional_data))
                agent_id += 1

        # Number of agents still needed
        remaining = num_agents - len(seeds)
        if remaining > 0:
            # Sample based on normalized fractional parts
            total_fraction = sum(frac for _, _, frac in fractional_parts)
            probabilities = [frac / total_fraction if total_fraction > 0 else 0 for _, _, frac in fractional_parts]
            sampled_indices = np.random.choice(len(fractional_parts), size=remaining, p=probabilities)
            for idx in sampled_indices:
                attributes, additional_data, _ = fractional_parts[idx]
                seeds.append(MiD2017Seed(agent_id, attributes, additional_data))
                agent_id += 1

        return seeds


def create_variable_dict(df):
    columns_to_ffill = ['Variable', 'Variablenlabel', 'Messniveau', 'Format']
    df[columns_to_ffill] = df[columns_to_ffill].ffill()

    variable_dict = {}
    grouped = df.groupby('Variable')
    for var, group in grouped:
        value_label_mapping = {str(k): str(v) for k, v in zip(group['Wert'], group['Wertelabel'])}
        variable_dict[var] = {
            "Variable Label": str(group['Variablenlabel'].iloc[0]),
            "Messniveau": str(group['Messniveau'].iloc[0]),
            "Format": str(group['Format'].iloc[0]),
            "Wert-Wertelabel": value_label_mapping
        }
    return variable_dict


def code_label_mapping_from_excel(file_path):
    excel_dict = {}
    xls = pd.ExcelFile(file_path)
    for sheet_name in ['Personen']:
        df = pd.read_excel(file_path, header=1, sheet_name=sheet_name)
        excel_dict[sheet_name] = create_variable_dict(df)
    return excel_dict


def get_variable_labels_for(person, variables, code_label_mapping):
    code_label_mapping = code_label_mapping['Personen']
    long_variable_labels_dict = {}
    for variable in variables:
        code = str(person[variable])
        long_variable = code_label_mapping[variable]['Variable Label']
        label = code_label_mapping[variable]['Wert-Wertelabel'].get(code)
        if not label:
            label = code
        long_variable_labels_dict[long_variable] = label
    return long_variable_labels_dict
