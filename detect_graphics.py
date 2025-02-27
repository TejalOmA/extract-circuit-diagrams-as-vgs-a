import fitz  # PyMuPDF

def detect_rects(page, graphics=None, delta=60, margin=36):
    """
    Logic for detecting rectangles that contain vector graphics.
      Merges overlapping rectangles for vector graphic boundary.
      Source code - pymupdf-utils/extract-vector-graphics. (Please refer).
    """
    def are_neighbors(r1, r2):
        #Finds out the overlap between two rectangles, on their x and y axes.
        return (
            (
                (r2.x0 - delta <= r1.x0 <= r2.x1 + delta or r2.x0 - delta <= r1.x1 <= r2.x1 + delta)
                and (r2.y0 - delta <= r1.y0 <= r2.y1 + delta or r2.y0 - delta <= r1.y1 <= r2.y1 + delta)
            )
            or (
                (r1.x0 - delta <= r2.x0 <= r1.x1 + delta or r1.x0 - delta <= r2.x1 <= r1.x1 + delta)
                and (r1.y0 - delta <= r2.y0 <= r1.y1 + delta or r1.y0 - delta <= r2.y1 <= r1.y1 + delta)
            )
        )

    #Adjusts the rects so that they fall inside the margins of the pdf page
    page_area = page.rect + (-margin, -margin, margin, margin)
    if graphics is None:
        #Get the vector drawings
        graphics = page.get_drawings()

    #
    filtered_graphics = [
        p for p in graphics if page_area.x0 <= p["rect"].x0 <= p["rect"].x1 <= page_area.x1 and page_area.y0 <= p["rect"].y0 <= p["rect"].y1 <= page_area.y1
    ]

    #Sorts the rects for the detected graphics in the pdf page
    rects = sorted([p["rect"] for p in filtered_graphics], key=lambda r: (r.y1, r.x0))

    merged_rects = []
    while rects:
        current_rect = rects[0]
        repeat = True
        while repeat:
            repeat = False
            for i in range(len(rects) - 1, 0, -1):
                if are_neighbors(rects[i], current_rect):
                    # Merge neighboring rectangles as union set hyper-rectangle
                    current_rect |= rects[i].tl
                    current_rect |= rects[i].br
                    del rects[i]
                    repeat = True

        rects[0] = +current_rect
        merged_rects.append(rects.pop(0))
        rects = sorted(list(set(rects)), key=lambda r: (r.y1, r.x0))

    merged_rects = sorted(list(set(merged_rects)), key=lambda r: (r.y1, r.x0))
    return [r for r in merged_rects if r.width > 3 and r.height > 3] #Adjust as needed
