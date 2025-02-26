from flask import Flask, request, jsonify
import google.generativeai as genai
from pymongo import MongoClient
import os
import difflib

# Initialize Flask app
app = Flask(__name__)

# Configure the Generative AI API key
genai.configure(api_key="AIzaSyBjKe4Wk6CUtT0oSG1pUaq4Sn0ER90JpGY")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Connect to MongoDB
mongo_uri = 'mongodb://localhost:27017/'
client = MongoClient(mongo_uri)

# Access the database and collection
db = client['summarydb']  # Database name
collection = db['summaries']  # Collection name


def fetch_prompt():
    # Fetch the document with a specific template_key from the database
    result = db['promptTemplates'].find_one(
        {"template_key": "Summary_generation_prompt"}, 
        {"template_content.prompt_template": 1}
    )

    # Check if the result is found and return the prompt_template
    if result and 'template_content' in result:
        prompt_template = result['template_content'].get('prompt_template', 'No prompt_template found')
    else:
        prompt_template = 'No prompt_template found'
    
    return prompt_template

def content_file():
    # Set the environment variable for the file path (for testing)
    os.environ['MY_FILE_PATH'] = 'D://AI_Integrated_services//content.txt'

    file_path = os.environ.get('MY_FILE_PATH')

    if file_path:
        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            content = None
    else:
        content = None

    return content

# Function to generate a summary using the AI model
def generate_summary(content, prompt_template):
    prompt_text = f"{content},{prompt_template}"
    response = model.generate_content([prompt_text])
    return response.text

# Function to fetch the last saved summary from MongoDB
def find_summary_in_db():
    # Search the collection for the document that contains the specific content
    summary_doc = collection.find_one({}, sort=[('_id', -1)])
    if summary_doc:
        return summary_doc.get('summary', None)  # Return the summary field if it exists
    else:
        return None 
    
# Function to compare two summaries and return the differences
def compare_summaries(generated_summary, stored_summary):
    # Use difflib to generate a list of differences
    diff = difflib.ndiff(stored_summary.split(), generated_summary.split())
    
    # Filter the differences to show only the changes
    differences = '\n'.join(diff)
    return differences



# Flask route for generating a summary
@app.route('/generate-summary', methods=['POST'])
def summarize():
    data = request.get_json()
    flag = data.get("generate_flag", False)  # Default to False if the flag is not provided

    # Read the content from the local file
    content = content_file()
    # Fetch the stored summary from the database (if it exists)
    stored_summary = find_summary_in_db()

    if not content:
        return jsonify({"error": "Content is missing!"}), 400

    if not flag:
        # If the flag is False and the summary exists in the database, return the stored summary
        if stored_summary:
            return jsonify({"summary": stored_summary, "message": "Summary fetched from database"}), 200
        else:
            return jsonify({"error": "No summary found in the database."}), 404

    # If flag is True, generate a new summary using LLM or update the existing one
    prompt_template = fetch_prompt()

    if not prompt_template:
        return jsonify({"error": "Prompt template is missing!"}), 400

    try:
        # Generate the new summary using the LLM
        generated_summary = generate_summary(content, prompt_template)

        # Upsert logic: update the summary if it exists, otherwise insert a new document
        collection.update_one(
            {"content": content},  # Query filter to find the document by content
            {
                "$set": {
                    "content": content,
                    "prompt": prompt_template,
                    "summary": generated_summary
                }
            },
            upsert=True  # Insert a new document if no existing document is found
        )
        differences = compare_summaries(generated_summary, stored_summary)
        return jsonify({
            "generated_summary": generated_summary,
            "message": "Summary generated and saved/updated in the database",
            "Differences": differences
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check route to verify the service is running
@app.route('/')
def home():
    return "AI Summary Generation Service is running!", 200

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)