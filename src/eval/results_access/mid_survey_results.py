import pandas as pd


class MidSurveyResults:
    def __init__(self, path, bland):
        persons_path = f'{path}/MiD2017_Personen.csv'
        self.persons_data = pd.read_csv(persons_path, sep=';')
        self.persons_data = self.persons_data[self.persons_data['BLAND'] == bland]

        routes_path = f'{path}/MiD2017_Wege.csv'
        self.routes_data = pd.read_csv(routes_path, sep=';')
        # Convert W_GEW from comma to decimal and cast to float
        self.routes_data['W_GEW'] = (
            self.routes_data['W_GEW']
            .astype(str)
            .str.replace(',', '.')
            .astype(float)
        )
        self.routes_data = self.routes_data[self.routes_data['BLAND'] == bland]

        # ─── Merge codes 3 & 4 into a single MIV category (3) ─────────────────
        def _map_hvm_to_grouped(hvm_code):
            if hvm_code in (3, 4):
                return 3
            else:
                return hvm_code

        self.routes_data['hvm_grouped'] = self.routes_data['hvm'].apply(_map_hvm_to_grouped)
        # Now valid hvm_grouped codes are {1 = Fuß, 2 = Fahrrad, 3 = MIV, 5 = ÖPV}.
        # ────────────────────────────────────────────────────────────────────────

    def get_person_ids(self, person_filter):
        if person_filter is not None:
            filtered_persons_data = person_filter(self.persons_data)
        else:
            filtered_persons_data = self.persons_data
        return list(filtered_persons_data['HP_ID'])

    def get_person(self, person_id):
        return self.persons_data[self.persons_data['HP_ID'] == int(person_id)]

    def get_routes(self, person_id):
        return self.routes_data[self.routes_data['HP_ID'] == int(person_id)]

    @staticmethod
    def get_weighted_grouping_by_single(routes_data, group_var, valid_codes):
        """
        Groups routes_data by one variable (group_var) using W_GEW as weights.
        Any rows whose group_var is NOT in valid_codes get redistributed proportionally.
        Returns a DataFrame with columns: [group_var, original_weight, final_weight, percentage].
        """
        df = routes_data[['W_GEW', group_var]].copy()

        valid_df = df[df[group_var].isin(valid_codes)].copy()
        agg_valid = (
            valid_df.groupby(group_var)['W_GEW']
            .sum()
            .reset_index(name='original_weight')
        )

        total_valid = agg_valid['original_weight'].sum()
        missing_weight = df[~df[group_var].isin(valid_codes)]['W_GEW'].sum()

        agg_valid['final_weight'] = (
                agg_valid['original_weight']
                + missing_weight * (agg_valid['original_weight'] / total_valid)
        )

        overall_weight = total_valid + missing_weight
        agg_valid['percentage'] = (agg_valid['final_weight'] / overall_weight) * 100

        return agg_valid

    @staticmethod
    def get_weighted_grouping_by_two(
            routes_data,
            group_var1,
            group_var2,
            valid_codes1,
            valid_codes2
    ):
        """
        Groups routes_data by two variables (group_var1, group_var2) using W_GEW weights.
        Any rows invalid in either dimension have their weights redistributed proportionally.
        Returns a DataFrame with columns: [group_var1, group_var2, original_weight, final_weight, percentage].
        """
        df = routes_data[['W_GEW', group_var1, group_var2]].copy()

        valid_df = df[
            df[group_var1].isin(valid_codes1) &
            df[group_var2].isin(valid_codes2)
            ].copy()
        agg_valid = (
            valid_df.groupby([group_var1, group_var2])['W_GEW']
            .sum()
            .reset_index(name='original_weight')
        )

        total_by_g1 = agg_valid.groupby(group_var1)['original_weight'].sum().to_dict()
        overall_valid = sum(total_by_g1.values())

        missing_g1_weight = df[
            (~df[group_var1].isin(valid_codes1)) &
            (df[group_var2].isin(valid_codes2))
            ]['W_GEW'].sum()

        missing_g2_by_g1 = (
            df[
                (df[group_var1].isin(valid_codes1)) &
                (~df[group_var2].isin(valid_codes2))
                ]
            .groupby(group_var1)['W_GEW']
            .sum()
            .to_dict()
        )

        missing_both_weight = df[
            (~df[group_var1].isin(valid_codes1)) &
            (~df[group_var2].isin(valid_codes2))
            ]['W_GEW'].sum()

        factor_g1 = {
            g1: (
                        total_by_g1[g1]
                        + missing_g1_weight * (total_by_g1[g1] / overall_valid)
                ) / total_by_g1[g1]
            for g1 in total_by_g1
        }

        factor_g2 = {
            g1: 1 + missing_g2_by_g1.get(g1, 0) / total_by_g1[g1]
            for g1 in total_by_g1
        }

        factor_both = (
            (overall_valid + missing_both_weight) / overall_valid
            if overall_valid > 0 else 1
        )

        def compute_final_weight(row):
            g1 = row[group_var1]
            return (
                    row['original_weight']
                    * factor_g1.get(g1, 1)
                    * factor_g2.get(g1, 1)
                    * factor_both
            )

        agg_valid['final_weight'] = agg_valid.apply(compute_final_weight, axis=1)

        sum_final_by_g1 = agg_valid.groupby(group_var1)['final_weight'].transform('sum')
        agg_valid['percentage'] = (agg_valid['final_weight'] / sum_final_by_g1) * 100

        return agg_valid

    def get_modality_split(self, person_filter=None):
        """
        Returns a dict mapping mobility modes to their weighted share (%).
        Uses a one-dimensional weighted grouping on 'hvm_grouped'.
        Valid codes (after grouping) are [1, 2, 3, 5], which we map directly to:
          1 → "By foot"
          2 → "Bicycle"
          3 → "MIT" (merged driver+passenger)
          5 → "Public Transport"
        """
        filtered = self.filter_routes_by_persons(person_filter)

        valid_hvm_grouped = [1, 2, 3, 5]
        agg = MidSurveyResults.get_weighted_grouping_by_single(
            filtered, 'hvm_grouped', valid_codes=valid_hvm_grouped
        )

        label_map_en = {
            1: "By foot",
            2: "Bicycle",
            3: "MIT",
            5: "Public Transport"
        }
        agg['hvm_grouped'] = agg['hvm_grouped'].map(label_map_en)
        return dict(zip(agg['hvm_grouped'], agg['percentage']))

    def get_route_lengths_by_modalities(self):
        """
        Returns (result_dict, categories, modes), where:
          - categories = ["<0.5 km", "0.5-1 km", …, ">100 km"]
          - modes = ["By foot", "Bicycle", "MIT", "Public Transport"]
          - result_dict: { mode_label: [pct_for_cat1, …, pct_for_cat9] }
        Uses two-dimensional grouping on ('hvm_grouped', 'wegkm_gr') with valid codes:
          hvm_grouped ∈ [1, 2, 3, 5]
          wegkm_gr ∈ [1..9]
        """
        valid_hvm = [1, 2, 3, 5]
        valid_wegkm = list(range(1, 10))

        agg = MidSurveyResults.get_weighted_grouping_by_two(
            self.routes_data,
            'hvm_grouped',
            'wegkm_gr',
            valid_codes1=valid_hvm,
            valid_codes2=valid_wegkm
        )

        hvm_map_en = {
            1: "By foot",
            2: "Bicycle",
            3: "MIT",
            5: "Public Transport"
        }
        wegkm_map = {
            1: "<0.5 km",
            2: "0.5-1 km",
            3: "1-2 km",
            4: "2-5 km",
            5: "5-10 km",
            6: "10-20 km",
            7: "20-50 km",
            8: "50-100 km",
            9: ">100 km"
        }

        agg['hvm_grouped'] = agg['hvm_grouped'].map(hvm_map_en)
        agg['wegkm_gr'] = agg['wegkm_gr'].map(wegkm_map)

        categories = list(wegkm_map.values())
        modes = ["By foot", "Bicycle", "MIT", "Public Transport"]

        pivot_df = (
            agg.pivot(index='hvm_grouped', columns='wegkm_gr', values='percentage')
            .reindex(index=modes, columns=categories)
            .fillna(0.0)
        )

        result = {mode: list(pivot_df.loc[mode]) for mode in modes}
        return result, categories, modes

    def get_route_durations(self, person_filter=None):
        """
        Returns a dict mapping each duration category to its weighted percentage.
        Uses one-dimensional grouping on 'wegmin_gr' with valid codes [1..8].
        """
        filtered = self.filter_routes_by_persons(person_filter)

        valid_wegmin = list(range(1, 9))
        agg = MidSurveyResults.get_weighted_grouping_by_single(
            filtered, 'wegmin_gr', valid_codes=valid_wegmin
        )

        wegmin_map = {
            1: "<5 min",
            2: "5-10 min",
            3: "10-15 min",
            4: "15-20 min",
            5: "20-30 min",
            6: "30-45 min",
            7: "45-60 min",
            8: ">60 min"
        }
        agg['wegmin_gr'] = agg['wegmin_gr'].map(wegmin_map)
        return dict(zip(agg['wegmin_gr'], agg['percentage']))

    def get_route_lengths(self, person_filter=None):
        """
        Returns a dict mapping each length category to its weighted percentage.
        Uses one-dimensional grouping on 'wegkm_gr' with valid codes [1..9].
        """
        filtered = self.filter_routes_by_persons(person_filter)

        valid_wegkm = list(range(1, 10))
        agg = MidSurveyResults.get_weighted_grouping_by_single(
            filtered, 'wegkm_gr', valid_codes=valid_wegkm
        )

        wegkm_map = {
            1: "<0.5 km",
            2: "0.5-1 km",
            3: "1-2 km",
            4: "2-5 km",
            5: "5-10 km",
            6: "10-20 km",
            7: "20-50 km",
            8: "50-100 km",
            9: ">100 km"
        }
        agg['wegkm_gr'] = agg['wegkm_gr'].map(wegkm_map)
        return dict(zip(agg['wegkm_gr'], agg['percentage']))

    def get_route_durations_by_modalities(self):
        """
        Returns (result_dict, categories, modes), where:
          - categories = ["<5 min", "5-10 min", …, ">60 min"]
          - modes = ["By foot", "Bicycle", "MIT", "Public Transport"]
          - result_dict: { mode_label: [pct_for_cat1, …, pct_for_cat8] }
        Uses two-dimensional grouping on ('hvm_grouped', 'wegmin_gr') with valid codes:
          hvm_grouped ∈ [1, 2, 3, 5]
          wegmin_gr ∈ [1..8]
        """
        valid_hvm = [1, 2, 3, 5]
        valid_wegmin = list(range(1, 9))

        agg = MidSurveyResults.get_weighted_grouping_by_two(
            self.routes_data,
            'hvm_grouped',
            'wegmin_gr',
            valid_codes1=valid_hvm,
            valid_codes2=valid_wegmin
        )

        hvm_map_en = {
            1: "By foot",
            2: "Bicycle",
            3: "MIT",
            5: "Public Transport"
        }
        wegmin_map = {
            1: "<5 min",
            2: "5-10 min",
            3: "10-15 min",
            4: "15-20 min",
            5: "20-30 min",
            6: "30-45 min",
            7: "45-60 min",
            8: ">60 min"
        }

        agg['hvm_grouped'] = agg['hvm_grouped'].map(hvm_map_en)
        agg['wegmin_gr'] = agg['wegmin_gr'].map(wegmin_map)

        categories = list(wegmin_map.values())
        modes = ["By foot", "Bicycle", "MIT", "Public Transport"]

        pivot_df = (
            agg.pivot(index='hvm_grouped', columns='wegmin_gr', values='percentage')
            .reindex(index=modes, columns=categories)
            .fillna(0.0)
        )

        result = {mode: list(pivot_df.loc[mode]) for mode in modes}
        return result, categories, modes

    def filter_routes_by_persons(self, person_filter):
        filtered = self.persons_data
        if person_filter:
            filtered = person_filter(filtered)
        return self.routes_data[self.routes_data['HP_ID'].isin(filtered['HP_ID'])]

    @staticmethod
    def standardize_keys(modality_split):
        """
        Converts German keys to English; kept for backward compatibility
        but should no longer be needed if all methods return English already.
        """
        standard_map = {
            "zu Fuß": "By foot",
            "Fahrrad": "Bicycle",
            "MIT": "MIT",
            "ÖPV": "Public Transport",
            "keine Angabe": "No answer",
            "Weg ohne Detailerfassung": "No details"
        }

        result = {}
        for k, v in modality_split.items():
            result[standard_map.get(k, k)] = v
        return result


if __name__ == "__main__":
    path = '../../../data/census/B1_Standard-Datensatzpaket/CSV'
    mid = MidSurveyResults(path, bland=11)

    # Example: modality split (now in English)
    mod_split = mid.get_modality_split()
    print("Modality split (percent):")
    print(mod_split)
    # → {'By foot': xx.xx, 'Bicycle': xx.xx, 'MIT': xx.xx, 'Public Transport': xx.xx}

    # Example: route lengths by mode (now in English)
    route_len_result, length_cats, length_modes = mid.get_route_lengths_by_modalities()
    print("\nRoute lengths by mode (%):")
    print("Categories:", length_cats)
    print("Modes:", length_modes)
    print(route_len_result)
    # → keys will be: "By foot", "Bicycle", "MIT", "Public Transport"

    # Example: route durations (one-dimensional)
    dur_split = mid.get_route_durations()
    print("\nRoute durations (%):")
    print(dur_split)

    # Example: route durations by mode (two-dimensional, English)
    route_dur_result, dur_cats, dur_modes = mid.get_route_durations_by_modalities()
    print("\nRoute durations by mode (%):")
    print("Categories:", dur_cats)
    print("Modes:", dur_modes)
    print(route_dur_result)
