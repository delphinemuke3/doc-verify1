import sys
import json
import os

def convert_pdf_to_image(pdf_path, output_dir=None, dpi=200):
    """
    Convert first page of PDF to JPG image.
    Returns dict with success status and output image path.
    """
    try:
        from pdf2image import convert_from_path

        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}",
                "image_path": None
            }

        # Output in same folder as PDF if not specified
        if output_dir is None:
            output_dir = os.path.dirname(pdf_path)

        base_name   = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, base_name + '_converted.jpg')

        # Convert first page only
        pages = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=1,
            poppler_path=r'C:\poppler-26.02.0\Library\bin'
        )

        if not pages:
            return {
                "success": False,
                "error": "PDF has no pages or could not be read",
                "image_path": None
            }

        # Save as JPG
        pages[0].save(output_path, 'JPEG', quality=95)

        return {
            "success":    True,
            "image_path": output_path,
            "pages":      len(pages),
            "message":    f"PDF converted to image: {output_path}"
        }

    except Exception as e:
        return {
            "success":    False,
            "error":      str(e),
            "image_path": None
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: pdf_convert.py <pdf_path>"
        }))
        sys.exit(1)

    result = convert_pdf_to_image(sys.argv[1])
    print(json.dumps(result))