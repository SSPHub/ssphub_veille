from ssphub_veille.veille_function import *

# To test
extract_and_add_to_veille('ssphub_veille/export.json', extract_max_date(target_table='Test'), time_format_date=False, target_table='Test')

# To add automatically
extract_and_add_to_veille('ssphub_veille/export.json', extract_max_date(), time_format_date=False, target_table='Veille')

# To set a date
# extract_and_add_to_veille('ssphub_veille/export.json', "2025-10-12", target_table='Veille')