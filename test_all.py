from ssphub_veille.veille_function import *

def test_():
    extract_and_add_to_veille('ssphub_veille/export.json', '2021-01-01', time_format_date=True, target_table='Test')

