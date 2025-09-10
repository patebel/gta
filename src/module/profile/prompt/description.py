from model.seed import Seed


def get_description_prompt(seed: Seed):
    return (f'Sample attributes from the Berlin population:\n{seed.get_attributes_string()}\n'
            f'Imagine a realistic person with these attributes. Write a specific one paragraph description:\n'
            f'Do not include any explanations, only provide a  RFC8259 compliant JSON response  following this format '
            f'without deviation.\n'
            f'{{"persona_description":"realistic one paragraph description of someone with these attributes"}}\n'
            f'The JSON Response:\n')
