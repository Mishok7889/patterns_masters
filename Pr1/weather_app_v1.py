import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = "55555"
# you can get API keys for free here - https://api-ninjas.com/api/jokes
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


excluded_fields = ['stations', 'icon', 'source', 'datetimeEpoch']


def cleanup_api_response(data):
    if isinstance(data, dict):
        return {k: cleanup_api_response(v) for k, v in data.items() if v is not None
                and k not in excluded_fields}
    elif isinstance(data, list):
        return [cleanup_api_response(item) for item in data]
    else:
        return data


def get_weather(location, date):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}/{date}?unitGroup=metric&include=days&key={RSA_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        weather_data = cleanup_api_response(
            json.loads(response.text)['days'][0])  # Assuming the first item is the relevant weather
        # Add any additional processing if needed to match the weather data with the desired date
        return weather_data
    else:
        raise InvalidUsage("Failed to fetch weather data", status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    request_data = request.get_json()

    # Validate the required fields in the request payload
    if not all(key in request_data for key in ["requester_name", "location", "date"]):
        raise InvalidUsage("Missing required field(s)", status_code=400)

    token = request_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    location = request_data["location"]
    date = request_data["date"]

    weather_data = get_weather(location, date)

    response_data = {
        "requester_name": request_data["requester_name"],
        "timestamp": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": weather_data  # Assuming the structure matches; you might need to adjust based on the API response
    }

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
