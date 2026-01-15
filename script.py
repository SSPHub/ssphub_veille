import veille_function as veille

# To test
# veille.extract_and_add_to_veille('export.json', veille.extract_max_date(target_table='Test'), time_format_date=False, target_table='Test')

# To add automatically
veille.extract_and_add_to_veille('export.json', veille.extract_max_date(), time_format_date=False, target_table='Veille')

# To set a date
# veille.extract_and_add_to_veille('export.json', "2025-10-12", target_table='Veille')