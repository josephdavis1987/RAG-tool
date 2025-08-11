import PyPDF2
from typing import List, Dict
import streamlit as st

class PDFLoader:
    def __init__(self):
        pass
    
    def load_pdf(self, pdf_file) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
            
            return text
        
        except Exception as e:
            st.error(f"Error loading PDF: {str(e)}")
            return ""
    
    def get_document_info(self, pdf_file) -> Dict:
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return {
                "num_pages": len(pdf_reader.pages),
                "metadata": pdf_reader.metadata if pdf_reader.metadata else {}
            }
        except Exception as e:
            return {"error": str(e)}