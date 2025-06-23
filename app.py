import streamlit as st
from rag1 import initialize_components, return_docs,generate_answer, check_access,process_docs
import time
# Configure Streamlit page
st.set_page_config(
    page_title="Role-Based Document Q&A System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    .position-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        padding: 0.75rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        padding: 0.75rem;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'position_set' not in st.session_state:
    st.session_state.position_set = False
if 'current_position' not in st.session_state:
    st.session_state.current_position = None
if 'docs_loaded' not in st.session_state:
    st.session_state.docs_loaded = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Main header
st.markdown("""
<div class="main-header">
    <h1>📚 Role-Based Document Q&A System</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar for position selection and system info
with st.sidebar:
    st.header("🔐 Access Control")
    
    # Role selection
    if not st.session_state.position_set:
        st.subheader("Select Your Role")
        role_options = ['finance', 'marketing', 'hr', 'engineering', 'executive', 'employee']
        selected_role = st.selectbox(
            "Choose your role:",
            options=role_options,
            help="Your role determines which documents you can access"
        )

        if st.button("Set Role", type="primary"):
            with st.spinner("Checking access rights..."):
                access_rights = check_access(selected_role)
                if access_rights:
                    st.session_state.current_position = selected_role
                    st.session_state.position_set = True
                    st.success(f"Role set to: {selected_role.title()}")
                    st.rerun()
                else:
                    st.error("Invalid role or no access rights.")

    else:
        # Show current role and access rights
        st.markdown(f"""
        <div class="position-card" style="color: black;">
            <h4 style="color: black;">Current Role: {st.session_state.current_position.title()}</h4>
            <p style="color: black;"><strong>Access to folders:</strong></p>
            <ul style="color: black;">
        """, unsafe_allow_html=True)
        
        access_folders = check_access(st.session_state.current_position)
        for folder in access_folders:
            st.markdown(f"<li>{folder.title()}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)

        # Button to change role
        if st.button("Change Role"):
            st.session_state.position_set = False
            st.session_state.docs_loaded = False
            st.session_state.initialized = False
            st.session_state.chat_history = []
            st.rerun()
    
    st.divider()
    

# Main content area
if not st.session_state.position_set:
    st.info("👈 Please select your Role from the sidebar to get started.")
    
    # Show access rights information
    st.subheader("📋 Role Access Rights")
    access_info = {
        'Finance': ['Finance', 'Marketing', 'General'],
        'Marketing': ['Marketing'],
        'HR': ['HR'],
        'Engineering': ['Engineering'],
        'Executive': ['All folders (Marketing, Finance, General, HR, Engineering)'],
        'Employee': ['General']
    }

    for role, access in access_info.items():
        with st.expander(f"{role} Access"):
            st.write(f"**Folders accessible:** {', '.join(access)}")

else:
    # Initialize components if not done
    if not st.session_state.initialized:
        with st.spinner("Initializing system components..."):
            try:
                initialize_components()
                st.session_state.initialized = True
                st.success("System components initialized successfully!")
            except Exception as e:
                st.error(f"Error initializing components: {str(e)}")
                st.stop()
    
    # Load documents if not done
    if not st.session_state.docs_loaded:
        with st.spinner("Loading documents based on your access rights..."):
            try:
                all_docs = return_docs(st.session_state.current_position)
                if all_docs:
                    process_docs(all_docs)
                    st.session_state.docs_loaded = True
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ Successfully loaded {len(all_docs)} documents for position: {st.session_state.current_position.title()}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-message">
                        ❌ No documents found in your accessible folders.
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading documents: {str(e)}")
                st.stop()
    
    # Chat interface
    if st.session_state.docs_loaded:
        st.subheader("💬 Ask Questions About Your Documents")
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("📝 Chat History")
            for i, (question, answer, sources) in enumerate(st.session_state.chat_history):
                with st.expander(f"Q{i+1}: {question[:50]}{'...' if len(question) > 50 else ''}"):
                    st.write(f"**Question:** {question}")
                    st.write(f"**Answer:** {answer}")
                    if sources:
                        st.write(f"**Sources:** {sources}")
                    else:
                        st.write("**Sources:** No sources found")
        
        # Input for new question
        user_question = st.text_input(
            "Enter your question:",
            placeholder="e.g., What are the marketing strategies mentioned in the documents?",
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            ask_button = st.button("Ask Question", type="primary")
        with col2:
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
        
        if ask_button and user_question:
            with st.spinner("Searching for answers..."):
                try:
                    answer, sources = generate_answer(user_question)
                    
                    # Add to chat history
                    st.session_state.chat_history.append((user_question, answer, sources))
                    
                    # Display current answer
                    st.subheader("🤖 Answer")
                    st.write(answer)
                    
                    if sources:
                        st.subheader("📚 Sources")
                        st.write(sources)
                    else:
                        st.info("No specific sources found for this answer.")
                        
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
        
        elif ask_button and not user_question:
            st.warning("Please enter a question before clicking 'Ask Question'.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Built with Streamlit • Powered by LangChain & Groq"
    "</div>",
    unsafe_allow_html=True
)