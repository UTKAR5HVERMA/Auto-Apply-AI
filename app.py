import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import streamlit as st
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
import PyPDF2

# Load environment variables
load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Initialize LLM
llm = OllamaLLM(model="gemma:2b")

# Function to extract text from a PDF file object
def extract_resume_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

# Extract Resume Information
def extract_resume_info(resume_text):
    prompt = f"""
Extract the following information from this resume:

1. Full Name
2. Email
3. Education (degrees, colleges, years)
4. Work Experience (roles, companies, durations)
5. Skills
6. Projects
7. Certifications (if any)

Resume:
{resume_text}

Respond in JSON format.
"""
    return llm.invoke(prompt)

# Extract Job Description Information
def extract_job_info(job_description):
    prompt = f"""
Extract key job details from the following job description:

1. Position title
2. Required skills
3. Desired experience
4. Responsibilities
5. Keywords to include in resume/email

Job Description:
{job_description}

Respond in JSON format.
"""
    return llm.invoke(prompt)

# Generate a customized email based on resume and job description
def generate_matched_email(resume_info, job_info):
    prompt = f"""
Write a job application email based on the applicant’s resume and the job description.

Resume Info: {resume_info}

Job Info: {job_info}

Keep it under 200 words. Use a professional, personalized tone. Mention key matching skills. Close politely.
Sign off using the applicant's name.
"""
    return llm.invoke(prompt)

# Send the email with the resume attached
def send_email(to_email, subject, body, resume_file):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg.set_content(body)

    # Attach resume
    resume_bytes = resume_file.read()
    msg.add_attachment(resume_bytes, maintype='application', subtype='pdf', filename=resume_file.name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# --- Streamlit UI ---
st.title("📧 AI-Powered Job Application Agent")

uploaded_resume = st.file_uploader("Upload your Resume (PDF)", type="pdf")
job_description = st.text_area("Enter Job Description", height=200)
recipient_email = st.text_input("Recipient Email")
company = st.text_input("Company Name")
role = st.text_input("Job Role")

if uploaded_resume and job_description and recipient_email and company and role:
    if st.button("Send Email"):
        with st.spinner("Generating and sending email..."):
            try:
                # Extract text and parse
                resume_text = extract_resume_text(uploaded_resume)
                resume_info = extract_resume_info(resume_text)
                job_info = extract_job_info(job_description)
                email_body = generate_matched_email(resume_info, job_info)
                subject = f"Application for {role} at {company}"

                # Reset file pointer before sending
                uploaded_resume.seek(0)
                send_email(recipient_email, subject, email_body, uploaded_resume)

                st.success("Email sent successfully!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
else:
    st.warning("Please upload your resume, enter job description, and fill all fields.")
