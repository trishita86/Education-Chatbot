import os
import sqlite3
import hashlib
from dotenv import load_dotenv
from datetime import datetime
import time
import streamlit as st
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Check if API key is available
if not api_key:
    st.error("No API key found! Please add your API key to an .env file or secrets.toml.")

# Initialize OpenAI client directly with API key
client = OpenAI(api_key=api_key)

# List of non-educational topics to filter out
non_educational_topics = [
    "movie", "film", "song", "music", "place", "sports", "vacation", "travel", 
    "tourism", "restaurants", "shopping_mall", "shopping", "days_date_time", 
    "months", "medicines", "doctors", "hospitals", "celebrity", "gossip", "fashion",
    "weather", "politics", "news"
]

# SQLite database setup
def create_connection():
    conn = sqlite3.connect("users.db")
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Email already exists.")
    conn.close()

def verify_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user

def reset_password(email, new_password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
    conn.commit()
    conn.close()

# Initialize database
create_table()

# Function to check if the user's input is educational or not
def is_educational(user_input):
    user_input = user_input.lower()
    return not any(topic in user_input for topic in non_educational_topics)

# Function to call OpenAI API using client chat completion
def generate_response(user_input, chatbot_tone, age_group, education_level, field_of_study, learning_style, topics, skill_level, available_time):
    # Prepare messages list with system, user, and assistant roles
    messages = []

    if chatbot_tone:
        messages.append({
            "role": "system",
            "content": f"You are a helpful tutor who communicates in a {chatbot_tone.lower()} manner."
        })

    if age_group or education_level or field_of_study or learning_style or topics or skill_level or available_time:
        assistant_message = ""
        if age_group:
            assistant_message += f"Age- {age_group} years old\n"
        if education_level:
            assistant_message += f"Education- {education_level}\n"
        if field_of_study:
            assistant_message += f"Studying/Completed- {field_of_study}\n"
        if learning_style:
            assistant_message += f"Learning Style- {learning_style}\n"
        if topics:
            assistant_message += f"Interested in the topics- {', '.join(topics)}\n"
        if skill_level:
            assistant_message += f"Rating the skill Level- {skill_level}\n"
        if available_time:
            assistant_message += f"Dedicate to study- {available_time} hours per day\n"
        if assistant_message:
            messages.append({
                "role": "assistant",
                "content": assistant_message.strip()
            })

    messages.append({
        "role": "user",
        "content": user_input
    })

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=4096,
        temperature=0.7
    )

    # Extract the assistant's response
    chatbot_response = response.choices[0].message.content.strip() if response.choices else "No response from the model."

    # Add additional resources based on learning style
    additional_resources = ""
    if learning_style == "Reading":
        documentation_links = get_documentation_links(user_input)
        additional_resources = "\n\nAdditional Reading Resources:\n" + "\n".join(documentation_links)
    elif learning_style == "Watching Videos":
        youtube_links = get_youtube_video_links(user_input)
        additional_resources = "\n\nSuggested YouTube Videos:\n" + "\n".join(youtube_links)
    elif learning_style == "Listening to Audio":
        audio_clips = get_audio_clips(user_input)
        additional_resources = "\n\nSuggested Audio Clips:\n" + "\n".join(audio_clips)

    # Return the response with additional resources
    return chatbot_response + additional_resources

