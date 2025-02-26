from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import json

# Initialize Flask app
app = Flask(__name__)

# Configure the Generative AI API key
genai.configure(api_key="")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Function to generate a summary using the AI model with a dynamic prompt
def generate_summary(content, prompt_template):
    # Format the provided prompt with the content
    prompt_text = prompt_template.format(content=content)
    
    # Call the model to generate the summary
    response = model.generate_content([prompt_text])
    
    # Return the generated summary
    return response.text

def content_file():
# Set the environment variable for this session (for testing)
    os.environ['MY_FILE_PATH'] = 'D://AI_Integrated_services//content.txt'

    file_path = os.environ.get('MY_FILE_PATH')

    if file_path:
        # Do something with the file path, such as reading the file
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                # print("File Content:", content)
        except FileNotFoundError:
            print("File not found:", file_path)
    else:
        print("Environment variable 'MY_FILE_PATH' not found")
    return content


# Flask route for generating a summary
@app.route('/generate-summary', methods=['POST'])
def summarize():
    # Get the content and prompt from the request body
    data = request.json
    content = content_file()
    # print(f"the content is: {content}")
    # content = data.get('content', '')
    prompt_template = data.get('prompt', '')

    # Validate input
    if not content or not prompt_template:
        return jsonify({"error": "Both content and prompt must be provided"}), 400
    
    # Generate a summary using the AI model
    try:
        summary = generate_summary(content, prompt_template)
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check route to verify the service is running
@app.route('/')
def home():
    return "AI Summary Generation Service is running!", 200

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
