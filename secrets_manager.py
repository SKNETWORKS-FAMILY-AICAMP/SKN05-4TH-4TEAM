import os
import json

def get_api_keys(filename='secrets.json'):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        with open(file_path, 'r') as file:
            secrets = json.load(file)
        
        openai_key = secrets.get('OpenAI_API_KEY')
        pinecone_key = secrets.get('PINECONE_API_KEY')

        if openai_key is None or pinecone_key is None:
            raise KeyError("One or both of the required API keys are missing from the secrets file.")

        return openai_key, pinecone_key

    except FileNotFoundError:
        print(f"The file {filename} was not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"The file {filename} is not a valid JSON file.")
        return None, None
    except KeyError as e:
        print(str(e))
        return None, None
