import requests
import json

import ollama

def post_request_generate(model, prompt):
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "stream": True}

    model_details = get_model_details(model)
    model_format = model_details.get("details", {}).get("format", "N/A")
    model_family = model_details.get("details", {}).get("family", "N/A")
    model_parameter_size = model_details.get("details", {}).get("parameter_size", "N/A")
    model_quantization_level = model_details.get("details", {}).get("quantization_level", "N/A")

    response_content = ""
    with requests.post(url, headers=headers, json=data, stream=True) as r:
        for line in r.iter_lines():
            if line:
                json_response = json.loads(line)
                if not json_response.get("done", False):
                    content = json_response.get("response", "")
                    print(content, end='', flush=True)
                    response_content += content
                else:
                    # This is the final response with metrics
                    print("\n\n---------------------")
                    print(f"Model: {model} (Family: {model_family}), Format: {model_format}, Parameter Size: {model_parameter_size}, Quantization Level: {model_quantization_level}")
                    eval_count = json_response.get("eval_count", 0)
                    prompt_eval_count = json_response.get('prompt_eval_count', 0)
                    eval_duration = json_response.get("eval_duration", 1)  # in nanoseconds
                    tokens_per_second = (eval_count / eval_duration) * 1e9
                    print(f"Tokens generated: {eval_count}")
                    print(f"Generation time: {eval_duration / 1e9:.2f} seconds")
                    print(f"Speed: {tokens_per_second:.2f} tokens/second")
                    print(f"Prompt tokens: {prompt_eval_count}")
                    print(f"Total tokens: {prompt_eval_count + eval_count}")
                    print(f"Total duration: {json_response.get('total_duration', 0) / 1e9:.2f} seconds")
                    print("---------------------")
    print()
    return response_content


def get_model_details(model):
    try:
        return ollama.show(model)
    except Exception as e:
        return f"Error retrieving model details: {str(e)}"
