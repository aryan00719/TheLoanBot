// --- GLOBAL VARIABLES ---
let isTtsEnabled = true; // Text-to-Speech toggle
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

let chatHistory = [
    {
        "role": "system",
        "content": "You are a helpful loan assistant for TheLoanBot. When a user requests a sanction letter, ask for the required details: name, address, city, loan amount, interest rate, and loan type. Collect all the information from the conversation. Once you have all the details, respond with 'GENERATE_PDF:' followed by a JSON object containing the collected data, like {'name': 'John Doe', 'address': '123 Main St', 'city': 'Anytown', 'amount': '50000', 'interest_rate': '10', 'loan_type': 'Personal Loan'}. Do not generate the PDF yourself; just provide the JSON."
    }
];


// Check if browser supports Speech Recognition
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true; // Keep listening but stop after timeout
    recognition.lang = 'en-IN'; // Indian English default
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    // --- Recognition Event Handlers ---
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) { // Check if micBtn exists
        recognition.onstart = () => {
            micBtn.classList.add('is-listening');
        };

        recognition.onspeechend = () => {
            recognition.stop();
            micBtn.classList.remove('is-listening');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            // Detect Hindi voice phrases (romanized or native)
            if (/[\u0900-\u097F]/.test(transcript) || /(chahiye|loan|ghar|mujhe|kar|len|jankari|bataye|batao)/i.test(transcript)) {
                recognition.lang = 'hi-IN';
            } else {
                recognition.lang = 'en-IN';
            }
            document.getElementById('query').value = transcript;
            // Automatically send the query after speech
            if (window.sendQuery) window.sendQuery();
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            micBtn.classList.remove('is-listening');
        };
    }
}


// --- MAIN CHAT FUNCTION ---
window.sendQuery = async function () {
    const input = document.getElementById("query");
    const userText = input.value.trim();
    if (!userText) return;

    addMessage(userText, "user");
    input.value = "";
    showTypingIndicator(true);

    try {
        // Send the full history and the new query
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: userText,
                history: chatHistory,
                is_voice: recognition && document.getElementById('mic-btn') && document.getElementById('mic-btn').classList.contains('is-listening')
            })
        });

        const data = await res.json();

        // Update the global chat history
        chatHistory = data.history;

        // --- Check for GENERATE_PDF anywhere in the response ---
        const pdfMatch = data.response.match(/GENERATE_PDF:\s*(\{[\s\S]*?\})/);
        if (pdfMatch && pdfMatch[1]) {
            const jsonStr = pdfMatch[1].trim();
            try {
                const pdfData = JSON.parse(jsonStr);
                // Show the chat message without the JSON part
                const cleanText = data.response.replace(pdfMatch[0], "").trim();
                addMessage(cleanText, "assistant");
                addMessage("Generating your sanction letter...", "assistant");
                generateAndDownloadPDF(pdfData);
            } catch (e) {
                console.error("Error parsing PDF data:", e);
                addMessage(data.response, "assistant");
                addMessage("Sorry, there was an error generating the PDF.", "assistant");
            }
        } else {
            // Normal AI response
            addMessage(data.response, "assistant");
            // --- Play voice reply if available ---
            if (data.audio) {
                const audio = new Audio(data.audio);
                audio.play();
            }
        }

    } catch (error) {
        console.error("Error fetching /ask:", error);
        showTypingIndicator(false);
        addMessage("Sorry, I'm having trouble connecting to the server.", "assistant");
    }
}

// --- Triggers the mock score check ---
async function triggerMockScore() {
    showTypingIndicator(true); // Show typing while we get the score
    try {
        const res = await fetch("/get_mock_score", { method: "POST" });
        const data = await res.json();

        // Send the score *back to the AI* for analysis
        await sendQueryForAnalysis(data.response);

    } catch (error) {
        console.error("Error fetching /get_mock_score:", error);
        showTypingIndicator(false);
        addMessage("Sorry, I couldn't run the credit check.", "assistant");
    }
}

// --- NEW: Triggers the mock KYC check ---
async function triggerKycCheck() {
    showTypingIndicator(true); // Show typing while we verify KYC
    try {
        const res = await fetch("/verify_kyc", { method: "POST" });
        const data = await res.json();

        // Send the KYC status *back to the AI* for analysis
        await sendQueryForAnalysis(data.response);

    } catch (error) {
        console.error("Error fetching /verify_kyc:", error);
        showTypingIndicator(false);
        addMessage("Sorry, I couldn't run the KYC check.", "assistant");
    }
}


