import sys
import os
import json
import urllib.request
import urllib.parse

NEWS_API_KEY = "YOUR_NEWS_API_KEY"

def get_current_weather(city: str, unit: str = "celsius") -> str:
    """Gets the current temperature for a given city using open-meteo API."""
    try:
        # Geocode the city to get latitude and longitude
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        geo_req = urllib.request.Request(geo_url, headers={'User-Agent': 'Gemma4ToolCalling/1.0'})
        with urllib.request.urlopen(geo_req) as response:
            geo_data = json.loads(response.read().decode('utf-8'))

        if "results" not in geo_data or not geo_data["results"]:
            return f"Could not find coordinates for city: {city}."

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        country = location.get("country", "")

        # Fetch the weather
        temp_unit = "fahrenheit" if unit.lower() == "fahrenheit" else "celsius"
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&temperature_unit={temp_unit}"
        weather_req = urllib.request.Request(weather_url, headers={'User-Agent': 'Gemma4ToolCalling/1.0'})
        with urllib.request.urlopen(weather_req) as response:
            weather_data = json.loads(response.read().decode('utf-8'))

        if "current" in weather_data:
            current = weather_data["current"]
            temp = current["temperature_2m"]
            wind = current["wind_speed_10m"]
            temp_unit_str = weather_data["current_units"]["temperature_2m"]
            wind_unit_str = weather_data["current_units"]["wind_speed_10m"]

            return f"The current weather in {city.title()} ({country}) is {temp}{temp_unit_str} with wind speeds of {wind}{wind_unit_str}."
        else:
            return f"Weather data for {city} is unavailable from the API."

    except Exception as e:
        return f"Error fetching weather for {city}: {e}"

def get_current_news(topic: str = None) -> str:
    """Fetches the latest news headlines using NewsAPI, optionally filtered by a topic."""
    api_key = NEWS_API_KEY
    if api_key == "YOUR_API_KEY":
        return "Error: Please replace 'YOUR_API_KEY' with your actual NewsAPI key in the script."

    try:
        if topic and topic.strip():
            url = f"https://newsapi.org/v2/everything?q={urllib.parse.quote(topic)}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=5&apiKey={api_key}"

        req = urllib.request.Request(url, headers={'User-Agent': 'Gemma4ToolCalling/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get("status") != "ok":
            return f"Error fetching news: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])
        if not articles:
            return f"No news articles found{' for ' + topic if topic else ''}."

        results = [f"News{' on ' + topic if topic else ' Headlines'}:"]
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No Title")
            source = article.get("source", {}).get("name", "Unknown Source")
            results.append(f"{i}. {title} ({source})")

        return "\n".join(results)

    except Exception as e:
        return f"Error fetching news: {e}"

def get_current_time(timezone: str) -> str:
    """Gets the current time for a specific timezone (e.g., 'Europe/London' or 'America/New_York')."""
    try:
        # Utilizing TimeAPI.io as a more stable alternative
        url = f"https://timeapi.io/api/Time/current/zone?timeZone={urllib.parse.quote(timezone)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Gemma4ToolCalling/1.0', 'Accept': 'application/json'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        time_str = data.get("time")
        date_str = data.get("date")

        if time_str and date_str:
            return f"The current time in {timezone} is {time_str} on {date_str}."
        return f"Could not fetch time for {timezone}."

    except Exception as e:
        return f"Error fetching time for {timezone}. Make sure to use a valid timezone like 'America/New_York'. API Error: {e}"

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Converts a specific amount from one currency to another."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Gemma4ToolCalling/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        rates = data.get("rates", {})
        if to_currency not in rates:
            return f"Error: Currency code '{to_currency}' is not supported or invalid."

        rate = rates[to_currency]
        converted = float(amount) * rate
        return f"{amount} {from_currency} is equal to {converted:.2f} {to_currency} (Rate: {rate})."

    except Exception as e:
        return f"Error converting currency: {e}"

# A dictionary to easily access the functions by name
TOOL_FUNCTIONS = {
    "convert_currency": convert_currency,
    "get_current_news": get_current_news,
    "get_current_time": get_current_time,
    "get_current_weather": get_current_weather
}

# The tools defined in the Ollama JSON schema format
available_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Gets the current temperature for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. Tokyo"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_news",
            "description": "Fetches the latest news headlines. Optionally provide a topic to search for specific news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for in the news, e.g., 'Artificial Intelligence' or 'Tesla'."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Gets the current time for a specific timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The timezone to get the time for, e.g., 'Europe/London' or 'America/New_York'."
                    }
                },
                "required": ["timezone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Converts a specific amount from one currency to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount to convert."
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "The 3-letter currency code to convert from, e.g., 'USD' or 'EUR'."
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "The 3-letter currency code to convert to, e.g., 'JPY' or 'GBP'."
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    }
]

