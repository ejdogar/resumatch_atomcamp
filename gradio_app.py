import gradio as gr
import requests
import os

# FASTAPI_URL = "https://resumatchlanggraph-production.up.railway.app:8080"
FASTAPI_URL = "http://0.0.0.0:8000"

def create_download_button(file_path: str, label: str) -> gr.HTML:
    if not file_path:
        return gr.HTML(f"""
        <div style='
            display: inline-block;
            padding: 12px 24px;
            background: #e0e0e0;
            color: #666;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 16px;
            margin: 5px 0;
        '>
        ⬇️ {label} (Not generated yet)
        </div>
        """)
    
    filename = os.path.basename(file_path)
    return gr.HTML(f"""
    <a href='{FASTAPI_URL}/download/{file_path}'
       download='{filename}'
       style='
           display: inline-block;
           padding: 12px 24px;
           background: #4CAF50;
           color: white;
           text-decoration: none;
           border-radius: 6px;
           font-weight: bold;
           font-size: 16px;
           margin: 5px 0;
       '>
       ⬇️ Download {label}
    </a>
    """)

def process_files(resume_file, job_desc_file, job_title):
    try:
        files = {
            "resume_file": open(resume_file.name, "rb"),
            "job_desc_file": open(job_desc_file.name, "rb")
        }
        
        response = requests.post(
            f"{FASTAPI_URL}/process_resume/",
            files=files,
            data={"job_title": job_title}
        )
        response.raise_for_status()
        
        result = response.json()
        outputs = result["outputs"]
        
        return [
            create_download_button(outputs.get("cover_letter"), "Cover Letter"),
            create_download_button(outputs.get("pitch"), "60-Second Pitch"),
            create_download_button(outputs.get("resume_edits"), "Optimized Resume"),
            result["analysis"]["resume_summary"],
            result["analysis"]["job_match"],
            "✅ Processing complete"
        ]
    except Exception as e:
        return [
            gr.HTML(f"""
            <div style='
                display: inline-block;
                padding: 12px 24px;
                background: #ffebee;
                color: #c62828;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 5px 0;
            '>
            ❌ Failed to generate
            </div>
            """),
            gr.HTML(f"""
            <div style='
                display: inline-block;
                padding: 12px 24px;
                background: #ffebee;
                color: #c62828;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 5px 0;
            '>
            ❌ Failed to generate
            </div>
            """),
            gr.HTML(f"""
            <div style='
                display: inline-block;
                padding: 12px 24px;
                background: #ffebee;
                color: #c62828;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 5px 0;
            '>
            ❌ Failed to generate
            </div>
            """),
            None,
            None,
            f"❌ Error: {str(e)}"
        ]

custom_css = """
.accordion-textbox textarea {
    min-height: 200px !important;
    max-height: 200px !important;
}
"""

with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# resuMatch")
    gr.Markdown("### 🎯 AI Agentic Workflow Powered Resume, Cover Letter & Pitch Generator")
    
    with gr.Row():
        with gr.Column():
            resume_upload = gr.File(label="Upload Resume", type="filepath")
            job_desc_upload = gr.File(label="Upload Job Description", type="filepath")
            job_title = gr.Textbox(label="Job Title", placeholder="Job title comes here...")
            submit_btn = gr.Button("Generate", variant="primary")
            
        with gr.Column():
            # Download buttons (always visible)
            gr.Markdown("### Download Generated Files")
            cover_letter_dl = create_download_button(None, "Cover Letter")
            pitch_dl = create_download_button(None, "60-Second Pitch")
            resume_edits_dl = create_download_button(None, "Optimized Resume")
            
            # Analysis sections
            with gr.Accordion("Resume Summary", open=False):
                resume_summary = gr.Textbox(show_label=False, elem_classes="accordion-textbox")
            
            with gr.Accordion("Job Match Analysis", open=False):
                job_match = gr.Textbox(show_label=False, elem_classes="accordion-textbox")
            
            status = gr.Textbox(label="Status", interactive=False)

    submit_btn.click(
        fn=process_files,
        inputs=[resume_upload, job_desc_upload, job_title],
        outputs=[cover_letter_dl, pitch_dl, resume_edits_dl, resume_summary, job_match, status]
    )

if __name__ == "__main__":
    demo.launch(share=True, debug=True)



    #AI Agentic Workflow Powered Resume & Cover Letter Generator