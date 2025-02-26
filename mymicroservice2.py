from flask import Flask, request, jsonify
import google.generativeai as genai
from pymongo import MongoClient
import os

# Initialize Flask app
app = Flask(__name__)

# Configure the Generative AI API key
genai.configure(api_key="AIzaSyBjKe4Wk6CUtT0oSG1pUaq4Sn0ER90JpGY")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Connect to MongoDB
# Assuming MongoDB is running locally and no password is needed. Adjust the URI if necessary.
mongo_uri =  'mongodb://localhost:27017/'
client = MongoClient(mongo_uri)

# Access the database and collection
db = client['summarydb']  # Database name
collection = db['summaries']  # Collection name

def fetch_prompt():
    db = client['summarydb']  # Replace with your database name
    collection = db['promptTemplates']  # Replace with your collection name

    # Fetch the document with a specific template_key
    result = collection.find_one({"template_key": "Summary_generation_prompt"}, {"template_content.prompt_template": 1})

    # Check if the result is found and print the prompt_template
    if result and 'template_content' in result:
        prompt_template = result['template_content'].get('prompt_template', 'No prompt_template found')
        # print(f'Prompt Template: {prompt_template}')
    else:
        print('Document not found or prompt_template not available.')
    return prompt_template

# Function to generate a summary using the AI model with a dynamic prompt
def generate_summary(content, prompt_template):
    # Format the provided prompt with the content
    prompt_text = f"{content},{prompt_template}"
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

# Flask route for generating a summary and storing it in MongoDB
@app.route('/generate-summary', methods=['POST'])
def summarize():
    # Get the content and prompt from the request body
    data = request.get_json()
    content = content_file()
    # print(f"my content is : {content}")
    # prompt_template = data.get('prompt', '')
    flag = data.get('set_flag', True)
    prompt_template = fetch_prompt()

    # Validate input
    if not content or not prompt_template:
        return jsonify({"error": "Both content and prompt must be provided"}), 400
    
    # Generate a summary using the AI model
    try:
        summary = generate_summary(content, prompt_template)

        # Store the summary in MongoDB
        summary_data = {
            'content': content,
            'prompt': prompt_template,
            'summary': summary
        }
        collection.insert_one(summary_data)  # Insert into MongoDB

        return jsonify({"summary": summary, "message": "Summary saved to database", "generated_data": flag}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check route to verify the service is running
@app.route('/')
def home():
    return "AI Summary Generation Service is running!", 200

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
