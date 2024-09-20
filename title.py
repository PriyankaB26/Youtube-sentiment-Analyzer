from flask import Flask, request, render_template
from transformers import T5ForConditionalGeneration, T5Tokenizer
from datasets import load_dataset
import language_tool_python

# Initialize Flask app
app = Flask(__name__)

# Load pre-trained model and tokenizer
model_name = "t5-base"  # You can switch to "t5-large" if needed for better results
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Load your fine-tuning dataset
dataset = load_dataset("AdamLucek/youtube-titles")  # Ensure this dataset is accessible

# Initialize LanguageTool for grammar checking
tool = language_tool_python.LanguageTool('en-US')

# Function to generate title
def generate_title(description):
    try:
        # Directly use the description as input
        input_text = description
        print(f"Input text: {input_text}")  # Debugging line to check input text

        # Tokenize input
        inputs = tokenizer(input_text, return_tensors="pt", max_length=128, truncation=True)

        # Generate the title with adjusted parameters
        output = model.generate(
            **inputs,
            max_length=50,
            top_p=0.9,
            top_k=50,
            temperature=0.7,
            num_return_sequences=1
        )

        # Decode the generated output into a readable title
        title = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"Generated title: {title}")  # Debugging line to check output title
        return title
    except Exception as e:
        print(f"Error: {e}")
        return f"Error in generating title: {str(e)}"

# Function to check grammar
def check_grammar(title):
    try:
        matches = tool.check(title)
        corrected_title = language_tool_python.utils.correct(title, matches)
        return corrected_title
    except Exception as e:
        return f"Error in grammar check: {str(e)}"

# Route to render form and process input
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        description = request.form.get("description")

        # Check if description is provided
        if not description or description.strip() == "":
            return render_template("title.html", error="Please provide a valid description.")

        # Generate the title
        generated_title = generate_title(description)

        # If an error occurred during title generation, show it
        if "Error" in generated_title:
            return render_template("title.html", error=generated_title)

        # Optionally apply grammar check
        apply_grammar_check = request.form.get("apply_grammar", "no")  # Checkbox value
        if apply_grammar_check == "yes":
            corrected_title = check_grammar(generated_title)
        else:
            corrected_title = generated_title

        return render_template("title.html", title=corrected_title)

    return render_template("title.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
