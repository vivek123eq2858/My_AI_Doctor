import os
from flask import Flask, request, jsonify, render_template, session
import json # Import json for parsing __firebase_config if needed

# --- Firebase Configuration (Placeholder - not used for this example's core functionality) ---
# In a real application, you'd initialize Firebase here for database storage.
# For this example, we're focusing on the Flask app and LLM interaction.
# const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
# const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');
# const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : '';
# -----------------------------------------------------------------------------------------

app = Flask(__name__)
# Set a secret key for session management. In production, use a strong, randomly generated key.
app.secret_key = os.urandom(24) 

# --- LLM API Configuration ---
# Leave apiKey as an empty string. Canvas will automatically provide it at runtime.
API_KEY = "AIzaSyCaMV-Z1gvDHLQbOJtb2V77JroghTDVh4U" 
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + API_KEY

async def llm_call(chat_history):
    """
    Makes an asynchronous call to the Gemini API to get a response.
    """
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json", # Requesting JSON response
            "responseSchema": { # Define schema for structured output
                "type": "OBJECT",
                "properties": {
                    "message": {"type": "STRING"},
                    "next_action": {
                        "type": "STRING",
                        "enum": ["ask_vitals", "ask_prescription", "suggest_doctor", "continue_chat", "end_session"]
                    }
                },
                "required": ["message", "next_action"]
            }
        }
    }

    try:
        # Use a synchronous requests call for simplicity in Flask backend.
        # In a highly concurrent app, you might use aiohttp with async Flask.
        import requests
        response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            # The LLM is designed to return a JSON string within the 'text' part
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            # Parse the JSON string into a Python dictionary
            parsed_json = json.loads(json_string)
            return parsed_json
        else:
            print(f"LLM response structure unexpected: {result}")
            return {"message": "I'm having trouble understanding. Could you please rephrase?", "next_action": "continue_chat"}
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        return {"message": "I'm sorry, I'm currently unable to process your request. Please try again later.", "next_action": "end_session"}
    except json.JSONDecodeError as e:
        print(f"Error decoding LLM response JSON: {e} - Raw response: {response.text}")
        return {"message": "I received an unreadable response. Please try again.", "next_action": "continue_chat"}


