# TheLoanBot

Meet TheLoanBot, your personal automated assistant dedicated to making the loan process easier. Whether you're exploring mortgage options, a personal loan, or a car loan, TheLoanBot is here 24/7 to answer your questions, check eligibility, and guide you through every step with instant, clear, and reliable information.

## 🚀 Features

- **AI-Powered Loan Assistant**: Get instant answers about different loan types, eligibility criteria, and application processes
- **Interactive Chat Interface**: User-friendly chat interface with voice support
- **Sanction Letter Generation**: Automatically generate professional sanction letters in PDF format
- **Multi-language Support**: Supports Hindi and English conversations
- **Credit Score Simulation**: Mock credit evaluation for demonstration purposes
- **KYC Verification**: Simulated KYC process for complete loan workflow

## 🎯 Demo Credentials

To explore TheLoanBot's features, use these demo credentials:

### Login Credentials
- **Username**: `demo`
- **Password**: `demo123`

### API Configuration
The app uses Futurix AI API. You'll need to set the `FUTURIX_API_KEY` environment variable.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- pip
- Virtual environment (recommended)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/aryan00719/TheLoanBot.git
   cd TheLoanBot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   # Create .env file
   echo "FUTURIX_API_KEY=your_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5050
   ```

## 🌐 Deployment

The app is configured for easy deployment on cloud platforms:

### Render (Recommended)
1. Connect your GitHub repository to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Add environment variable: `FUTURIX_API_KEY`

### Heroku
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set config: `heroku config:set FUTURIX_API_KEY=your_key`
5. Deploy: `git push heroku main`

## 📱 Usage

1. **Login** with demo credentials (username: `demo`, password: `demo123`)
2. **Start chatting** with TheLoanBot about loans
3. **Request sanction letters** by providing required details
4. **Download PDFs** of generated sanction letters
5. **Use voice features** for hands-free interaction

## 🏗️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI**: OpenAI API (Futurix)
- **PDF Generation**: FPDF
- **Voice**: gTTS, Speech Recognition
- **Translation**: Deep Translator

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 📞 Support

For questions or support, please open an issue on GitHub.
