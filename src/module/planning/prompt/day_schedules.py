def get_day_schedule_with_places_prompt(building_options, description, day):
    return (
        f'You are:\n{description}\n'
        f'Today is {day}. Write in broad strokes what you are doing during the day. Start the day at home. '
        f'Only include tasks that occur at a specific location which must be one of the provided building options and '
        f'do not include any transportation or commuting tasks (for example, do not include actions like "walking by foot" or "driving a car" or "taking the bus") or locations (for example "parking", bicycle_parking", etc.).\n'
        f'building options:\n{building_options}\n'
        f'Do not include any explanations, only provide a RFC8259 compliant JSON response following this format '
        f'without deviation.\n{{"description_of_today": '
        f'[{{"time":"HH:MM","action":"a one sentence description of what you start doing at that time", '
        f'"building_type": "building for your task which must be from above building options and can not be anything else"}},...]}}\n'
        f'The JSON Response for {day}:\n'
    )