# Sample resource generators for documentation, videos, and audio (Placeholders)
def get_documentation_links(topic):
    return [f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"]

def get_youtube_video_links(topic):
    return [f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}"]

def get_audio_clips(topic):
    return [f"https://www.podcasts.com/search?q={topic.replace(' ', '+')}"]

# Initialize session state for storing context
if "context" not in st.session_state:
    st.session_state["context"] = ""
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# Custom CSS for background colors
st.markdown("""
   <style>
        .css-1d391kg {
            background-color: #ADD8E6;  /* Light Blue */
        }
        .css-1d391kg .css-1g55b52 {
            background-color: #FFB6C1;  /* Light Pink */
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        .center-title {
            text-align: center;
            margin-top: 50px; /* Adjust the margin as needed */
        }
        .welcome-message {
            text-align: center;
            font-size: 20px;
            font-weight: bold; /* Make the text bold */
            margin-top: 20px; /* Adjust as needed */
            margin-bottom: 40px; /* Add space below the welcome message */
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 class='center-title'>Educational Tutor Chatbot</h1>", unsafe_allow_html=True)

# Conditional display of welcome message
if not st.session_state.get("logged_in", False):
    st.markdown("""
        <div class='welcome-message'>
            WELCOME to The Educational Tutor Chatbot!!<br>
            In this application, you will be able to search information regarding education-related topics.<br>
            I hope you will enjoy this application.
        </div>
    """, unsafe_allow_html=True)

# Authentication logic
if not st.session_state["logged_in"]:
    st.sidebar.header("User Authentication")
    option = st.sidebar.selectbox("Choose an option:", ["Login", "Sign Up", "Forgot Password"])

    if option == "Sign Up":
       st.sidebar.subheader("Sign Up")
       email = st.sidebar.text_input("Email (must be an email address):")
       password = st.sidebar.text_input("Password:", type="password")
       if st.sidebar.button("Sign Up"):
          if email and password:
             if add_user(email, password):
                st.sidebar.success("User registered successfully. Please log in.")
             else:
                st.sidebar.warning("User already exists. Please use a different email address.")
          else:
            st.sidebar.error("Please enter both email and password.")

    elif option == "Login":
        st.sidebar.subheader("Login")
        email = st.sidebar.text_input("Email:", key="login_email")
        password = st.sidebar.text_input("Password:", type="password", key="login_password")
        if st.sidebar.button("Login"):
            if verify_user(email, password):
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = email
                st.sidebar.success("Logged in successfully.")
            else:
                st.sidebar.error("Invalid username or password.")
    
    elif option == "Forgot Password":
        st.sidebar.subheader("Forgot Password")
        email = st.sidebar.text_input("Email (must be an email address):", key="reset_email")
        new_password = st.sidebar.text_input("New Password:", type="password", key="new_password")
        confirm_password = st.sidebar.text_input("Confirm New Password:", type="password", key="confirm_password")
        if st.sidebar.button("Reset Password"):
            if new_password == confirm_password:
                reset_password(email, new_password)
                st.sidebar.success("Password reset successfully. Please log in with your new password.")
                st.sidebar.header("Welcome, " + st.session_state["current_user"])
            else:
                st.sidebar.error("Passwords do not match.")
else:
    #st.sidebar.header("Welcome, " + st.session_state["current_user"])
    st.sidebar.subheader("Customize Your Profile:-")
    
    # Sidebar components
    age_group = st.sidebar.selectbox("Select your age group:", ["", "Under 18", "18-25", "26-35", "36-50", "Above 50"], index=0)
    education_level = st.sidebar.radio("What's your current education level?", ["", "High School", "Undergraduate", "Postgraduate", "Graduated", "Other"], index=0)
    if education_level == "Other":
        other_education_level = st.sidebar.text_input("Please specify your education level:", "")
        if other_education_level:
            education_level = other_education_level

    field_of_study = st.sidebar.text_input("What is your field of study or main interest?", "")
    learning_style = st.sidebar.selectbox("How do you prefer to learn?", ["", "Reading", "Watching Videos", "Listening to Audio"])
    topics = st.sidebar.multiselect("What topics are you interested in?", ["Math", "Science", "History", "Literature", "Technology", "Art", "Other"])
    if "Other" in topics:
        other_topic = st.sidebar.text_input("Please specify the 'Other' topic", "")
        if other_topic:
            topics.append(other_topic)
            topics.remove("Other")

    skill_level = st.sidebar.slider("How would you rate your skill level in your selected topic(s)?", 0, 5, 0)
    available_time = st.sidebar.number_input("How many hours per day can you dedicate to learning?", min_value=0.0, max_value=24.0, step=0.5, value=0.0)
    chatbot_tone = st.sidebar.selectbox("How would you like the chatbot to communicate?", ["", "Formal", "Friendly", "Humorous", "Motivational"], index=0)

    # Construct the context based on sidebar inputs
    context = ""
    if chatbot_tone:
        context += f"You are a helpful tutor who communicates in a {chatbot_tone.lower()} manner.\n"

    st.session_state["context"] = context

    # Layout: User input first, then constructed prompt
    user_input = st.text_area("Ask me a question", st.session_state["user_input"], height=100, key="user_input")

    # Informational message to the user
    st.info("This chatbot is designed to assist with education and training-related queries. Please ask a question related to these topics.")

    # Constructed prompt with roles
    constructed_prompt = ""
    if chatbot_tone or age_group or education_level or field_of_study or learning_style or topics or skill_level or available_time:
        if chatbot_tone:
            constructed_prompt += f"System: You are a helpful tutor who communicates in a {chatbot_tone.lower()} manner.\n"
        
        if age_group or education_level or field_of_study or learning_style or topics or skill_level or available_time:
            constructed_prompt += f"Assistant:\n"
            
            if age_group:
                constructed_prompt += f"Age- {age_group} years old\n"
            if education_level:
                constructed_prompt += f"Education- {education_level}\n"
            if field_of_study:
                constructed_prompt += f"Studying/Completed- {field_of_study}\n"
            if learning_style:
                constructed_prompt += f"Learning Style- {learning_style}\n"
            if topics:
                constructed_prompt += f"Interested in the topics- {', '.join(topics)}\n"
            if skill_level:
                constructed_prompt += f"Rating the skill Level- {skill_level}\n"
            if available_time:
                constructed_prompt += f"Dedicate to study- {available_time} hours per day\n"
            
        constructed_prompt += f"user: {user_input}\n"
    else:
        constructed_prompt += f"user: {user_input}\n"

    # Display the constructed prompt with roles in a disabled text box
    st.text_area("Constructed Prompt", constructed_prompt.strip(), height=150, disabled=True, key="constructed_prompt")

    # Check if the question is educational and generate a response
    if st.button("Send", key="send_button"):
        user_input = st.session_state.get("user_input", "").strip()
        if user_input:
            if is_educational(user_input):
                with st.spinner("Generating response...."):
                    time.sleep(1)  # Simulate processing delay
                    chatbot_response = generate_response(user_input, chatbot_tone, age_group, education_level, field_of_study, learning_style, topics, skill_level, available_time)
                    st.success(chatbot_response)
            else:
                st.warning("Sorry, I can only provide educational-related information, not other topics. Thank you.")
        else:
            st.error("Please enter a question to receive a response.")

    # Clear chat functionality
    if st.button("Clear Chat"):
       # st.session_state["user_input"] = ""
        st.session_state["context"] = ""
        st.success("Chat cleared. Customize your experience again.")


    if st.sidebar.button("Logout"):
       st.session_state.clear()
       st.rerun()