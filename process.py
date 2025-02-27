import os
import json
import fitz  # PyMuPDF
from .detect_graphics import detect_rects

def process_single_pdf(pdf_path, output_dir, dpi=150, margin=36):
    """
    Process single PDF file to store vector graphic outputs,
    in PDF format, to a directory.
    """
    #Make output directory
    os.makedirs(output_dir, exist_ok=True)
    pdfs_dir = os.path.join(output_dir, "pdfs")
    os.makedirs(pdfs_dir, exist_ok=True)

    #Open pdf file
    doc = fitz.open(pdf_path)
    pdf_data = {}
    for page_number, page in enumerate(doc, start=1):
        # Detect rectangles containing vector graphics
        rects = detect_rects(page)
        
        # Extracts and removes tables and long blocks of texts
        text_blocks = page.get_text("blocks")
        tables = page.find_tables(horizontal_strategy="lines", vertical_strategy="lines")
        table_bboxes = [table.bbox for table in tables]
        text_boxes = [tuple(map(int, block[:4])) for block in text_blocks if len(block[4]) > 9]
        
        extracted_bboxes = text_boxes + table_bboxes
        # #Visualise the bounding boxes of all elements in individual pdf-pages.
        # for table in tables:
        #     page.draw_rect(table.bbox, color=(1,0,0), width=1)
        # for rect in rects:
        #     page.draw_rect(rect, color=(0,1,0), width=1)
        # for text_box in text_boxes:
        #     page.draw_rect(text_box, color=(0,0,1), width=1)
        # pix = page.get_pixmap()
        # pix.save(f"{output_dir}/pdf-page{page_number:03d}.png")


        # Removes tables and text bound boxes
        for ext_box in extracted_bboxes:
          ext_rect = fitz.Rect(ext_box)
          print(ext_rect)
          page.add_redact_annot(ext_rect, fill=(1, 1, 1))
        page.apply_redactions()

        page_data = []
        for i, rect in enumerate(rects):
            rect = rect.intersect(page.mediabox)
            new_doc = fitz.open()
            new_page = new_doc.new_page(width=rect.width, height=rect.height)
            page.set_cropbox(rect)
            new_page.show_pdf_page(page.rect, doc, pno=page_number - 1)

            cropped_pdf_path = os.path.join(pdfs_dir, f"pdf-page{page_number:03d}-rect{i:02d}.pdf")
            new_doc.save(cropped_pdf_path)
            new_doc.close()


            #Bounding rects data for metadata JSON file
            page_data.append({
                'rect': {
                    'x0': rect.x0,
                    'y0': rect.y0,
                    'x1': rect.x1,
                    'y1': rect.y1
                }
            })

        pdf_data[page_number] = page_data

    # Save JSON Metadata
    json_output_path = os.path.join(pdfs_dir, os.path.basename(pdf_path).replace('.pdf', '.json'))
    with open(json_output_path, 'w') as json_file:
        json.dump(pdf_data, json_file, indent=4)

def process_pdf_directory(input_dir, output_base_dir="output_images", dpi=150, margin=36):
    """
    Processes all PDF files in the given directory,
    It stores the vgs in a separate "pdfs" directory, inside the nested output directory,
    for each PDF file.
    """
    os.makedirs(output_base_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            relative_path = os.path.splitext(filename)[0]
            output_pdf_dir = os.path.join(output_base_dir, relative_path)

            os.makedirs(output_pdf_dir, exist_ok=True)
            os.makedirs(os.path.join(output_pdf_dir, "pdfs"), exist_ok=True)

            print(f"Processing: {filename}")
            process_single_pdf(pdf_path, output_pdf_dir, dpi, margin)
