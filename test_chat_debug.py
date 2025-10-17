#!/usr/bin/env python3
"""
Debug script to test chat functionality
"""

import streamlit as st
import asyncio
from datetime import datetime
from src.application.dependency_injection import DependencyContainer
from config import Config

st.set_page_config(page_title="Chat Debug", layout="wide")

def test_chat():
    st.title("🐛 Chat Debug Test")
    
    # Initialize container
    try:
        if 'container' not in st.session_state:
            st.session_state.container = DependencyContainer(Config)
            st.session_state.container.initialize()
            st.success("✅ Container initialized")
        
        container = st.session_state.container
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat input
        st.subheader("Chat Input")
        user_input = st.text_input(
            "Ask about AWS costs:", 
            placeholder="what is cost of ec2 instance",
            key="debug_chat_input"
        )
        
        # Debug info
        st.write("**Debug Info:**")
        st.write(f"- User input: '{user_input}'")
        st.write(f"- Input length: {len(user_input) if user_input else 0}")
        st.write(f"- Chat history length: {len(st.session_state.chat_history)}")
        
        # Process input
        if user_input and user_input.strip():
            st.write(f"**Processing input:** '{user_input}'")
            
            with st.spinner("Getting response..."):
                try:
                    chat_use_case = container.get_use_case('handle_chat')
                    st.write(f"✅ Got chat use case: {type(chat_use_case).__name__}")
                    
                    response = asyncio.run(chat_use_case.execute(user_input))
                    st.write(f"✅ Got response: {response[:100]}...")
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        'user': user_input,
                        'assistant': response,
                        'timestamp': datetime.now()
                    })
                    
                    st.success("✅ Added to chat history")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("Chat History")
            for i, chat in enumerate(st.session_state.chat_history):
                st.write(f"**{i+1}. You:** {chat['user']}")
                st.write(f"**Vismaya:** {chat['assistant']}")
                st.write(f"*Time: {chat['timestamp']}*")
                st.write("---")
        
        # Clear button
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()
            
    except Exception as e:
        st.error(f"Initialization error: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    test_chat()