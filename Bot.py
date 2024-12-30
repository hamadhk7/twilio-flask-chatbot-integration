from flask import Flask, request, render_template, redirect
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.voice_response import Gather
from twilio.rest import Client
import requests
import urllib.parse
from twilio.base.exceptions import TwilioRestException

# Twilio credentials (replace with your actual credentials)
TWILIO_ACCOUNT_SID ="SID"TWILIO_AUTH_TOKEN = "auth_token"
TWILIO_PHONE_NUMBER = "phone_number"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
messages = []
app = Flask(_name_)

# Your existing chatbot logic to generate responses
def chat_with_llama(messages):
    endpoint = 'https://api.together.xyz/v1/chat/completions'
    headers = {
        "Authorization": "together_ai token",
    }
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": .8,
        "top_k": 75,
        "repetition_penalty": 1 ,
        "stop": ["[/INST]", "</s>"],
        "messages": messages
    }

    response = requests.post(endpoint, json=payload, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content'].strip()
        else:
            return "Sorry, I didn't understand that. Could you please rephrase?"
    else:
        return f"Error: {response.status_code} - {response.text}"

# Handle incoming calls and initiate a chatbot conversation
@app.route("/call-response", methods=["GET", "POST"])
def call_response():
    # Log the request data
    print("Request data:", request.args)

    # Retrieve parameters
    product_name = request.args.get('product_name')
    product_description = request.args.get('product_description')
    product_price = request.args.get('product_price')
    product_discounts = request.args.get('product_discounts')

    # Check if parameters are present and log them
    print(f"Product Name: {product_name}")
    print(f"Product Description: {product_description}")
    print(f"Product Price: {product_price}")
    print(f"Product Discounts: {product_discounts}")

    if not all([product_name, product_description, product_price, product_discounts]):
        return "Missing parameters", 400
    
    # Generate chatbot message
    system_message_content = (
        f"<human>: Hi! <bot>: Hi there! My name is Saad and I am a representative of Talkative. "
        f"I am here to answer your questions about {product_name}. The product description is {product_description}. "
        f"The price of the product is {product_price}. Discounts available: {product_discounts}. "
        "I am kind, friendly, professional, and very persuasive. My answers are human-like and I am very careful with my tone. "
        "i dont introduce myself again and again.i keep the conversation natural and engaging making sure that the person is not bored by keeping my answers short and to the point, making sure to interact with the customer after every few lines."
        "i dont repeat the product name very often."
        "I can also give answers to questions like 'How are you?' which is that 'i am fine and happy to assist you today'."
        "when someone asks 'where can i buy this ?' i answer 'we will text you the details if you are interested'."
        "I am careful to only provide factual short answers, and when I’m not sure of the answer I say 'Sorry, I don’t have an answer for you on that. "
        "Sorry I wasn’t able to help!'"
    )

    # Prepare messages for the chatbot
    messages.append({"content": system_message_content, "role": "system"})
    user_input = "generate a 2 to 3 line marketing statement for the product.it should be human like and persuasive. keep it short and list the features without explaining them. use terms like You and Yours to make the customer feel needed. create a sense of urgency. Also state your name and company and greet the user .At the end also say 'if you have any questions feel free to ask.' "
    messages.append({"role": "user", "content": user_input})
    # Call the chatbot
    initial_response = chat_with_llama(messages)

    if not initial_response:
        print("Chatbot response is empty.")
        return "Error: Chatbot response is empty", 500

    print(initial_response)
    messages.append({"role": "assistant", "content": initial_response})
    # Twilio Voice Response
    response = VoiceResponse()
    response.say(initial_response)
    response.gather(input="speech", action="/gather-response", speech_timeout="auto", method="POST")
    return str(response)


@app.route("/gather-response", methods=["POST"])
def gather_response():
    # Initialize the VoiceResponse object
    response = VoiceResponse()
    # Get user speech input from the call
    user_input = request.form.get('SpeechResult')
    print(f"User input: {user_input}")
    # If no input is provided, prompt agains
    if not user_input:
        response.say("Sorry, I didn't catch that. Could you please repeat?")
        response.gather(input="speech", action="/gather-response", speech_timeout="auto", method="POST")
        return str(response)
    if user_input.lower() in ['bye', 'good bye', 'thankyou goodbye','thank you, goodbye','thank you good bye','thankyou good bye', 'exit', 'have a nice day, bye' 'goodbye', 'thank you so much', 'bye have a nice day']:
        goodbye_message = "Thank you for chatting with Talkative. Have a great day! Goodbye!"
        print(f"Saad: {goodbye_message}")
        response.say(goodbye_message)
        response.hangup()  # This will end the call
        return str(response)
    if user_input == 'sorry speak again':
        print("Sorry, there was an issue. Please speak again.")
    else:
        messages.append({"role": "user", "content": user_input})
        answer = chat_with_llama(messages)
        response = VoiceResponse()
        print(answer)
        response.say(answer)
        messages.append({"role": "assistant", "content": answer})
        print(messages)
    
    # Continue the conversation by asking for more input
    response.gather(input="speech", action="/gather-response", speech_timeout="auto", method="POST")

    return str(response)

import urllib.parse

def initiate_call(to_number, product_name, product_description, product_price, product_discounts):
    try:
        # URL-encode the query parameters to make them safe for the URL
        encoded_product_name = urllib.parse.quote(product_name)
        encoded_product_description = urllib.parse.quote(product_description)
        encoded_product_price = urllib.parse.quote(product_price)
        encoded_product_discounts = urllib.parse.quote(product_discounts)

        # Construct the URL with encoded parameters
        url = (
            f'https://awaited-squirrel-major.ngrok-free.app/call-response'
            f'?product_name={encoded_product_name}&product_description={encoded_product_description}'
            f'&product_price={encoded_product_price}&product_discounts={encoded_product_discounts}'
        )

        # Initiate the Twilio call
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=url  # Twilio will call this URL
        )

       
        return call.sid

    except TwilioRestException as e: 
        # Handle errors from the Twilio API
        print(f"Twilio API error: {e}")
        return None
    except Exception as e:
        # Handle any other unexpected exceptions
        print(f"An error occurred: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/call.html')
def nextpage():
    return render_template('call.html')

@app.route('/main.html')
def mainpage():
    return render_template('main.html')

@app.route('/chat', methods=['POST'])
def chat():
    product_name = request.form.get('product_name')
    product_description = request.form.get('product_description')
    product_price = request.form.get('product_price')
    product_discounts = request.form.get('product_discounts')
    to_number = request.form.get('phone_number')  # User's phone number

    # Initiate the call
    call_sid = initiate_call(to_number, product_name, product_description, product_price, product_discounts)

    return f"Call initiated with SID: {call_sid}"

if _name_ == "_main_":
    app.run(debug=True)



from flask import Flask, request

app = Flask(_name_)


#----------------------------------for later use ---------------------------------------
# @app.route('/status', methods=['POST'])
# def call_status():
#     call_sid = request.form.get('CallSid')
#     call_status = request.form.get('CallStatus')
#     from_number = request.form.get('From')
#     to_number = request.form.get('To')

#     print(f"Call SID: {call_sid}")
#     print(f"Status: {call_status}")
#     print(f"From: {from_number}")
#     print(f"To: {to_number}")

#     return 'Status received', 200

# if _name_ == "_main_":
#     app.run(debug=True)