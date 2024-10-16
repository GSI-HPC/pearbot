import requests

OLLAMA_API_BASE_URL = "http://localhost:11434/api"

def is_model_available(model_name):
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [model["name"].split(":")[0] for model in models]
            return model_name in available_models
        else:
            print(f"Error checking model availability: HTTP {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error connecting to Ollama API: {e}")
        return False

def get_available_models():
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"].split(":")[0] for model in models]
        else:
            print(f"Error fetching available models: HTTP {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error connecting to Ollama API: {e}")
        return []

def validate_models(models):
    all_models = set(models)
    unavailable_models = [model for model in all_models if not is_model_available(model)]

    if unavailable_models:
        print(f"Error: The following models are not available: {', '.join(unavailable_models)}")
        print("Available models:")
        print(", ".join(get_available_models()))
        return False
    return True
