from app.config import Config
from app.utils.text_processor import TextProcessor
from app.models import Annotation


class AnnotationHelper:
    """Helper for creating annotations from chunks"""
    
    @staticmethod
    def create_annotations_from_chunks(chunks, max_chars_per_page=None):
        """
        Menggabungkan chunks menjadi pages dengan maksimal karakter per halaman.
        Text akan dibersihkan terlebih dahulu sebelum disimpan.
        
        Args:
            chunks: List of text chunks
            max_chars_per_page: Maksimal karakter per halaman
        
        Returns:
            List of Annotation objects
        """
        if max_chars_per_page is None:
            max_chars_per_page = Config.MAX_CHARS_PER_PAGE
        
        annotations = []
        current_page = 1
        current_text = ""
        
        for chunk in chunks:
            # Clean chunk first
            cleaned_chunk = TextProcessor.clean_text(chunk)
            
            # Skip empty chunks
            if not cleaned_chunk or len(cleaned_chunk) < 10:
                continue
            
            # Split long chunks into multiple pages
            remaining_chunk = cleaned_chunk
            
            while remaining_chunk:
                # Calculate space left in current page
                space_left = max_chars_per_page - len(current_text)
                
                if space_left <= 0:
                    # Page is full, save and create new page
                    if current_text.strip():
                        annotations.append(Annotation(current_page, current_text.strip()))
                        current_page += 1
                        current_text = ""
                    space_left = max_chars_per_page
                
                # Take as much text as fits in current page
                if len(remaining_chunk) <= space_left:
                    # All remaining chunk fits
                    current_text += remaining_chunk
                    remaining_chunk = ""
                else:
                    # Cut at nearest space to avoid breaking words
                    cut_point = remaining_chunk.rfind(' ', 0, space_left)
                    if cut_point == -1:
                        # No space found, force cut
                        cut_point = space_left
                    
                    current_text += remaining_chunk[:cut_point]
                    remaining_chunk = remaining_chunk[cut_point:].lstrip()
                    
                    # Save full page
                    if len(current_text) >= max_chars_per_page - 10:
                        annotations.append(Annotation(current_page, current_text.strip()))
                        current_page += 1
                        current_text = ""
        
        # Save last page if there's remaining text
        if current_text.strip():
            annotations.append(Annotation(current_page, current_text.strip()))
        
        return annotations


# Singleton instance
annotation_helper = AnnotationHelper()
