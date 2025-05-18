#!/bin/bash

# Create .streamlit directory if it doesn't exist
mkdir -p .streamlit

# Create a default secrets.toml file if it doesn't exist
if [ ! -f .streamlit/secrets.toml ]; then
    cat > .streamlit/secrets.toml <<EOL
# OpenAI API Key
OPENAI_API_KEY = "your_openai_api_key_here"
EOL
    echo "Created .streamlit/secrets.toml with a placeholder for your OpenAI API key"
    echo "Please update it with your actual API key before deploying to Streamlit Cloud"
fi

echo "Setup complete!"
