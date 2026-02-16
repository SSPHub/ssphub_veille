import src.veille_function as veille


def main(how: str):
    """
    Extract and add articles from tchap group to veille table on grist

    Args:
        how : choice between 'Test' and 'Veille' modalities
    
    """
    veille.extract_and_add_to_veille('data/export.json', target_table=how)

        

if __name__ == "__main__":
    try:
        # main("Test")
        main("Veille")
    except Exception as e:
        print(f"Fatal error in pipeline: {e}")
        raise