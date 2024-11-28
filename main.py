import streamlit as st
import autogen
import logging
from datetime import datetime
import os
from fpdf import FPDF
from dotenv import load_dotenv
import json
from pathlib import Path

# Set up logging
logging.basicConfig(
    filename=f'app_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_config(api_key=None):
    """Sets up the configuration for the autogen agents.
    
    Args:
        api_key (str, optional): The Groq API key. If None, will check environment variables.
        
    Returns:
        dict: Configuration dictionary for the agents
    """
    logger.info("Setting up configuration")
    
    try:
        # Get API key from environment if not provided
        api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not api_key:
            raise ValueError("No API key provided. Please set GROQ_API_KEY in .env file or provide it directly.")
        
        config_list = [{
            'model': 'llama3-8b-8192',
            "api_type": "groq",
            "api_key": api_key,
        }]
        
        return {
            "cache_seed": 42,
            "temperature": 0,
            "config_list": config_list,
            "timeout": 120,
        }
    except Exception as e:
        logger.error(f"Error in setup_config: {str(e)}")
        raise

def create_agents(config, prompts):
    """Creates the autogen agents with the given configuration and prompts."""
    logger.info("Creating agents")
    try:
        # Create user proxy agent
        user_proxy = autogen.UserProxyAgent(
            name="user",
            system_message="A person seeking advice about apartment purchase",
            code_execution_config=False,
            human_input_mode="NEVER",
        )

        # Create all expert agents
        experts = []
        for i in range(1, 7):  # Create all 6 experts
            expert = autogen.AssistantAgent(
                name=prompts[f'expert{i}_name'],
                system_message=prompts[f'expert{i}_prompt'],
                llm_config={"config_list": config["config_list"]}
            )
            experts.append(expert)

        # Return all agents (user_proxy + experts)
        all_agents = [user_proxy] + experts
        logger.info(f"Created {len(all_agents)} agents successfully")
        return all_agents

    except Exception as e:
        logger.error(f"Error creating agents: {str(e)}")
        raise

def create_output_directory():
    """Create necessary output directories if they don't exist.
    
    Creates:
        - outputs/: Main output directory
        - outputs/prompts/: For prompt JSON files
        - outputs/results/: For analysis results
    """
    logger.info("Creating output directories")
    try:
        Path("outputs/prompts").mkdir(parents=True, exist_ok=True)
        Path("outputs/results").mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {str(e)}")
        return False

def save_prompts_to_json(prompts):
    """Save prompts to a JSON file with timestamp.
    
    Args:
        prompts (dict): Dictionary containing the prompts
        
    Returns:
        str: Path to saved file or None if error
    """
    try:
        # Validate prompts before saving
        is_valid, error_message = validate_prompts(prompts)
        if not is_valid:
            st.error(f"Invalid prompts: {error_message}")
            return None
            
        # Create outputs directory if it doesn't exist
        Path("outputs").mkdir(exist_ok=True)
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"outputs/prompts_{timestamp}.json"
        
        # Save prompts to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=4)
            
        logger.info(f"Prompts saved successfully to {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving prompts: {str(e)}")
        return None

def save_output():
    """Save the consultation output in selected format."""
    logger.info("Starting save_output function")
    
    try:
        # Check if there's content to save
        if 'result' not in st.session_state:
            logger.error("No result found in session state")
            st.error("❌ No content to save. Please run the consultation first.")
            return
            
        if not st.session_state.result:
            logger.error("Result in session state is empty")
            st.error("❌ No content to save. The consultation result is empty.")
            return
            
        logger.info("Found valid content in session state")
        
        # Create save interface
        st.subheader("Save Results")
        output_format = st.radio(
            "Save output as:",
            ["MD", "PDF"],
            key="save_format"
        )
        logger.info(f"Selected output format: {output_format}")
        
        if st.button("Save Output", key="save_button"):
            logger.info("Save button clicked")
            
            # Ensure output directory exists
            try:
                os.makedirs("outputs/results", exist_ok=True)
                logger.info("Output directory verified/created")
            except Exception as e:
                logger.error(f"Failed to create output directory: {str(e)}")
                st.error("❌ Failed to create output directory")
                return
            
            # Format content
            try:
                content = st.session_state.result
                if isinstance(content, list):
                    content = "\n\n".join(content)
                elif isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                logger.info("Content formatted successfully")
            except Exception as e:
                logger.error(f"Failed to format content: {str(e)}")
                st.error("❌ Failed to format content for saving")
                return
            
            # Generate timestamp and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format == "MD":
                try:
                    output_path = f"outputs/results/consultation_{timestamp}.md"
                    logger.info(f"Attempting to save markdown file: {output_path}")
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write("# Expert Consultation Results\n\n")
                        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write("## Consultation Output\n\n")
                        f.write(str(content))  # Ensure content is string
                    
                    logger.info("Markdown file saved successfully")
                    st.success(f"✅ Saved as Markdown: {output_path}")
                    
                    # Create download button
                    with open(output_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        st.download_button(
                            label="📥 Download MD File",
                            data=file_content,
                            file_name=f"consultation_{timestamp}.md",
                            mime="text/markdown",
                            key="md_download"
                        )
                    logger.info("Download button created successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to save markdown file: {str(e)}")
                    st.error(f"❌ Error saving markdown: {str(e)}")
                    
            else:  # PDF
                try:
                    logger.info("Attempting to save as PDF")
                    output_path = f"outputs/results/consultation_{timestamp}.pdf"
                    
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    
                    # Split content into lines and write
                    clean_content = str(content).encode('latin-1', 'replace').decode('latin-1')
                    lines = clean_content.split('\n')
                    for line in lines:
                        pdf.multi_cell(0, 10, txt=line)
                    
                    pdf.output(output_path)
                    logger.info(f"PDF saved successfully: {output_path}")
                    
                    # Create download button
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f.read(),
                            file_name=f"consultation_{timestamp}.pdf",
                            mime="application/pdf",
                            key="pdf_download"
                        )
                    logger.info("PDF download button created successfully")
                    
                    st.success(f"✅ Saved as PDF: {output_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to save PDF: {str(e)}")
                    st.error(f"❌ Error saving PDF: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in save_output: {str(e)}")
        st.error(f"❌ An unexpected error occurred: {str(e)}")

def load_prompts_from_json(file):
    """Load prompts from a JSON file.
    
    Args:
        file: Uploaded file object
        
    Returns:
        dict: Loaded prompts or None if invalid
    """
    try:
        prompts = json.load(file)
        # Validate the loaded prompts
        is_valid, error_message = validate_prompts(prompts)
        if is_valid:
            return prompts
        else:
            logger.error(f"Invalid prompts loaded: {error_message}")
            return None
    except Exception as e:
        logger.error(f"Error loading prompts: {str(e)}")
        return None

def initialize_default_prompts():
    """Initialize default prompts for the experts.
    
    Returns:
        dict: Default prompts configuration
    """
    return {
        'task_description': 'You are trying to purchase an apartment. You seek advice and guidance from experts.',
        'expert1_name': 'real_estate_agent',
        'expert1_prompt': 'You are a professional real estate agent. Provide guidance on property selection, market analysis, and negotiation strategies.',
        'expert2_name': 'financial_advisor',
        'expert2_prompt': 'You are a financial advisor. Provide advice on budgeting, mortgages, and financial planning for property purchase.',
        'expert3_name': 'property_inspector',
        'expert3_prompt': 'You are a property inspector. Assess building condition, identify potential issues, and provide maintenance insights.',
        'expert4_name': 'legal_advisor',
        'expert4_prompt': 'You are a legal advisor. Guide through contracts, legal requirements, and property law considerations.',
        'expert5_name': 'neighborhood_specialist',
        'expert5_prompt': 'You are a neighborhood specialist. Provide insights on location, amenities, development plans, and community aspects.',
        'expert6_name': 'interior_designer',
        'expert6_prompt': 'You are an interior designer. Advise on layout optimization, renovation potential, and space utilization.'
    }

def validate_prompts(prompts):
    """Validate that all required prompt fields are present and non-empty.
    
    Args:
        prompts (dict): Dictionary of prompts to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    required_fields = [
        'task_description',
        'expert1_name', 'expert1_prompt',
        'expert2_name', 'expert2_prompt',
        'expert3_name', 'expert3_prompt',
        'expert4_name', 'expert4_prompt',
        'expert5_name', 'expert5_prompt',
        'expert6_name', 'expert6_prompt'
    ]
    
    try:
        # Check for missing fields
        for field in required_fields:
            if field not in prompts:
                return False, f"Missing field: {field}"
            if not isinstance(prompts[field], str):
                return False, f"Invalid type for {field}: expected string"
            if not prompts[field].strip():
                return False, f"Empty field: {field}"
        return True, ""
    except Exception as e:
        return False, str(e)

def format_chat_message(message):
    """Format a chat message for display.
    
    Args:
        message (dict): Message dictionary containing 'name' and 'content'
        
    Returns:
        str: Formatted message string
    """
    return f"**{message['name']}**: {message['content']}\n\n---\n\n"

def stream_agent_output(result):
    """Stream the agent output to the Streamlit interface.
    
    Args:
        result: The result from the agent chat
    """
    try:
        placeholder = st.empty()
        messages = []
        
        for message in result.chat_history:
            messages.append(f"**{message['name']}**: {message['content']}\n\n---\n\n")
            placeholder.markdown("".join(messages))
            
        # Store formatted content in session state for saving
        st.session_state.formatted_content = "".join(messages)
        
        logger.info("Agent output streamed successfully")
    except Exception as e:
        logger.error(f"Error streaming output: {str(e)}")
        st.error("Error displaying chat results")

def create_prompts_tab():
    """Creates and manages the prompts tab interface."""
    try:
        st.header("Prompt Management")
        
        # Initialize prompts if not in session state
        if 'prompts' not in st.session_state:
            st.session_state.prompts = initialize_default_prompts()
            logger.info("Initialized default prompts in session state")
        
        # Create columns for load/save functionality
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader(
                "Load prompts configuration",
                type=['json'],
                help="Upload a JSON file containing prompt configurations"
            )
            if uploaded_file is not None:
                try:
                    loaded_prompts = json.loads(uploaded_file.getvalue().decode('utf-8'))
                    st.session_state.prompts = loaded_prompts
                    logger.info("Successfully loaded prompts from uploaded file")
                    st.success("✅ Prompts loaded successfully!")
                except Exception as e:
                    logger.error(f"Error loading prompts file: {str(e)}")
                    st.error(f"Error loading prompts. Please check the file format. Error: {str(e)}")
        
        with col2:
            if st.button("Save Current Configuration"):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"outputs/prompts/prompts_{timestamp}.json"
                    
                    # Create directory if it doesn't exist
                    os.makedirs("outputs/prompts", exist_ok=True)
                    
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(st.session_state.prompts, f, indent=4)
                    
                    logger.info(f"Saved prompts configuration to {save_path}")
                    st.success("✅ Configuration saved!")
                    
                    # Create download button
                    with open(save_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Configuration",
                            data=f,
                            file_name=f"prompts_{timestamp}.json",
                            mime="application/json"
                        )
                except Exception as e:
                    logger.error(f"Error saving prompts configuration: {str(e)}")
                    st.error(f"Error saving configuration. Error: {str(e)}")
        
        # Task Description Section
        st.subheader("Task Description")
        task_description = st.text_area(
            "Edit task description:",
            value=st.session_state.prompts['task_description'],
            height=100
        )
        st.session_state.prompts['task_description'] = task_description
        
        # Expert Configuration Section
        st.subheader("Expert Configuration")
        expert_tabs = st.tabs([f"Expert {i}" for i in range(1, 7)])
        
        for i, tab in enumerate(expert_tabs, 1):
            with tab:
                try:
                    # Using timestamp in key to ensure uniqueness
                    tab_id = f"tab_{i}_{datetime.now().strftime('%Y%m%d')}"
                    
                    expert_name = st.text_input(
                        f"Expert {i} Role:",
                        value=st.session_state.prompts[f'expert{i}_name'],
                        key=f'expert{i}_name_{tab_id}'  # Updated unique key
                    )
                    st.session_state.prompts[f'expert{i}_name'] = expert_name
                    
                    expert_prompt = st.text_area(
                        f"Expert {i} Prompt:",
                        value=st.session_state.prompts[f'expert{i}_prompt'],
                        height=150,
                        key=f'expert{i}_prompt_{tab_id}'  # Updated unique key
                    )
                    st.session_state.prompts[f'expert{i}_prompt'] = expert_prompt
                    
                    # Preview section
                    st.markdown(f"### Preview for Expert {i}:")
                    st.markdown(f"**{expert_name}**: {expert_prompt}")
                    
                except Exception as e:
                    logger.error(f"Error in Expert {i} tab: {str(e)}")
                    st.error(f"Error loading Expert {i} configuration. Error: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in prompts tab: {str(e)}")
        st.error("Error loading prompts tab content")

def initialize_session_state():
    """Initialize session state variables."""
    try:
        if 'prompts' not in st.session_state:
            logger.info("Initializing session state with default prompts")
            st.session_state.prompts = initialize_default_prompts()
        if 'result' not in st.session_state:
            st.session_state.result = None
        if 'formatted_content' not in st.session_state:
            st.session_state.formatted_content = None
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        raise

def get_api_key():
    """Get API key from session state or environment variables.
    
    Returns:
        str: API key if found, None otherwise
    """
    try:
        # Check session state first
        if 'api_key' in st.session_state and st.session_state.api_key:
            return st.session_state.api_key
            
        # Check environment variables
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            st.session_state.api_key = api_key
            return api_key
            
        return None
        
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        return None

def main():
    """Main function to run the Streamlit application."""
    try:
        st.set_page_config(layout="wide")
        st.title("Expert Consultation Assistant")
        
        # Initialize session state first
        initialize_session_state()
        
        # Create output directories
        if not create_output_directory():
            st.error("Error creating output directories. Check logs for details.")
            return

        # Create tabs
        tab_main, tab_prompts, tab_help, tab_source, tab_reqs, tab_logs = st.tabs([
            "Main", "Prompts", "Help", "Source Code", "Requirements", "Logs"
        ])

        # Main tab
        with tab_main:
            left_col, right_col = st.columns([1, 2])
            
            with left_col:
                st.subheader("Configuration")
                # API Key input with default from environment
                api_key = st.text_input(
                    "Enter your Groq API key:",
                    value=get_api_key() or "",  # Changed from load_api_key to get_api_key
                    type="password",
                    help="Enter your Groq API key to enable the consultation. You can also set GROQ_API_KEY in your .env file."
                )
                
                # Store API key in session state if provided
                if api_key:
                    st.session_state.api_key = api_key
                
                # Show API key status
                if get_api_key():  # Changed from load_api_key to get_api_key
                    st.success("✅ API Key configured")
                else:
                    st.warning("⚠️ No API Key found. Please enter your Groq API key or set GROQ_API_KEY in your .env file.")

                st.subheader("Task Description")
                task_description = st.text_area(
                    "Edit task description:",
                    value=st.session_state.prompts['task_description']
                )
                st.session_state.prompts['task_description'] = task_description

                # Expert Configuration
                st.subheader("Expert Configuration")
                expert_tabs = st.tabs([f"Expert {i}" for i in range(1, 7)])
                
                for i, tab in enumerate(expert_tabs, 1):
                    with tab:
                        expert_name = st.text_input(
                            f"Expert {i} Role:",
                            value=st.session_state.prompts[f'expert{i}_name'],
                            key=f'expert{i}_name_input'
                        )
                        st.session_state.prompts[f'expert{i}_name'] = expert_name
                        
                        expert_prompt = st.text_area(
                            f"Expert {i} Prompt:",
                            value=st.session_state.prompts[f'expert{i}_prompt'],
                            height=100,
                            key=f'expert{i}_prompt_input'
                        )
                        st.session_state.prompts[f'expert{i}_prompt'] = expert_prompt

                # Start Consultation button
                if st.button("Start Consultation", type="primary"):
                    if not api_key:
                        st.error("Please enter your API key first")
                    else:
                        run_consultation(api_key, st.session_state.prompts, right_col)

            with right_col:
                st.subheader("Consultation Results")
                if 'result' in st.session_state:
                    stream_agent_output(st.session_state.result)
                    
                    st.subheader("Save Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        output_format = st.radio(
                            "Save output as:",
                            ('MD', 'PDF')
                        )
                    
                    with col2:
                        if st.button("Save Output"):
                            if 'formatted_content' in st.session_state:
                                file_path = save_output(
                                    st.session_state.formatted_content,
                                    output_format.lower()
                                )
                                if file_path:
                                    st.success(f"Output saved to {file_path}")
                                    with open(file_path, 'rb') as f:
                                        st.download_button(
                                            label=f"Download {output_format}",
                                            data=f,
                                            file_name=os.path.basename(file_path),
                                            mime="application/pdf" if output_format.lower() == 'pdf' else "text/markdown"
                                        )
                                else:
                                    st.error("Error saving output")
                            else:
                                st.error("No content to save. Please run the consultation first.")

        # Prompts tab
        with tab_prompts:
            create_prompts_tab()

        # Help tab
        with tab_help:
            with open("README.md", "r", encoding='utf-8') as f:
                st.markdown(f.read())

        # Source Code tab
        with tab_source:
            with open("main.py", "r", encoding='utf-8') as f:
                st.code(f.read(), language="python")

        # Requirements tab
        with tab_reqs:
            with open("requirements.txt", "r", encoding='utf-8') as f:
                st.code(f.read(), language="text")

        # Logs tab
        with tab_logs:
            if os.path.exists("app.log"):
                with open("app.log", "r", encoding='utf-8') as f:
                    st.code(f.read(), language="text")
            else:
                st.info("No logs available yet.")

    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

# Add these helper functions
def update_expert_prompt(expert_name, task_description):
    """Update expert prompt with task description.
    
    Args:
        expert_name (str): Name of the expert
        task_description (str): Current task description
        
    Returns:
        str: Updated prompt
    """
    return f"You are a professional {expert_name} with years of experience. You are to assist with {task_description}"

def run_consultation(api_key, prompts, right_col):
    """Run the consultation with all experts."""
    try:
        with right_col:
            with st.spinner("Running consultation..."):
                config = setup_config(api_key)
                agents = create_agents(config, prompts)
                
                # Create group chat with all agents
                groupchat = autogen.GroupChat(
                    agents=agents,
                    messages=[],
                    max_round=12  # Increased to allow more interaction
                )
                
                # Configure manager with specific speaking order
                manager = autogen.GroupChatManager(
                    groupchat=groupchat,
                    llm_config=config,
                    system_message="""Manage a group discussion about apartment purchase. 
                    Ensure each expert contributes their specific expertise:
                    1. Real estate agent for property insights
                    2. Financial advisor for budget and mortgage advice
                    3. Property inspector for condition assessment
                    4. Legal advisor for contract and legal matters
                    5. Neighborhood specialist for location insights
                    6. Interior designer for layout and renovation potential"""
                )

                # Initiate chat with specific instructions for expert participation
                result = agents[0].initiate_chat(
                    manager,
                    message=f"""Please provide comprehensive advice regarding: {prompts['task_description']}
                    Each expert should contribute their specific expertise to the discussion."""
                )

                st.session_state.result = result
                stream_agent_output(result)

    except Exception as e:
        logger.error(f"Error during consultation: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def save_as_pdf(content, filename):
    """Save content as PDF with proper Unicode handling.
    
    Args:
        content (str): Content to save
        filename (str): Output filename
        
    Returns:
        str: Path to saved file or None if error
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Add Unicode font support
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # Clean and encode content
        clean_content = content.encode('latin-1', 'replace').decode('latin-1')
        
        # Split content into lines and write
        lines = clean_content.split('\n')
        for line in lines:
            pdf.multi_cell(0, 10, txt=line)
            
        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"outputs/results/{filename}_{timestamp}.pdf"
        
        # Ensure directory exists
        os.makedirs("outputs/results", exist_ok=True)
        
        pdf.output(output_path)
        logger.info(f"Successfully saved PDF to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving PDF: {str(e)}")
        return None

if __name__ == "__main__":
    main() 