// --- Sends data (like score or KYC status) back to AI for analysis ---
async function sendQueryForAnalysis(analysisText) {
    try {
        // This is a special "tool" message for the AI
        // We add it to the history as a "user" message so the AI can "see" it
        chatHistory.push({ "role": "user", "content": analysisText });

        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // Send the *updated* history
            body: JSON.stringify({
                query: analysisText, // We send the text as the "query"
                history: chatHistory // The history includes the new query
            })
        });

        const data = await res.json();

        // Update the global chat history
        chatHistory = data.history;

        showTypingIndicator(false);

        // Check for sanction offer *immediately* after analysis
        // This logic is now generic and works after credit OR KYC
        if (data.response.includes("[ACTION:OFFER_SANCTION")) {
            const commandMatch = data.response.match(/\[ACTION:OFFER_SANCTION\|(.*?)]/);
            if (commandMatch && commandMatch[1]) {
                const loanDetails = JSON.parse(commandMatch[1]);
                const cleanText = data.response.replace(commandMatch[0], "").trim();
                addMessage(cleanText, "assistant");
                addDownloadButton(loanDetails);
            } else {
                addMessage(data.response.replace(/\[ACTION:.*?\]/g, ""), "assistant");
            }
        } else {
            addMessage(data.response, "assistant"); // Add AI's analysis
        }

    } catch (error) {
        console.error("Error sending analysis:", error);
        showTypingIndicator(false);
    }
}

// --- Adds a "Download PDF" button to the chat ---
function addDownloadButton(loanDetails) {
    const chatBox = document.getElementById("chat-box");
    const btn = document.createElement('button');
    btn.className = 'chat-action-btn'; // This class is styled by the new CSS
    btn.textContent = 'Download Sanction Letter';

    // Store data in the button itself
    btn.dataset.name = loanDetails.name;
    btn.dataset.amount = loanDetails.amount;
    btn.dataset.rate = loanDetails.interest_rate;

    btn.onclick = async (e) => {
        const { name, amount, rate } = e.target.dataset;
        e.target.textContent = "Generating...";
        e.target.disabled = true;

        try {
            const res = await fetch("/generate_custom_pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: name,
                    amount: amount,
                    interest_rate: rate
                })
            });

            // Check content type before proceeding
            const contentType = res.headers.get("Content-Type") || "";
            if (!res.ok || !contentType.includes("application/pdf")) {
                let errorText = "";
                try {
                    errorText = await res.text();
                } catch (e) {
                    errorText = "(Could not retrieve error details)";
                }
                console.error("PDF Download Error:", errorText || res.statusText);
                e.target.textContent = "Failed to generate";
                e.target.style.background = "#ef4444";
                return;
            }

            // Trigger browser download
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'Loan_Application_Letter.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            e.target.textContent = "Downloaded!";

        } catch (error) {
            console.error("PDF Download Error:", error);
            e.target.textContent = "Failed to generate";
            e.target.style.background = "#ef4444"; // Use the new CSS variable for danger
        }
    };

    // Append button inside a new bubble
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", "assistant");
    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    bubble.appendChild(btn);
    msgDiv.appendChild(bubble);
    chatBox.appendChild(msgDiv);
    // Call this to update input area position
    if (window.updateInputAreaPosition) {
        window.updateInputAreaPosition();
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}


