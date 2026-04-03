import streamlit as st
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download nltk resources
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger_eng")

# Page setup
st.set_page_config(page_title="Resume Job Match Scorer", page_icon="📄", layout="wide")
st.title("🎯 Resume Job Match Scorer")

with st.sidebar:
    st.header("📋 Menu")
    st.subheader("Upload Files")
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "txt"])
    st.divider()
    st.subheader("📋 Job Description")
    job_input_method = st.radio(
        "Choose input method:",
        ["📁 Upload File", "📝 Paste Text"],
        horizontal=True
    )
    job_file = None
    job_pasted_text = None
    if job_input_method == "📁 Upload File":
        job_file = st.file_uploader("Upload Job Description", type=["pdf", "txt"])
    else:
        job_pasted_text = st.text_area(
            "Paste Job Description here:",
            placeholder="Copy job description from LinkedIn and paste here...",
            height=250
        )
    analyze_btn = st.button("🔍 Analyze Match", use_container_width=True)
    st.divider()
    with st.expander("ℹ️ About this App"):
        st.write("""
        This tool will help you measure:
        - ✅ Match score between your resume and job description
        - 🔍 Missing keywords
        - 📊 Skill gaps
        - 💡 Tips to improve your resume
        """)

# ── Helper Functions ──────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    else:
        return uploaded_file.read().decode("utf-8")

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    return " ".join([word for word in words if word not in stop_words])

def calculate_similarity(resume_text, job_description):
    resume_processed = remove_stopwords(clean_text(resume_text))
    job_processed = remove_stopwords(clean_text(job_description))
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_processed, job_processed])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
    return round(score, 2), resume_processed, job_processed

def get_missing_keywords(resume_processed, job_processed):
    resume_words = set(resume_processed.split())
    job_words = set(job_processed.split())
    missing = sorted(job_words - resume_words)  # sorted for consistent ordering
    return missing[:20]

def get_common_keywords(resume_processed, job_processed):
    resume_words = set(resume_processed.split())
    job_words = set(job_processed.split())
    return sorted(resume_words & job_words)  # sorted for consistent ordering

# ── Main App ──────────────────────────────────────────────────────

def main():
    job_text = None
    if job_input_method == "📁 Upload File":
        if job_file:
            job_text = extract_text(job_file)
    else:
        if job_pasted_text and job_pasted_text.strip():
            job_text = job_pasted_text

    if resume_file and job_text:
        resume_text = extract_text(resume_file)
        if analyze_btn:
            if not resume_text:
                st.error("Could not extract text from resume. Please try another file.")
                return
            if not job_text:
                st.error("Could not extract job description. Please upload or paste it.")
                return

            with st.spinner("Analyzing your resume..."):
                score, resume_processed, job_processed = calculate_similarity(resume_text, job_text)
                missing_keywords = get_missing_keywords(resume_processed, job_processed)
                common_keywords = get_common_keywords(resume_processed, job_processed)

            st.subheader("📊 Match Score")
            st.metric(label="Your Resume Match", value=f"{score}%")

            if score < 40:
                color = "red"
                st.error("❌ Low match! Consider tailoring your resume.")
            elif score < 70:
                color = "orange"
                st.warning("⚠️ Moderate match! Add more relevant keywords.")
            else:
                color = "green"
                st.success("✅ Great match! Your resume aligns well.")

            fig, ax = plt.subplots(figsize=(6, 1))
            ax.barh(["Match"], [score], color=color)
            ax.set_xlim([0, 100])
            ax.set_xlabel("Match Percentage")
            ax.set_title("Resume Match Score")
            st.pyplot(fig)
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔍 Missing Keywords")
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.success("No major keywords missing!")
            with col2:
                st.subheader("✅ Matching Keywords")
                if common_keywords:
                    st.write(", ".join(common_keywords[:20]))
                else:
                    st.warning("No common keywords found.")

            st.divider()
            with st.expander("📄 View Extracted Resume Text"):
                st.write(resume_text)
            with st.expander("📄 View Extracted Job Description Text"):
                st.write(job_text)

    else:
        if not resume_file:
            st.info("👈 Please upload your Resume from the sidebar.")
        elif not job_text:
            if job_input_method == "📁 Upload File":
                st.info("👈 Please upload a Job Description from the sidebar.")
            else:
                st.info("👈 Please paste a Job Description in the sidebar.")


if __name__ == "__main__":
    main()