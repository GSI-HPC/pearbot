import ollama

def get_available_models():
    model_list = ollama.list()
    models = model_list.get("models", [])
    return [model["name"] for model in models]

def is_model_available(model_name):
    available_models = get_available_models()
    return model_name in available_models or f"{model_name}:latest" in available_models

def validate_models(models):
    all_models = set(models)
    unavailable_models = [model for model in all_models if not is_model_available(model)]

    if unavailable_models:
        print(f"Error: The following models are not available: {', '.join(unavailable_models)}")
        print("Available models:")
        print(", ".join(get_available_models()))
        return False
    return True
