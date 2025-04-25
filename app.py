from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import os
from pipeline.graph import build_graph
from utils.utils import export_pdf
from langchain_core.messages import AIMessage
import tempfile
import gradio as gr
import uvicorn
import requests

app = FastAPI()

# I am using this function to extract content from the AIMessage
def extract_content(message):
    if isinstance(message, AIMessage):
        return message.content
    return str(message)

@app.post("/api/process_resume/")
async def process_resume(
    resume_file: UploadFile = File(...),
    job_desc_file: UploadFile = File(...),
    job_title: str = Form(...)
) -> Dict[str, Any]:
    try:
        resume = (await resume_file.read()).decode("utf-8")
        job_desc = (await job_desc_file.read()).decode("utf-8")

        graph = build_graph()
        result = graph.invoke({
            "resume": resume,
            "job_description": job_desc,
            "job_title": job_title
        })

        processed_result = {key: extract_content(value) for key, value in result.items()}

        temp_dir = tempfile.mkdtemp()
        
        outputs = {}
        outputs["cover_letter"] = export_pdf(processed_result["cover_letter"], os.path.join(temp_dir, "cover_letter.pdf"))
        outputs["pitch"] = export_pdf(processed_result["pitch"], os.path.join(temp_dir, "pitch.pdf"))
        outputs["resume_edits"] = export_pdf(processed_result["resume_edits"], os.path.join(temp_dir, "resume_edits.pdf"))
        
        return {
            "message": "Processing complete",
            "outputs": outputs,
            "analysis": {
                "resume_summary": processed_result["resume_summary"],
                "job_match": processed_result["job_match"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=os.path.basename(file_path))

# Gradio UI functions
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
    <a href='/api/download/{file_path}'
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
            "resume_file": (os.path.basename(resume_file.name), open(resume_file.name, "rb")),
            "job_desc_file": (os.path.basename(job_desc_file.name), open(job_desc_file.name, "rb"))
        }
        
        response = requests.post(
            "http://localhost:8000/api/process_resume/",
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

with gr.Blocks(css=custom_css, title="resuMatch") as demo:
    gr.Markdown("# resuMatch")
    gr.Markdown("### 🎯 AI Agentic Workflow Powered Resume, Cover Letter & Pitch Generator")
    
    with gr.Row():
        with gr.Column():
            resume_upload = gr.File(label="Upload Resume", type="filepath")
            job_desc_upload = gr.File(label="Upload Job Description", type="filepath")
            job_title = gr.Textbox(label="Job Title", placeholder="Job title comes here...")
            submit_btn = gr.Button("Generate", variant="primary")
            
        with gr.Column():
            # these are my file download buttons
            gr.Markdown("### Download Generated Files")
            cover_letter_dl = create_download_button(None, "Cover Letter")
            pitch_dl = create_download_button(None, "60-Second Pitch")
            resume_edits_dl = create_download_button(None, "Optimized Resume")
            
            # displaying summary analysis
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

# here i am moutning gradio at the root path
app = gr.mount_gradio_app(app, demo, path="/")

# Redirect root to Gradio interface
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)