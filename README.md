# Architecture Design Assistant

A Streamlit application that helps design architecture solutions using AI agents using Groq's LLM API.

## Prerequisites

### Groq API Key
1. Sign up for a Groq account at [https://console.groq.com](https://console.groq.com)
2. Navigate to API Keys section
3. Generate a new API key
4. Copy your API key (starts with `gsk_`)

## Installation

### Windows
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Create .env file
echo GROQ_API_KEY=your_api_key_here > .env
```

### Linux
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env
```

You can either:
1. Set up the `.env` file with your API key
2. Or enter the API key directly in the application interface
3. The application will prioritize any API key entered in the interface over the `.env` file

## Running the Application

### Windows
```bash
streamlit run main.py
```

### Linux
```bash
streamlit run main.py
```

## Features

- **API Key Management**:
  - Secure API key storage in `.env` file
  - Override capability through UI
  - Environment variable validation

- **Interactive Prompt Editing**:
  - Customizable agent prompts
  - Real-time prompt updates
  - Pre-configured default prompts

- **AI Agents**:
  - Multiple specialized agents for architecture design
  - Cloud architecture expert
  - OSS solutions expert
  - Lead architect for final decisions

- **Export Options**:
  - Export results in Markdown format
  - Export results in PDF format
  - Automatic timestamping of exports

- **Monitoring and Debugging**:
  - Comprehensive logging system
  - View logs in real-time through UI
  - Source code visibility
  - Requirements tracking

## Project Structure

```
project/
├── main.py
├── requirements.txt
├── .env
├── outputs/
│   ├── prompts_20240321.json
│   ├── output_20240321.md
│   └── output_20240321.pdf
└── ...
```

## Security Notes

- Never commit your `.env` file to version control
- Keep your API key secure and rotate it regularly
- The `.env` file is included in `.gitignore` by default

## Troubleshooting

1. If you get an API key error:
   - Check if your `.env` file exists
   - Verify the API key format (should start with `gsk_`)
   - Try entering the key directly in the UI

2. If the application fails to start:
   - Verify all requirements are installed
   - Check the logs tab for detailed error messages
   - Ensure Python environment is activated

## License

This project is free software.

## Contributing

Feel free to submit issues and enhancement requests.

## Configuration

### Environment Variables
The application uses a `.env` file for configuration. Create a `.env` file in the project root with the following variables: