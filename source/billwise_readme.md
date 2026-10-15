# ⚡ Billwise - Utility Bill Decoder

An AI-powered assistant that reads complex electricity bills (K-Electric, LESCO, IESCO), extracts detailed billing data into structured JSON, and acts as a customer support agent to answer user questions in plain English. 

Built for the WomenTechQuest (WTQ) 2026 Build Track.

## Features

- **Level 1 (Extraction):** Batch processes folder of bill images and extracts 20+ data points (tariffs, taxes, arrears, etc.) into a strict JSON schema.
- **Level 2 (Explanation):** Answers custom user questions using precise calculations and plain-English explanations grounded purely in the bill's data.
- **Interactive Dashboard:** A beautiful, aesthetic Streamlit interface for uploading bills, viewing JSON data, and chatting with the AI assistant.

## Prerequisites

- Python 3.11 or later
- A Gemini API Key (Google AI Studio)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/utility-bill-decoder.git
   cd utility-bill-decoder
   ```

2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Rename `.env.example` to `.env` and add your Google Gemini API key:
   ```env
   MODEL_PROVIDER=google
   MODEL_NAME=gemini-3.5-flash-lite
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## Exact Commands to Run the Project

**To run the batch CSV generator (WTQ Competition Scoring):**
This script reads all bills from the `test/bills/` folder, processes them, and outputs `level1.csv` and `level2.csv` into the `output/` folder.
```bash
python source/main.py
```

**To run the interactive Billwise UI:**
```bash
streamlit run source/app.py
```

## AI Usage Section

- **Models Used:** Google `gemini-3.5-flash-lite` for both Level 1 JSON extraction and Level 2 Question Answering.
- **AI Coding Assistants:** Used Google Gemini as a pair-programming chatbot to assist with writing Python scripts, handling rate-limit errors, and designing the Streamlit CSS interface.