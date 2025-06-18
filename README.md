# 🩺 AI Healthcare Assistant

This project is an **AI-powered healthcare assistant** web application built using **Flask** and **Google Gemini Pro (Flash)** model. The assistant guides users through health-related conversations and provides **non-diagnostic support**, such as:

* Asking for symptoms
* Collecting vital signs
* Asking for prescription text
* Advising users to consult professionals

> ⚠️ **Disclaimer**: This AI does **not** provide medical diagnoses or emergency advice. Always consult a medical professional.

---

## 🔍 Features

✅ Empathetic conversational AI
✅ Collects & interprets vital signs
✅ Accepts prescription texts for basic explanation
✅ Suggests seeing a doctor if needed
✅ Built-in safety and ethical prompts

---

## 📷 Screenshots

**Chat UI Example:**
![Screenshot](media/detection_sample.png)

**Live Demo (GIF or Video):**
![Demo](media/demo.gif)

Or, if using YouTube:
[Watch the demo](https://youtu.be/your_video_id)

---

## ⚙️ Tech Stack

* **Python 3.x**
* **Flask** – web framework
* **HTML/CSS/JS** – frontend (in `templates/index.html`)
* **Google Gemini Flash API** – LLM integration

---

## 🚀 How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/healthcare-ai-assistant.git
cd healthcare-ai-assistant
```

### 2. Install Dependencies

```bash
pip install flask requests
```

### 3. Add Your API Key (Optional)

Edit the `API_KEY` value in the code with your own Gemini Pro API key if needed.

### 4. Run the App

```bash
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 📁 File Structure

```
├── app.py                   # Main Flask application
├── templates/
│   └── index.html          # Frontend UI
├── static/
│   └── styles.css          # Optional custom styling
├── media/
│   ├── detection_sample.png
│   └── demo.gif
└── README.md               # Project documentation
```

---

## 📌 Key API Usage

Using Gemini Flash API endpoint:

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY
```

With JSON structured schema expected as:

```json
{
  "message": "text to display",
  "next_action": "ask_vitals | ask_prescription | suggest_doctor | continue_chat | end_session"
}
```

---

## 🤝 Contributing

Feel free to fork the project, improve it, and submit PRs!

---

## 📄 License

MIT License © 2025
