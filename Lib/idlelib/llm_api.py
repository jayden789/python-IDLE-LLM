import requests

class LLMApiClient:

    def __init__(self, api_url):
        self.api_url = api_url

    def send_request(self, message, request_type):
        try:
            payload = {
                "message": message,
                "notes": {
                    "type": request_type
                }
            }

            response = requests.post(
                self.api_url,
                json=payload
            )

            response.raise_for_status()
            explanation = response.json().get("reply", "No explanation returned.")
            return explanation

        except Exception as e:
            print("Error contacting LLM API:", e)
            return None