@app.route('/')
def index():
    """Renders the main chat interface."""
    # Initialize chat history for a new session
    session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    """Handles user messages and interacts with the LLM."""
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"ai_message": "Please type a message.", "next_action": "continue_chat"})

    # Get chat history from session or initialize
    chat_history = session.get('chat_history', [])

    # Add user message to history
    chat_history.append({"role": "user", "parts": [{"text": user_message}]})

    # Define the system instruction for the LLM
    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need (e.g., "Blood Pressure (systolic/diastolic)", "Heart Rate (BPM)", "Oxygen Saturation (%)").
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" (the AI's text response) and "next_action" (a string indicating the next required user input or system action).

    **Possible `next_action` values:**
    * `ask_vitals`: The AI needs vital signs (BP, HR, O2).
    * `ask_prescription`: The AI needs prescription text.
    * `suggest_doctor`: The AI has enough information to strongly suggest seeing a doctor.
    * `continue_chat`: The AI needs more general information or is providing general info.
    * `end_session`: The conversation is winding down or an error occurred.

    **Conversation Flow Examples:**
    - User: "I have a headache."
    - AI: `{"message": "I'm sorry to hear that. Can you tell me more about your headache? How severe is it on a scale of 1-10, and how long have you had it?", "next_action": "continue_chat"}`
    - User: "It's a 7, and for 3 days."
    - AI: `{"message": "Thank you for that information. Have you experienced any other symptoms like fever, nausea, or changes in vision?", "next_action": "continue_chat"}`
    - User: "No, just the headache. My BP is 130/80."
    - AI: `{"message": "Thank you for sharing your blood pressure. To get a fuller picture, could you also provide your heart rate (BPM) and oxygen saturation (%)?", "next_action": "ask_vitals"}`
    - User: "I have a prescription I want to understand."
    - AI: `{"message": "I can help provide general information about medications, but remember I am not a pharmacist or doctor. Please type out the details of your prescription.", "next_action": "ask_prescription"}`
    - AI (after gathering enough info for a concerning situation): `{"message": "Based on the information you've provided, it's important to consult a doctor or healthcare professional as soon as possible for a proper diagnosis and personalized advice. I am an AI and cannot provide medical diagnoses or treatment.", "next_action": "suggest_doctor"}`
    """
    
    # Prepend the system instruction to the chat history for each LLM call
    # This ensures the LLM always has its core directives.
    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history
    
    ai_response_json = await llm_call(llm_input_history)

    # Add AI response to history for future turns
    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]}) # Store as JSON string
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

@app.route('/submit_vitals', methods=['POST'])
async def submit_vitals():
    """Handles vital signs submission."""
    bp_systolic = request.json.get('bp_systolic')
    bp_diastolic = request.json.get('bp_diastolic')
    heart_rate = request.json.get('heart_rate')
    oxygen_level = request.json.get('oxygen_level')

    user_vital_message = (
        f"User provided vital signs: Blood Pressure {bp_systolic}/{bp_diastolic} mmHg, "
        f"Heart Rate {heart_rate} BPM, Oxygen Saturation {oxygen_level}%."
    )

    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "parts": [{"text": user_vital_message}]})

    # Prompt the LLM to interpret vitals and suggest next steps
    llm_prompt_for_vitals = f"""
    The user has provided their vital signs: Blood Pressure {bp_systolic}/{bp_diastolic} mmHg, 
    Heart Rate {heart_rate} BPM, Oxygen Saturation {oxygen_level}%.
    Based on their previously described problem (if any, from chat history) and these readings, 
    provide general, non-diagnostic information about what these readings might indicate. 
    **Strongly advise them to consult a medical professional immediately if readings are concerning.**
    Remember, you are an AI and cannot provide medical diagnoses or treatment.
    """
    chat_history.append({"role": "user", "parts": [{"text": llm_prompt_for_vitals}]})
    
    # Prepend the system instruction again for this specific call
    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need (e.g., "Blood Pressure (systolic/diastolic)", "Heart Rate (BPM)", "Oxygen Saturation (%)").
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" (the AI's text response) and "next_action" (a string indicating the next required user input or system action).

    **Possible `next_action` values:**
    * `ask_vitals`: The AI needs vital signs (BP, HR, O2).
    * `ask_prescription`: The AI needs prescription text.
    * `suggest_doctor`: The AI has enough information to strongly suggest seeing a doctor.
    * `continue_chat`: The AI needs more general information or is providing general info.
    * `end_session`: The conversation is winding down or an error occurred.
    """
    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history

    ai_response_json = await llm_call(llm_input_history)

    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]})
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

@app.route('/submit_prescription', methods=['POST'])
async def submit_prescription():
    """Handles prescription text submission."""
    prescription_text = request.json.get('prescription_text')

    user_prescription_message = f"User provided prescription text: {prescription_text}"

    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "parts": [{"text": user_prescription_message}]})

    # Prompt the LLM to analyze prescription text
    llm_prompt_for_prescription = f"""
    The user has provided the following prescription text: '{prescription_text}'.
    Analyze this text to identify potential medications and their general uses, but **do not provide specific dosage instructions or medical advice.**
    Explain that this is for informational purposes only and they must consult their doctor or pharmacist for accurate information and guidance.
    Remember, you are an AI and cannot provide medical diagnoses or treatment.
    """
    chat_history.append({"role": "user", "parts": [{"text": llm_prompt_for_prescription}]})

    # Prepend the system instruction again for this specific call
    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need (e.g., "Blood Pressure (systolic/diastolic)", "Heart Rate (BPM)", "Oxygen Saturation (%)").
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" (the AI's text response) and "next_action" (a string indicating the next required user input or system action).

    **Possible `next_action` values:**
    * `ask_vitals`: The AI needs vital signs (BP, HR, O2).
    * `ask_prescription`: The AI needs prescription text.
    * `suggest_doctor`: The AI has enough information to strongly suggest seeing a doctor.
    * `continue_chat`: The AI needs more general information or is providing general info.
    * `end_session`: The conversation is winding down or an error occurred.
    """
    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history

    ai_response_json = await llm_call(llm_input_history)

    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]})
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

if __name__ == '__main__':
    app.run(debug=True)
