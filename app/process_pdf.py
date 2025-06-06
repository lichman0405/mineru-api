# The module for processing PDF files, analyzing them, and generating output files.
# Author: Shibo Li
# Date: 2025-06-06
# Version: 0.1.0

# app/process_pdf.py (更新后)

import os
import logging
from rich.console import Console
from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

logger = logging.getLogger(__name__)

def analyze_pdf(pdf_path: str, output_dir: str) -> dict: 
    """
    Analyzes a given PDF file and saves all outputs to a dedicated directory.
    Args:
        pdf_path (str): The path to the PDF file to be analyzed.
        output_dir (str): The directory where all output files will be saved.
    Returns:
        dict: A summary of the analysis results, including paths to generated files.
    Raises:
    """
    logger.info(f"Analysis started. All outputs will be saved to: {output_dir}")

    # All paths are now relative to the unique output_dir
    name_without_ext = os.path.splitext(os.path.basename(pdf_path))[0]
    local_image_dir = os.path.join(output_dir, "images")
    os.makedirs(local_image_dir, exist_ok=True)
    image_dir_relative_path = "images"

    # We only need one writer for images and one for everything else in the same directory
    image_writer = FileBasedDataWriter(local_image_dir)
    result_writer = FileBasedDataWriter(output_dir)
    
    # The reader is stateless and doesn't need to change
    from magic_pdf.data.data_reader_writer import FileBasedDataReader
    reader = FileBasedDataReader("")
    logger.info("✓ Environment prepared.")

    try:
        pdf_bytes = reader.read(pdf_path)
        ds = PymuDocDataset(pdf_bytes)
        logger.info("✓ PDF file read and loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to read or load PDF file: {e}", exc_info=True)
        raise

    console = Console()
    with console.status("[bold yellow]Running AI model analysis...", spinner="dots") as status:
        is_ocr = ds.classify() == SupportedPdfParseMethod.OCR
        # ... (The rest of the analysis logic remains the same) ...
        if is_ocr:
            status.update("[yellow]Scanned document detected, starting OCR mode analysis...")
            logger.info("Analysis Mode: OCR")
            infer_result = ds.apply(doc_analyze, ocr=True)
            status.update("[yellow]OCR analysis finished, building document structure...")
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            status.update("[yellow]Native PDF detected, starting text mode analysis...")
            logger.info("Analysis Mode: Text")
            infer_result = ds.apply(doc_analyze, ocr=False)
            status.update("[yellow]Text analysis finished, building document structure...")
            pipe_result = infer_result.pipe_txt_mode(image_writer)

    logger.info("✓ AI model analysis complete.")
    logger.info("Generating and saving output files...")
    
    try:
        # All output files are now written to the same 'output_dir'
        model_pdf_path = os.path.join(output_dir, f"{name_without_ext}_model.pdf")
        infer_result.draw_model(model_pdf_path)
        logger.info(f"Generated model visual report -> {model_pdf_path}")

        layout_pdf_path = os.path.join(output_dir, f"{name_without_ext}_layout.pdf")
        pipe_result.draw_layout(layout_pdf_path)
        logger.info(f"Generated layout visual report -> {layout_pdf_path}")

        span_pdf_path = os.path.join(output_dir, f"{name_without_ext}_spans.pdf")
        pipe_result.draw_span(span_pdf_path)
        logger.info(f"Generated spans visual report -> {span_pdf_path}")

        md_path = f"{name_without_ext}.md"
        pipe_result.dump_md(result_writer, md_path, image_dir_relative_path)
        logger.info(f"Generated Markdown file -> {os.path.join(output_dir, md_path)}")

        content_list_json_path = f"{name_without_ext}_content_list.json"
        pipe_result.dump_content_list(result_writer, content_list_json_path, image_dir_relative_path)
        logger.info(f"Generated content list JSON -> {os.path.join(output_dir, content_list_json_path)}")

        middle_json_path = f'{name_without_ext}_middle.json'
        pipe_result.dump_middle_json(result_writer, middle_json_path)
        logger.info(f"Generated middle structure JSON -> {os.path.join(output_dir, middle_json_path)}")
    except Exception as e:
        logger.error("An error occurred while generating output files.", exc_info=True)
        raise

    logger.info("[bold green]✓ All output files generated successfully.[/bold green]")
    
    # Update the result summary to reflect the new structure
    result_summary = {
        "status": "success",
        "input_file": pdf_path,
        "analysis_mode": "OCR" if is_ocr else "Text",
        "output_directory": output_dir, # A single output directory
        "generated_files": {
            "markdown": os.path.join(output_dir, md_path),
            "content_list_json": os.path.join(output_dir, content_list_json_path),
            "middle_json": os.path.join(output_dir, middle_json_path),
            "visual_reports": [model_pdf_path, layout_pdf_path, span_pdf_path],
            "image_dir": local_image_dir
        }
    }
    return result_summary