def call_ollama(payload):
    """Helper function to call the local Ollama API."""
    url = "http://localhost:11434/api/chat"
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    # Allow user prompt to be sent via command line as an arg
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        print("Please try again and provide a prompt to use.\n")
        sys.exit(1)

    print("\n[SYSTEM]")

    for tool in TOOL_FUNCTIONS.keys():
        print(f"  ○ {('Tool: ' + tool).ljust(45, '.')} [LOADED]")
    print()

    print(f'[PROMPT]\n{user_query}\n')

    # Initial payload to the model
    messages = [{"role": "user", "content": user_query}]
    payload = {
        "model": "gemma4:e2b",  # The model you specified
        "messages": messages,
        "tools": available_tools,
        "stream": False
    }

    print("[EXECUTION]")
    print("  ● Querying model...\n")

    try:
        response_data = call_ollama(payload)
    except Exception as e:
        print(f"    └─ [ERROR] Error calling Ollama API: {e}")
        print("    └─ Make sure Ollama is running and the gemma4:e2b model is pulled.")
        return

    message = response_data.get("message", {})

    # Check if the model decided to call tools
    if "tool_calls" in message and message["tool_calls"]:
        print("[TOOL EXECUTION]")

        # Add the model's tool calls to the chat history
        messages.append(message)

        # Execute each tool call
        num_tools = len(message["tool_calls"])
        for i, tool_call in enumerate(message["tool_calls"]):
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]

            # Formatting variables for the ASCII tree
            is_first = (i == 0)
            is_last = (i == num_tools - 1)

            if num_tools == 1:
                branch_char = "└──"
                child_pipe = "    "
            elif is_first:
                branch_char = "┌──"
                child_pipe = "│   "
            elif is_last:
                branch_char = "└──"
                child_pipe = "    "
            else:
                branch_char = "├──"
                child_pipe = "│   "

            # Format arguments safely for display
            args_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in arguments.items())

            print(f"  {branch_char} Calling: {function_name}")
            print(f"  {child_pipe}├─ Args: {args_str}")

            if function_name in TOOL_FUNCTIONS:
                func = TOOL_FUNCTIONS[function_name]
                try:
                    # Call the actual Python function with the provided arguments
                    result = func(**arguments)

                    # Clean up multi-line returns (like news) so they indent nicely within the tree
                    formatted_result = str(result).replace('\n', f'\n  {child_pipe}   ')
                    print(f"  {child_pipe}└─ Result: {formatted_result}")

                    # Add the tool response to messages history
                    messages.append({
                        "role": "tool",
                        "content": str(result),
                        "name": function_name
                    })
                except TypeError as e:
                    print(f"  {child_pipe}└─ [ERROR] calling function: {e}")
            else:
                print(f"  {child_pipe}└─ [ERROR] Unknown function: {function_name}")

            if not is_last:
                print("  │")

        # Send the tool results back to the model to get the final answer
        print("\n[EXECUTION]")
        print("  ● Synthesizing results...\n")
        payload["messages"] = messages

        try:
            final_response_data = call_ollama(payload)
            print("[RESPONSE]")
            print(final_response_data.get("message", {}).get("content", "")+"\n")
        except Exception as e:
            print(f"    └─ [ERROR] Error calling Ollama API for final response: {e}")

    else:
        # The model answered directly without using any tools
        print("[RESPONSE]")
        print(message.get("content", "")+"\n")

if __name__ == "__main__":
    main()
