import logging
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from typing import Optional
import anthropic
import json
from datetime import datetime
import os
import typst
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")
# --- Logging setup ---
# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your Anthropic API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY is None:
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# --- Global variables to store file paths ---
ORIGINAL_RESUME_PATH = "app/original_resume.txt"
TEMPLATE_PATH = "app/resume_template.typ"
PROMPTS_PATH = "app/prompt.txt"

# --- Function to read file content ---
def get_file_content(file_path):
    logger.info(f"Reading file content from {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file {file_path}")
    
@app.post("/tailor_resume/")
async def tailor_resume(
    role: str = Form(...),
    job_description_text: str = Form(...)
):
    logger.info(f"API called: /tailor_resume with role={role}")
    logger.info(f"Request body: role={role}, job_description_text={job_description_text}")

    # --- Get the pre-uploaded resume content ---
    try:
        resume_text = get_file_content("app/original_resume.txt")
        logger.info("Successfully read original resume content.")
    except Exception as e:
        logger.error(f"Error fetching original resume content: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch original resume content.")

    # Load prompt template
    prompt_template = get_file_content("app/prompt.txt")

    # Format the prompt
    prompt = prompt_template.format(
        original_resume=resume_text,
        job_description=job_description_text
    )
    # Call the resume tailoring function
    tailored_content = generate_tailored_content(prompt)

    if "error" in tailored_content:
        logger.error(f"Error in tailored content generation: {tailored_content['error']}")
        return tailored_content

    # --- Load the template ---
    template = get_file_content("app/resume_template.typ")

    # --- Replace placeholders in the template ---
    template = template.replace("[PROFILE_SUMMARY]", tailored_content['profile_summary'])
    template = template.replace("[SUMMARY_POINT_1]", tailored_content['key_achievements'][0])
    template = template.replace("[SUMMARY_POINT_2]", tailored_content['key_achievements'][1])
    template = template.replace("[SUMMARY_POINT_3]", tailored_content['key_achievements'][2])

    # Replace skill placeholders (assuming you have up to 12 skills)
    for i in range(12):
        skill_key = f"SKILL_{i+1}"
        if f"[{skill_key}]" in template:
            try:
                template = template.replace(f"[{skill_key}]", tailored_content['areas_of_expertise'][i])
            except IndexError:
                # Handle cases where Claude might return fewer than 12 skills
                template = template.replace(f"[{skill_key}]", "") 

    current_date = datetime.now().strftime("%Y-%m-%d")
    generated_resume_filename = f"Peerapat Chiaprasert Resume-{current_date}-{role}.typ"
    generated_resume_pdf_filename = f"Peerapat Chiaprasert Resume-{current_date}-{role}.pdf"

    # --- Save the populated template as a .typ file ---
    try:
        with open(generated_resume_filename, "w", encoding="utf-8") as file:
            file.write(template)
        logger.info(f"Generated .typ file: {generated_resume_filename}")
    except Exception as e:
        logger.error(f"Error saving Typst file: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving Typst file: {e}")

    # --- Compile to PDF using typst ---
    try:
        typst.compile(
            generated_resume_filename,
            font_paths=["app/fonts"],
            output=generated_resume_pdf_filename
        )
        logger.info(f"Successfully compiled PDF: {generated_resume_pdf_filename}")
    except Exception as e:
        logger.error(f"Error compiling Typst file: {e}")
        return {"error": f"Error compiling Typst file: {e}"}

    # Return download link
    logger.info(f"Returning download link for: {generated_resume_pdf_filename}")
    return {"download_link": f"/download_resume/{generated_resume_pdf_filename}"} 

@app.get("/download_resume/{filename}")
async def download_resume(filename: str):
    logger.info(f"API called: /download_resume with filename={filename}")

    file_path = os.path.join(os.getcwd(), filename)  # Construct the full file path
    if os.path.exists(file_path):
        logger.info(f"File found: {filename}")
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    else:
        logger.error(f"File not found: {filename}")
        return {"error": "File not found"}

def generate_tailored_content(prompt: str) -> dict:
    """
    Generates tailored resume content using Claude API.

    Args:
        prompt (str): The formatted prompt string for the Claude API.

    Returns:
        dict: A dictionary containing tailored resume sections.
    """
    logger.info(f"Generating tailored content with the prompt: {prompt[:100]}...")

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            temperature=0.3,
            messages=[
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        )

        tailored_content = json.loads(message.content[0].text)
        logger.info("Successfully generated tailored content.")
        return tailored_content
    except Exception as e:
        logger.error(f"Error generating tailored content: {e}")
        return {"error": f"Error generating tailored content: {e}"}