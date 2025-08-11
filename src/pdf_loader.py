"""
PDF Document Loader Module

This module provides functionality for extracting text and metadata from PDF documents.
It's specifically optimized for government documents and legislative texts that can be
50-200+ pages long.

The PDFLoader class handles:
- Text extraction with page boundary preservation
- Metadata extraction for document information
- Error handling for corrupted or protected PDFs
- Page-by-page processing for memory efficiency

Typical usage:
    loader = PDFLoader()
    with open('document.pdf', 'rb') as f:
        text = loader.load_pdf(f)
        info = loader.get_document_info(f)
"""

import PyPDF2
from typing import List, Dict
import streamlit as st

class PDFLoader:
    """
    Handles PDF document loading and text extraction.
    
    This class provides methods to extract text content and metadata from PDF files,
    with special handling for large government documents and legislative texts.
    """
    
    def __init__(self):
        """Initialize the PDFLoader with default settings."""
        pass
    
    def load_pdf(self, pdf_file) -> str:
        """
        Extract text content from a PDF file.
        
        Processes the PDF page by page, preserving page boundaries with markers
        for easier reference when citations are needed.
        
        Args:
            pdf_file: File-like object containing the PDF data (opened in 'rb' mode)
        
        Returns:
            str: Extracted text with page markers, or empty string on failure
        
        Note:
            - Page markers are inserted as "--- Page X ---" between pages
            - Handles encrypted PDFs gracefully by returning empty string
            - Preserves original formatting as much as PyPDF2 allows
        """
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
        """
        Extract metadata and document information from a PDF file.
        
        Retrieves document properties such as page count, title, author,
        creation date, and other embedded metadata.
        
        Args:
            pdf_file: File-like object containing the PDF data (opened in 'rb' mode)
        
        Returns:
            Dict containing:
                - num_pages (int): Total number of pages in the document
                - metadata (dict): PDF metadata (title, author, subject, etc.)
                - error (str): Error message if extraction fails
        
        Example:
            >>> info = loader.get_document_info(pdf_file)
            >>> print(f"Document has {info['num_pages']} pages")
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return {
                "num_pages": len(pdf_reader.pages),
                "metadata": pdf_reader.metadata if pdf_reader.metadata else {}
            }
        except Exception as e:
            return {"error": str(e)}