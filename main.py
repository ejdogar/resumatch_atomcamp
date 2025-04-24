from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any
import os
from graph import build_graph
from utils import export_pdf
from langchain_core.messages import AIMessage
import tempfile
import json

app = FastAPI()

# I am using this function to extract content from the AIMessage
def extract_content(message):

    if isinstance(message, AIMessage):
        return message.content
    return str(message)

@app.post("/process_resume/{job_title}")
async def process_resume(
    job_title:str,
    resume_file: UploadFile = File(...),
    job_desc_file: UploadFile = File(...),
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

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=os.path.basename(file_path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
