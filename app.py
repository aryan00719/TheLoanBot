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
from deep_translator import GoogleTranslator

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
    is_voice = data.get('is_voice', False)
    
    history = data.get('history', [
        {"role": "system", "content": "You are a helpful assistant."} # Basic fallback
    ])
    
    history.append({"role": "user", "content": query})

    try:
        completion = client.chat.completions.create(
            model="shivaay",
            messages=history,
            max_tokens=1000,
            temperature=0.8,
            top_p=0.9
        )
        answer = completion.choices[0].message.content.strip()

        history.append({"role": "assistant", "content": answer})

        if is_voice:
            try:
                lang_code, _ = langid.classify(answer)
                supported_langs = ['en', 'hi', 'bn', 'ta', 'te', 'ml', 'mr', 'gu', 'pa', 'ur', 'kn']
                if lang_code not in supported_langs:
                    lang_code = 'en'
            except Exception:
                lang_code = 'en'

            tts = gTTS(answer, lang=lang_code)
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

# --- PDF SANCTION LETTER ENDPOINT (This was already fixed) ---
@app.route('/generate_sanction_letter', methods=['POST'])
def generate_sanction_letter():
    data = request.json
    name = data.get('name', 'Valued Customer')
    # Remove any stray '₹' from the input, just in case
    amount = str(data.get('amount', 'N/A')).replace("₹", "").replace(",", "").strip()
    interest_rate = str(data.get('interest_rate', 'N/A')).replace("%", "").strip()
    loan_type = data.get('loan_type', 'Education Loan')

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=11)

        # --- HEADER ---
        today = datetime.date.today().strftime("%d/%m/%Y")
        pdf.cell(0, 10, f"Date: {today}", ln=True, align='L')
        pdf.ln(5)

        # --- RECIPIENT ---
        pdf.cell(0, 6, "To:", ln=True)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 6, f"{name}", ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 6, "Address: ___________________________", ln=True)
        pdf.cell(0, 6, "City: ___________________________", ln=True)
        pdf.ln(10)

        # --- SUBJECT & REF ---
        ref_no = f"A{random.randint(100000, 999999)}"
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 6, f"Subject: {loan_type} Sanction Letter", ln=True)
        pdf.cell(0, 6, f"Ref: Application No. {ref_no}", ln=True)
        pdf.ln(10)

        # --- BODY ---
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6,
            f"This has reference to your application for an {loan_type} for funding your "
            f"requirements. Based on the details provided in your application, "
            f"Shivaay AI Financial Services is pleased to inform you about the "
            f"provisional sanction of your loan on the following terms and conditions:"
        )
        pdf.ln(8)

        # --- TERMS LIST ---
        def bullet(text):
            pdf.cell(5)
            pdf.multi_cell(0, 6, f"• {text}")

        # --- UNICODE FIX HERE ---
        bullet(f"Loan Amount: INR {amount}")
        bullet(f"Rate of Interest: {interest_rate}% per annum (floating as per market conditions)")
        bullet("Payment Mode: EMI via registered bank account")
        bullet("Insurance to be taken by the applicant and duly assigned in favor of the lender")
        bullet("Validity: This offer stands valid for 30 days from the date of this letter")
        pdf.ln(8)

        pdf.multi_cell(0, 6,
            "Disbursement of the loan will be made only upon successful fulfillment of the conditions "
            "as mentioned below:\n"
            "1. Submission of required documents (ID, Address, Income proof)\n"
            "2. Successful KYC verification by the lender"
        )
        pdf.ln(10)

        # --- SIGN-OFF ---
        pdf.cell(0, 6, "For Shivaay AI Financial Services", ln=True)
        pdf.ln(15)
        pdf.cell(0, 6, "Authorized Signatory", ln=True)
        pdf.ln(10)

        # --- FOOTER ---
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 5, "Shivaay AI Financial Services", ln=True, align='C')
        pdf.set_font("Helvetica", size=9)
        pdf.cell(0, 5, "Corporate ID: SHV123456 | Address: 123 AI Tech Park, Jaipur, India", ln=True, align='C')
        pdf.cell(0, 5, "Tel: +91-123-456-7890 | Email: support@shivaayai.com", ln=True, align='C')

        # --- PDF BYTES STREAM ---
        pdf_bytes = pdf.output(dest='S')
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{name.replace(' ', '_')}_Sanction_Letter.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500

# --- NEW CLEAN TEXT-ONLY LOAN APPLICATION LETTER PDF ---
@app.route('/generate_custom_pdf', methods=['POST'])
def generate_custom_pdf():
    data = request.json
    name = data.get('name', 'Applicant')
    address = data.get('address', 'Address not provided')
    city = data.get('city', 'City not provided')
    loan_type = data.get('loan_type', 'Loan')
    loan_amount = data.get('loan_amount', 'N/A')
    loan_purpose = data.get('loan_purpose', 'N/A')
    income = data.get('income', 'N/A')
    tenure = data.get('tenure', 'N/A')
    bank_name = data.get('bank_name', 'Bank')

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=12)

        # Header
        today = datetime.date.today().strftime("%d/%m/%Y")
        pdf.cell(0, 10, f"Date: {today}", ln=True, align='R')
        pdf.cell(0, 10, bank_name, ln=True, align='C')
        pdf.ln(10)

        # Applicant Details
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, f"Applicant Details:", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, f"Name: {name}", ln=True)
        pdf.cell(0, 8, f"Address: {address}", ln=True)
        pdf.cell(0, 8, f"City: {city}", ln=True)
        pdf.ln(10)

        # Subject
        pdf.set_font("Helvetica", 'B', 12)
        # --- UNICODE FIX HERE ---
        pdf.cell(0, 10, f"Subject: Application for {loan_type} of INR {loan_amount}", ln=True)
        pdf.ln(10)

        # Body Paragraphs
        pdf.set_font("Helvetica", size=12)
        # --- UNICODE FIX HERE (x2) ---
        pdf.multi_cell(0, 8, f"Dear Sir/Madam,\n\nI am writing this letter to apply for a {loan_type} amounting to INR {loan_amount}. The purpose of this loan is {loan_purpose}. I am currently employed and my monthly income is INR {income}. I intend to repay the loan over a tenure of {tenure} months.\n\nI assure you of my ability to meet the repayment obligations on time and request you to kindly consider my application favorably.\n\nThank you for your time and consideration.\n")
        pdf.ln(10)

        # Closing
        pdf.cell(0, 8, "Yours sincerely,", ln=True)
        pdf.ln(20)
        pdf.cell(0, 8, f"{name}", ln=True)

        # Output PDF to bytes with proper encoding
        pdf_output = pdf.output(dest='S').encode('latin1')
        buffer = io.BytesIO(pdf_output)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="Loan_Application_Letter.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print(f"Error generating custom PDF: {e}")
        return jsonify({"error": str(e)}), 500

# =========================
# MAIN
# =========================
if __name__ == '__main__':
    app.run(debug=True, port=5000)