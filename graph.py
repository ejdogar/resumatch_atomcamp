from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from typing import TypedDict
import os

llm = ChatOpenAI(model="gpt-4", temperature=0.3, api_key=os.environ["OPENAI_API_KEY"])

resume_analysis_prompt = ChatPromptTemplate.from_template("""analyze this resume:\n{resume}""")
job_match_prompt = ChatPromptTemplate.from_template("""match resume with job:\n{resume_summary}\n{job_description}""")
tailor_prompt = ChatPromptTemplate.from_template("""suggest resume edits:\n{resume}\n{job_match}""")
cover_letter_prompt = ChatPromptTemplate.from_template("""write a cover letter for:\n{resume_summary}\n{job_description}""")
pitch_prompt = ChatPromptTemplate.from_template("""write a 60 second pitch for:\n{resume_summary}\n{job_title}""")

class ResumeState(TypedDict):
    resume: str
    job_description: str
    job_title: str
    resume_summary: str
    job_match: str
    resume_edits: str
    cover_letter: str
    pitch: str

def build_graph():
    builder = StateGraph(state_schema=ResumeState)

    builder.add_node("analyze_resume", 
        RunnablePassthrough.assign(
            resume_summary=lambda x: (resume_analysis_prompt | llm).invoke({"resume": x["resume"]})
        )
    )

    builder.add_node("match_job", 
        RunnablePassthrough.assign(
            job_match=lambda x: (job_match_prompt | llm).invoke({
                "resume_summary": x["resume_summary"],
                "job_description": x["job_description"]
            })
        )
    )

    builder.add_node("tailor_resume", 
        RunnablePassthrough.assign(
            resume_edits=lambda x: (tailor_prompt | llm).invoke({
                "resume": x["resume"],
                "job_match": x["job_match"]
            })
        )
    )

    builder.add_node("write_cover_letter", 
        RunnablePassthrough.assign(
            cover_letter=lambda x: (cover_letter_prompt | llm).invoke({
                "resume_summary": x["resume_summary"],
                "job_description": x["job_description"]
            })
        )
    )

    builder.add_node("write_pitch", 
        RunnablePassthrough.assign(
            pitch=lambda x: (pitch_prompt | llm).invoke({
                "resume_summary": x["resume_summary"],
                "job_title": x["job_title"]
            })
        )
    )

    # this is my application's workflow
    builder.set_entry_point("analyze_resume")
    builder.add_edge("analyze_resume", "match_job")
    builder.add_edge("match_job", "tailor_resume")
    builder.add_edge("tailor_resume", "write_cover_letter")
    builder.add_edge("write_cover_letter", "write_pitch")
    builder.add_edge("write_pitch", END)

    return builder.compile()


