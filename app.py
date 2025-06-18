import os
from flask import Flask, request, jsonify, render_template, session
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

API_KEY = ""
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + API_KEY

async def llm_call(chat_history):
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
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
        import requests
        response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            parsed_json = json.loads(json_string)
            return parsed_json
        else:
            return {"message": "I'm having trouble understanding. Could you please rephrase?", "next_action": "continue_chat"}
    except requests.exceptions.RequestException:
        return {"message": "I'm sorry, I'm currently unable to process your request. Please try again later.", "next_action": "end_session"}
    except json.JSONDecodeError:
        return {"message": "I received an unreadable response. Please try again.", "next_action": "continue_chat"}

@app.route('/')
def index():
    session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"ai_message": "Please type a message.", "next_action": "continue_chat"})

    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "parts": [{"text": user_message}]})

    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need (e.g., "Blood Pressure (systolic/diastolic)", "Heart Rate (BPM)", "Oxygen Saturation (%)").
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" and "next_action".

    **Possible `next_action` values:**
    * `ask_vitals`
    * `ask_prescription`
    * `suggest_doctor`
    * `continue_chat`
    * `end_session`
    """

    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history

    ai_response_json = await llm_call(llm_input_history)

    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]})
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

@app.route('/submit_vitals', methods=['POST'])
async def submit_vitals():
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

    llm_prompt_for_vitals = f"""
    The user has provided their vital signs: Blood Pressure {bp_systolic}/{bp_diastolic} mmHg, 
    Heart Rate {heart_rate} BPM, Oxygen Saturation {oxygen_level}%.
    Based on their previously described problem and these readings, 
    provide general, non-diagnostic information. 
    """

    chat_history.append({"role": "user", "parts": [{"text": llm_prompt_for_vitals}]})

    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need.
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" and "next_action".

    **Possible `next_action` values:**
    * `ask_vitals`
    * `ask_prescription`
    * `suggest_doctor`
    * `continue_chat`
    * `end_session`
    """

    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history

    ai_response_json = await llm_call(llm_input_history)

    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]})
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

@app.route('/submit_prescription', methods=['POST'])
async def submit_prescription():
    prescription_text = request.json.get('prescription_text')
    user_prescription_message = f"User provided prescription text: {prescription_text}"

    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "parts": [{"text": user_prescription_message}]})

    llm_prompt_for_prescription = f"""
    The user has provided the following prescription text: '{prescription_text}'.
    Analyze this text to identify potential medications and their general uses. 
    Explain that this is for informational purposes only and they must consult their doctor or pharmacist.
    """

    chat_history.append({"role": "user", "parts": [{"text": llm_prompt_for_prescription}]})

    system_instruction = """
    You are a helpful and empathetic healthcare AI assistant. Your primary goal is to gather information about a user's health problem and provide general, non-diagnostic guidance.

    **CRITICAL RULES:**
    1.  **NEVER provide medical diagnoses, specific treatment plans, or emergency medical advice.**
    2.  **ALWAYS advise the user to consult a qualified medical professional for any health concerns.**
    3.  Maintain an empathetic and supportive tone.
    4.  Keep responses concise and to the point.
    5.  When asking for vital signs, be specific about what you need.
    6.  If the user mentions a prescription, ask them to type out the details.
    7.  Structure your response as a JSON object with two keys: "message" and "next_action".

    **Possible `next_action` values:**
    * `ask_vitals`
    * `ask_prescription`
    * `suggest_doctor`
    * `continue_chat`
    * `end_session`
    """

    llm_input_history = [{"role": "user", "parts": [{"text": system_instruction}]}] + chat_history

    ai_response_json = await llm_call(llm_input_history)

    chat_history.append({"role": "model", "parts": [{"text": json.dumps(ai_response_json)}]})
    session['chat_history'] = chat_history

    return jsonify({"ai_message": ai_response_json['message'], "next_action": ai_response_json['next_action']})

if __name__ == '__main__':
    app.run(debug=True)
