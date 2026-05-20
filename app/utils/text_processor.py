import re
from semantic_text_splitter import TextSplitter
from tokenizers import Tokenizer
from app.config import Config


class TextProcessor:
    """Text processing and splitting utilities"""
    
    def __init__(self):
        self.max_tokens = Config.MAX_TOKENS
        self.tokenizer = Tokenizer.from_pretrained(Config.TOKENIZER_MODEL)
        self.splitter = TextSplitter.from_huggingface_tokenizer(self.tokenizer, self.max_tokens)
    
    def split_text(self, text):
        """Split text into chunks"""
        return self.splitter.chunks(text)
    
    @staticmethod
    def clean_text(text):
        """
        Membersihkan teks dari karakter aneh, simbol, dan format yang tidak perlu.
        Mempertahankan huruf, angka, tanda baca dasar, dan simbol matematika.
        
        Args:
            text: Raw text yang perlu dibersihkan
        
        Returns:
            Cleaned text (huruf, angka, spasi, tanda baca, dan simbol matematika)
        """
        if not text:
            return ""
        
        # 1. Pertahankan: huruf, angka, spasi, tanda baca (.,;:!?-), kurung, dan simbol matematika (+/×÷=%<>)
        cleaned = re.sub(r'[^\w\s\.,;:!?\-\(\)\+/×÷=%<>]', ' ', text)
        
        # 2. Hapus underscore (termasuk dalam \w tapi tidak diinginkan)
        cleaned = re.sub(r'_', ' ', cleaned)
        
        # 3. Ganti multiple newlines/tabs dengan single space
        cleaned = re.sub(r'[\n\t\r]+', ' ', cleaned)
        
        # 4. Ganti multiple spaces dengan single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 5. Hapus spaces sebelum tanda baca
        cleaned = re.sub(r'\s+([.,;:!?\)])', r'\1', cleaned)
        
        # 6. Hapus spaces setelah kurung buka
        cleaned = re.sub(r'\(\s+', r'(', cleaned)
        
        # 7. Tambahkan space setelah tanda baca jika tidak ada
        cleaned = re.sub(r'([.,;:!?\)])([^\s])', r'\1 \2', cleaned)
        
        # 8. Hapus angka yang berdiri sendiri dengan banyak digit (kemungkinan noise/ID)
        cleaned = re.sub(r'\b\d{5,}\b', '', cleaned)
        
        # 9. Hapus karakter berulang abnormal (misalnya: aaaaaaa, -----)
        cleaned = re.sub(r'(.)\1{4,}', '', cleaned)
        
        # 10. Bersihkan spaces berlebih lagi setelah semua replacement
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 11. Capitalize first letter of sentences
        sentences = cleaned.split('. ')
        sentences = [s.strip().capitalize() if s.strip() else s for s in sentences]
        cleaned = '. '.join(sentences)
        
        # 12. Trim dan return
        return cleaned.strip()


# Singleton instance
text_processor = TextProcessor()
