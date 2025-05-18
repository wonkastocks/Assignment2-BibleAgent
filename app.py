import streamlit as st
import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from agents import Agent, Runner
from datetime import datetime
import time # Import the time module

def convert_to_rtf(messages):
    """Convert chat messages to RTF format"""
    print(f"Converting {len(messages)} messages to RTF")  # Debug print
    
    # RTF header with proper encoding
    rtf = """{\\rtf1\\ansi\\ansicpg1252\\cocoartf1671\\cocoasubrtf600
{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica;}
{\\colortbl;\\red0\\green0\\blue0;\\red0\\green0\\blue255;}
\\paperw12240\\paperh15840\\margl1440\\margr1440\\vieww9000\\viewh8400\\viewkind0
\\pard\\tx566\\tx1133\\tx1700\\tx2267\\tx2834\\tx3401\\tx3968\\tx4535\\tx5102\\tx5669\\tx6236\\tx6803\\pardirnatural\\partightenfactor0

\\f0\\fs24 \\cf0 """
    
    # Add title and timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rtf += "\\b\\fs32 Biblical Research Assistant\\b0\\fs24 \\line "
    rtf += f"Conversation Export ({current_time})\\line \\line "
    
    # Add messages
    for msg in messages:
        #print(f"Processing message: {msg['role']}")  # Debug print
        role = msg["role"].title()
        content = msg["content"]
        #print(f"Content length: {len(content)}")  # Debug print
        
        # Properly escape RTF special characters
        content = content.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        content = content.replace('\n', '\\line ').replace('\t', '\\tab ')
        
        if role == "User":
            rtf += f"\\b\\cf1 Question:\\b0\\line {content}\\line \\line "
        else:
            rtf += f"\\b\\cf2 Answer:\\b0\\line {content}\\line \\line "
    
    rtf += "}"
    #print(f"Final RTF length: {len(rtf)}")  # Debug print
    return rtf

def convert_to_text(messages):
    """Convert chat messages to plain text format"""
    text = ""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text += f"Biblical Research Assistant\n"
    text += f"Conversation Export ({current_time})\n\n"
    
    for msg in messages:
        role = msg["role"].title()
        content = msg["content"]
        
        if role == "User":
            text += f"Question:\n{content}\n\n"
        else:
            text += f"Answer:\n{content}\n\n"
    return text

# Callback to initiate processing
def start_download_processing():
    st.session_state.download_stage = 'processing'
    # No sleep here, the processing stage itself will handle it

# Function to reset download state
def reset_download_state():
    st.session_state.download_stage = 'initial'
    st.session_state.text_to_download = None

# Load environment variables
load_dotenv(override=True)

# Get OpenAI API key from Streamlit secrets or environment variable
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set it in Streamlit secrets or .env file")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Available Bible files and their IDs
BIBLE_FILES = [
    "file-V4yyhhCzR7yWdebFhbdAux",  # Dake's Bible
    "file-XRvTotmSL9abx5HesWdAXA",  # Amplified Bible
    "file-Na2HfiAj5sSadUaVN7tnH9",  # NLT Bible
    "file-CHv1fAte7y9v97VnWGYoec",  # KJV Bible
    "file-3LuZfb2iHvfa9af9XJMbp1",  # NIV Bible
    "file-KgkGzfvXk8cnmPyQN8eQB9",  # New Jerusalem Bible
    "file-S1qcaPHubwF7vAfmYCkov2",  # The Living Bible
    "file-BTxs4N7hfU8E9DRvgcH9k3",  # KJV Strong's Concordance
]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = True
if "use_knowledge_base" not in st.session_state:
    st.session_state.use_knowledge_base = True
if "text_to_download" not in st.session_state:
    st.session_state.text_to_download = None
if "download_stage" not in st.session_state: # 'initial', 'processing', 'ready_to_download'
    st.session_state.download_stage = 'initial'

# Streamlit UI
st.set_page_config(
    page_title="Biblical Research Assistant",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.title("📚 Biblical Research Assistant")
st.write("Ask questions about the Bible and explore different translations.")

# Sidebar controls
st.sidebar.title("Search Settings")

# Search options
st.sidebar.subheader("Search Options")
web_search = st.sidebar.checkbox("Include Web Search", value=st.session_state.use_web_search)
knowledge_base = st.sidebar.checkbox("Include Knowledge Base Search", value=st.session_state.use_knowledge_base)

# Update search preferences
st.session_state.use_web_search = web_search
st.session_state.use_knowledge_base = knowledge_base

# Clear conversation button
st.sidebar.subheader("Conversation Controls")
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.session_state.agent = None
    reset_download_state() # Reset download stage
    st.rerun()

# Simplified Download Process
st.sidebar.subheader("Download Conversation")

# Stateful Download UI
if st.session_state.download_stage == 'initial':
    initial_button_disabled = not st.session_state.get("messages", [])
    st.sidebar.button(
        "Process & Download Chat (TXT)",
        on_click=start_download_processing,
        disabled=initial_button_disabled,
        key="initiate_download_process_btn"
    )
elif st.session_state.download_stage == 'processing':
    st.sidebar.info("Processing conversation... please wait.")
    # Perform the actual processing and delay here
    current_messages = st.session_state.get("messages", [])
    if current_messages:
        generated_text = convert_to_text(current_messages)
        st.session_state.text_to_download = generated_text
        time.sleep(5) # The 5-second delay
        st.session_state.download_stage = 'ready_to_download'
    else:
        # Should not happen if button was enabled, but as a fallback
        reset_download_state()
    st.rerun() # Force rerun to show the download button or revert

elif st.session_state.download_stage == 'ready_to_download':
    if st.session_state.get("text_to_download"):
        st.sidebar.download_button(
            label="Click Here to Download TXT",
            data=st.session_state.text_to_download,
            file_name="conversation_export.txt",
            mime="text/plain",
            key="final_download_action_btn",
            on_click=reset_download_state # Reset state after download click
        )
    else:
        # If somehow no text to download, revert to initial state
        st.sidebar.warning("No data to download. Please try again.")
        reset_download_state()
        st.rerun()

# Example questions
with st.sidebar.expander("Example Questions"):
    example_questions = [
        "Compare how different versions translate John 3:16",
        "What does the original Greek word mean in Romans 8:28?",
        "Show me Psalm 23 in multiple translations",
        "Explain the meaning of 'selah' in Psalms",
        "What are the different translations of the Lord's Prayer?",
        "Search for verses about love and compare translations"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"example_{question}"):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Researching..."):
                    try:
                        result = asyncio.run(Runner.run(st.session_state.agent, question))
                        response = result.final_output
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"An error occurred: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": f"*{error_msg}*"})
            st.rerun()

def ensure_agent():
    if not st.session_state.agent:
        try:
            with open('prompt.txt', 'r') as file:
                instructions = file.read()
            search_config = "\n\nSearch Configuration:"
            if st.session_state.use_web_search:
                search_config += "\n- Web search is enabled for additional context"
            if st.session_state.use_knowledge_base:
                search_config += "\n- Bible Knowledge Base search is enabled"
            instructions += search_config
        except FileNotFoundError:
            st.error("prompt.txt not found. Please ensure the file exists in the same directory as app.py")
            return None
        st.session_state.agent = Agent(
            name="Biblical Research Assistant",
            instructions=instructions
        )
    return st.session_state.agent

ensure_agent()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_question := st.chat_input("Ask your Bible research question"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)
    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                result = asyncio.run(Runner.run(st.session_state.agent, user_question))
                response = result.final_output
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": f"*{error_msg}*"})
            st.rerun()