// --- Show/Hide Typing Indicator ---
function showTypingIndicator(show) {
    const chatBox = document.getElementById("chat-box");
    let indicator = document.getElementById("typing-indicator");

    if (show) {
        if (!indicator) {
            indicator = document.createElement("div");
            indicator.id = "typing-indicator";
            indicator.className = "message assistant"; // Show on left

            // --- THIS IS THE FIX ---
            // This HTML now matches the new style.css
            // It uses the standard 'bubble' class and the new 'typing-indicator' class
            indicator.innerHTML = `
                <div class="bubble">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>`;
            // --- END OF FIX ---

            chatBox.appendChild(indicator);
        }
    } else {
        if (indicator) {
            indicator.remove();
        }
    }
    // Call this to update input area position
    if (window.updateInputAreaPosition) {
        window.updateInputAreaPosition();
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}


// --- Main function to add messages to UI ---
function addMessage(text, sender) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    let formattedText;
    if (sender === "assistant") {

        // --- NEW: Check if this is the special "tool" analysis text ---
        if (text.startsWith("The mock credit evaluation is complete.") || text.startsWith("Mock KYC check complete.")) {
            // This is a "tool" message, not for the user.
            // Do not add it to the chat box.
            return;
        }

        formattedText = formatAssistantMessage(text);
        bubble.innerHTML = formattedText;

        // --- NEW: Speak the response ---
        if (isTtsEnabled) {
            // Speak the clean text, without HTML tags
            speakText(formattedText.replace(/<[^>]*>?/gm, ''));
        }
    } else {
        bubble.textContent = text;
    }

    msgDiv.appendChild(bubble);
    chatBox.appendChild(msgDiv);

    // Call this to update input area position
    if (window.updateInputAreaPosition) {
        window.updateInputAreaPosition();
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- NEW: Text-to-Speech Function ---
function speakText(text) {
    // Stop any previous speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US'; // You can change this
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
}

// --- Formats the AI's markdown text ---
function formatAssistantMessage(text) {
    let formattedText = text;
    // 1. Remove emojis (already done, but good to keep)
    formattedText = formattedText.replace(/🎉|🏠|👉|💡|✅/g, '');
    // 2. Remove dividers
    formattedText = formattedText.replace(/---/g, '');
    // 3. Headings
    formattedText = formattedText.replace(/^#\s(.*?)$/gm, '<br><b>$1</b>');
    // 4. Blockquotes
    formattedText = formattedText.replace(/^> (.*?)$/gm, '<br><i>$1</i>');
    // 5. Lists
    formatted = formattedText.replace(/^- (.*?)$/gm, '<br>• $1');
    // 6. Bold/Italics
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    formattedText = formattedText.replace(/\*(.*?)\*/g, '<i>$1</i>');
    // 7. Paragraphs
    formattedText = formattedText.replace(/\n\n/g, '<br><br>'); // Double newline for paragraph
    formattedText = formattedText.replace(/\n/g, '<br>'); // Single newline for line break
    // 8. Cleanup
    formattedText = formattedText.replace(/^(<br>\s*)+/g, '');
    formattedText = formattedText.trim();
    return formattedText;
}

// --- Generates and downloads the sanction letter PDF ---
async function generateAndDownloadPDF(pdfData) {
    try {
        const res = await fetch("/generate_sanction_letter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pdfData)
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'Sanction_Letter.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error("Error generating PDF:", error);
        addMessage("Sorry, there was an error generating the sanction letter.", "assistant");
    }
}

// --- Select prompt from quick options ---
window.selectPrompt = function (promptKey) {
    const promptTexts = {
        "prompt1": "What types of loans do you offer?",
        "prompt2": "Am I eligible for a personal loan?",
        "prompt3": "What is the interest rate?"
    };
    const text = promptTexts[promptKey] || promptKey;
    const input = document.getElementById("query");
    input.value = text;
    window.sendQuery();
}

// --- NEW: Event Listeners for Voice Buttons ---
document.addEventListener('DOMContentLoaded', () => {
    // Send button
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendQuery);
    }

    // Speaker/Mute Button
    const speakerBtn = document.getElementById('speaker-btn');
    const speakerIcon = document.getElementById('speaker-icon');
    const muteIcon = document.getElementById('mute-icon');

    if (speakerBtn) { // Check if speakerBtn exists
        speakerBtn.addEventListener('click', () => {
            isTtsEnabled = !isTtsEnabled;
            if (isTtsEnabled) {
                speakerIcon.style.display = 'inline';
                muteIcon.style.display = 'none';
            } else {
                speakerIcon.style.display = 'none';
                muteIcon.style.display = 'inline';
                window.speechSynthesis.cancel(); // Stop any active speech
            }
        });
    }

    // Mic Button
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) { // Check if micBtn exists
        if (recognition) {
            micBtn.addEventListener('click', () => {
                if (micBtn.classList.contains('is-listening')) {
                    recognition.stop();
                } else {
                    try {
                        recognition.start();
                        // Stop listening automatically after 6 seconds
                        setTimeout(() => {
                            if (micBtn.classList.contains('is-listening')) {
                                recognition.stop();
                                micBtn.classList.remove('is-listening');
                            }
                        }, 6000);
                    } catch (e) {
                        console.error("Error starting recognition: ", e);
                        alert("Speech recognition could not be started. It might be in use or permissions are denied.");
                    }
                }
            });
        } else {
            // If browser doesn't support speech, hide the button
            micBtn.style.display = 'none';
        }
    }
});