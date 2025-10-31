from flask import Flask, render_template, request, jsonify, send_file
from openai import OpenAI
from dotenv import load_dotenv
import os
import random
from fpdf import FPDF
import io
import datetime
import langid
from gtts import gTTS
from deep_translator import GoogleTranslator  # NEW

# --- Load environment variables ---
load_dotenv()
app = Flask(__name__)

# --- AI CLIENT SETUP ---
api_key = os.getenv("FUTURIX_API_KEY")
if not api_key:
    raise ValueError("FUTURIX_API_KEY environment variable not set.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.futurixai.com/api/shivaay/v1"
)

# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    query = data.get('query', '')
    # --- Normalize mixed input (remove special characters and normalize casing) ---
    normalized_query = query.lower().strip()
    is_voice = data.get('is_voice', False)
    history = data.get('history', [
        {"role": "system", "content": "You are a helpful loan assistant."}
    ])

    history.append({"role": "user", "content": query})

    try:
        # --- Improved language detection and mixed Hindi-English handling ---
        romanized_hindi_keywords = [
        "chahiye", "ghar", "mujhe", "paise", "kitna",
        "batao", "kar", "len", "jan", "jankari", "sbik", "ki"
        ]
        
        if any(word in normalized_query for word in romanized_hindi_keywords):
            lang_code = "hi"
        else:
            lang_code, _ = langid.classify(query)
            if lang_code not in ["en", "hi"]:
                lang_code = "en"  # fallback to English for clarity
        
        lang_map = {
            "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
            "te": "Telugu", "ml": "Malayalam", "mr": "Marathi", "gu": "Gujarati",
            "pa": "Punjabi", "ur": "Urdu", "kn": "Kannada"
        }
        lang_name = lang_map.get(lang_code, "English")

        # --- Stronger multilingual system prompt ---
        system_prompt = (
            f"You are a multilingual financial assistant. "
            f"Always respond in the same language that the user used in their query. "
            f"If the user's message is in English, reply in English. "
            f"If it is in Hindi (in Devanagari or Romanized form), reply in Hindi. "
            f"If it is in another Indian language, respond in that language. "
            f"Never translate or switch to another language unless explicitly asked. "
            f"User’s detected language: {lang_name}."
        )
        history[0] = {"role": "system", "content": system_prompt}

        # --- Generate AI Response ---
        completion = client.chat.completions.create(
            model="shivaay",
            messages=history
        )
        answer = completion.choices[0].message.content.strip()

        # --- Fallback translation if model still replies in English ---
        if lang_code != "en":
            english_chars = sum(1 for ch in answer if ch.isascii())
            if english_chars / len(answer) > 0.6:
                try:
                    answer = GoogleTranslator(source='auto', target=lang_code).translate(answer)
                except Exception as trans_err:
                    print(f"Translation failed: {trans_err}")

        history.append({"role": "assistant", "content": answer})

        # --- Generate speech if voice input ---
        if is_voice:
            supported_langs = ['en', 'hi', 'bn', 'ta', 'te', 'ml', 'mr', 'gu', 'pa', 'ur', 'kn']
            tts_lang = lang_code if lang_code in supported_langs else 'en'
            tts = gTTS(answer, lang=tts_lang)
            audio_path = f"static/voice_reply_{datetime.datetime.now().timestamp()}.mp3"
            tts.save(audio_path)
            return jsonify({'response': answer, 'audio': audio_path, 'history': history})
        else:
            return jsonify({'response': answer, 'history': history})

    except Exception as e:
        print(f"Error contacting AI: {e}")
        return jsonify({'response': f"Error contacting AI: {e}"}), 500

# --- MOCK CREDIT SCORE ENDPOINT ---
@app.route('/get_mock_score', methods=['POST'])
def get_mock_score():
    mock_score = random.randint(650, 900)
    ai_response_text = f"The mock credit evaluation is complete. The score is {mock_score}. Please analyze this and inform the user of their eligibility and next steps."
    return jsonify({'response': ai_response_text})

# --- MOCK KYC ENDPOINT ---
@app.route('/verify_kyc', methods=['POST'])
def verify_kyc():
    ai_response_text = "Mock KYC check complete. PAN and Aadhaar details are verified successfully. Please inform the user and proceed to the next step (sanction letter offer)."
    return jsonify({'response': ai_response_text})

# --- PDF SANCTION LETTER ENDPOINT (FIXED DOWNLOAD VERSION) ---
@app.route('/generate_sanction_letter', methods=['POST'])
def generate_sanction_letter():
    data = request.json
    name = data.get('name', 'Valued Customer')
    amount = str(data.get('amount', 'N/A')).replace("₹", "").replace(",", "").strip()
    interest_rate = str(data.get('interest_rate', 'N/A')).replace("%", "").strip()

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "LOAN SALES ASSISTANT (LOGO)", ln=False, align='R')
        pdf.ln(20)

        pdf.set_font("Arial", size=11)
        today = datetime.date.today().strftime("%d-%m-%Y")
        pdf.cell(0, 6, f"Date: {today}", ln=True)
        pdf.ln(5)

        pdf.cell(0, 6, "To:", ln=True)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, f"{name}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 6, "123 Mock Address", ln=True)
        pdf.cell(0, 6, "City, Country 123456", ln=True)
        pdf.ln(10)

        pdf.cell(0, 6, "Dear Sir/Madam,", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(15, 6, "Subject:", ln=False)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 6, "Provisional Sanction Letter for Personal Loan", ln=True)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(15, 6, "Ref:", ln=False)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 6, f"Application No. A{random.randint(100000, 999999)}", ln=True)
        pdf.ln(10)

        pdf.multi_cell(0, 6, "This has reference to your application for a Personal Loan. We are pleased to inform you that, based on the preliminary verification, we have provisionally sanctioned the loan on the following terms and conditions:")
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, "Terms of Sanction:", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", size=11)
        def add_bullet(key, value):
            pdf.set_x(20)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(40, 6, key, ln=False)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 6, f": {value}", ln=True)

        add_bullet("Loan Amount", f"Rs. {amount}")
        add_bullet("Interest Rate", f"{interest_rate}% p.a. (Fixed)")
        add_bullet("Loan Tenure", "6 Years (72 Months)")
        add_bullet("Payment Mode", "EMI via Bank Transfer")
        add_bullet("Processing Fee", "Rs. 0 (Waived)")

        pdf.ln(10)
        pdf.cell(0, 6, "This offer is valid for a period of 15 days from the date of this letter.", ln=True)
        pdf.ln(10)
        pdf.cell(0, 6, "For Loan Sales Assistant AI", ln=True)
        pdf.ln(15)
        pdf.cell(0, 6, "(Authorized Signatory)", ln=True)
        pdf.ln(15)

        page_width = pdf.w - 2 * pdf.l_margin
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, "Shivaay AI Financial Services (Mock)", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        pdf.cell(0, 5, "Corporate ID: MOCK123456 | Address: 123 AI Lane, Tech Park", ln=True, align='C')
        pdf.cell(0, 5, "Tel: 123-456-1234 | Email: loans@shivaay-ai.mock", ln=True, align='C')

        # ✅ FIX: proper binary stream for download
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="Sanction_Letter.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500

# =========================
# MAIN
# =========================
if __name__ == '__main__':
    app.run(debug=True, port=5000)