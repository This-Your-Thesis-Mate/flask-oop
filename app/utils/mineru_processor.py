import time
import json
import base64
import zipfile
import shutil
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from app.config import Config
from app.utils.openai_client import groq_client


class MinerUProcessor:
    """Processor for MinerU document extraction"""
    
    IMG_PROMPT = (
        "Anda adalah asisten aksesibilitas. Buat anotasi deskriptif berbahasa Indonesia untuk gambar dokumen berikut.\n"
        "- Ringkasan 1-2 kalimat isi visual.\n"
        "- Detail penting (judul, sumbu/label jika grafik, angka yang terbaca, teks signage jika ada).\n"
        "- Konteks (mis. ilustrasi/diagram/tangkapan layar).\n"
        "PENTING: Tulis menggunakan huruf, angka, spasi, tanda baca dasar (titik, koma, tanda tanya, tanda seru), dan simbol matematika (+, -, /, ×, =, %, <, >). "
        "JANGAN gunakan simbol lain seperti #, @, $, &, *, _, |, ~, ^, dll.\n"
        "Format: paragraf singkat (maks 150 kata)."
    )
    
    TABLE_PROMPT_TEMPLATE = (
        "Ubah tabel berikut menjadi deskripsi naratif berbahasa Indonesia untuk pembaca tunanetra.\n"
        "- Jelaskan tujuan tabel, kolom utama, pola penting, dan 2-3 insight ringkas.\n"
        "- Jika tabel sangat panjang, rangkum tanpa menyebutkan setiap baris.\n"
        "PENTING: Tulis menggunakan huruf, angka, spasi, tanda baca dasar (titik, koma, tanda tanya, tanda seru), dan simbol matematika (+, -, /, ×, =, %, <, >). "
        "JANGAN gunakan simbol lain seperti #, @, $, &, *, _, |, ~, ^, dll.\n"
        "Konten tabel:\n\n{table_text}\n\n"
        "Tulis ringkas (maksimal 200 kata)."
    )
    
    def __init__(self):
        self.token = Config.MINERU_TOKEN
        self.api_base = Config.MINERU_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create session with retry strategy for network reliability
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,  # Total retry attempts
            backoff_factor=2,  # Exponential backoff: 2, 4, 8, 16, 32 seconds
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Increased timeouts for large files
        self.upload_timeout = 300  # 5 minutes for upload
        self.api_timeout = 60  # 1 minute for API calls
        self.download_timeout = 600  # 10 minutes for downloads
    
    @staticmethod
    def safe_read_text(path: Path, max_chars: int = 8000) -> str:
        """Read text file safely with truncation"""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1", errors="ignore")
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Catatan: konten dipotong karena panjang.]"
        return text
    
    @staticmethod
    def img_to_data_url(img_path: Path) -> str:
        """Convert image to data URL"""
        b = img_path.read_bytes()
        b64 = base64.b64encode(b).decode("utf-8")
        ext = img_path.suffix.lower().lstrip(".") or "png"
        return f"data:image/{ext};base64,{b64}"
    
    def groq_vision_annotate(self, img_path: Path, prompt: str) -> str:
        """Generate image annotation using Groq vision"""
        try:
            data_url = self.img_to_data_url(img_path)
            return groq_client.vision_annotate(data_url, prompt)
        except Exception as e:
            return f"[ERROR image annotation] {e}"
    
    def groq_text_annotate(self, prompt: str) -> str:
        """Generate table annotation using Groq text"""
        try:
            return groq_client.text_annotate(prompt)
        except Exception as e:
            return f"[ERROR table annotation] {e}"
    
    def annotate_dir(self, work_dir: Path):
        """Generate annotations for images and tables"""
        from app.utils.text_processor import TextProcessor
        
        ann_dir = work_dir / "annotations"
        img_dir = work_dir / "images"
        tbl_dir = work_dir / "tables"
        ann_dir.mkdir(exist_ok=True)
        
        # Annotate images
        if img_dir.exists():
            for img in sorted(img_dir.glob("*")):
                if img.is_file() and img.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                    desc = self.groq_vision_annotate(img, self.IMG_PROMPT)
                    # Clean the annotation text
                    desc = TextProcessor.clean_text(desc)
                    (ann_dir / f"{img.stem}.txt").write_text(desc, encoding="utf-8")
        
        # Annotate tables
        if tbl_dir.exists():
            for tbl in sorted(tbl_dir.glob("*")):
                if tbl.is_file() and tbl.suffix.lower() in [".json", ".md", ".markdown"]:
                    if tbl.suffix.lower() == ".json":
                        try:
                            j = json.loads(tbl.read_text(encoding="utf-8", errors="ignore"))
                            table_text = json.dumps(j, ensure_ascii=False)
                            if len(table_text) > 8000:
                                table_text = table_text[:8000] + "\n\n[Catatan: JSON dipotong karena panjang.]"
                        except Exception:
                            table_text = self.safe_read_text(tbl)
                    else:
                        table_text = self.safe_read_text(tbl)
                    
                    prompt = self.TABLE_PROMPT_TEMPLATE.format(table_text=table_text)
                    desc = self.groq_text_annotate(prompt)
                    # Clean the annotation text
                    desc = TextProcessor.clean_text(desc)
                    (ann_dir / f"{tbl.stem}.txt").write_text(desc, encoding="utf-8")
    
    @staticmethod
    def extract_and_organize(zip_path: Path, out_dir: Path):
        """Extract and organize MinerU ZIP output"""
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract all
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_dir)
        
        time.sleep(0.1)
        
        images_dir = out_dir / "images"
        tables_dir = out_dir / "tables"
        images_dir.mkdir(exist_ok=True)
        tables_dir.mkdir(exist_ok=True)
        
        # Move images
        for p in list(out_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                target = images_dir / p.name
                if p.resolve() != target.resolve():
                    try:
                        shutil.move(str(p), str(target))
                    except PermissionError:
                        shutil.copy(str(p), str(target))
                        try:
                            p.unlink()
                        except Exception:
                            pass
        
        # Move tables
        for p in list(out_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in [".md", ".markdown", ".json"]:
                target = tables_dir / p.name
                if p.resolve() != target.resolve():
                    try:
                        shutil.copy(str(p), str(target))
                    except PermissionError:
                        shutil.copy(str(p), str(target))
    
    @staticmethod
    def assemble_full_text_in_order(result_dir: Path) -> str:
        """Assemble full text with annotations"""
        # Find main markdown file
        main_md = None
        for p in result_dir.rglob("*.md"):
            parts = p.parts
            if "tables" not in parts and "annotations" not in parts:
                main_md = p
                break
        
        if not main_md:
            return "[ERROR] No main text file (.md) found.\n"
        
        content = main_md.read_text(encoding="utf-8", errors="ignore")
        
        ann_dir = result_dir / "annotations"
        annotations = {}
        
        # Load annotations
        if ann_dir.exists():
            for ann_file in ann_dir.glob("*.txt"):
                try:
                    txt = ann_file.read_text(encoding="utf-8", errors="ignore").strip()
                    if txt and not txt.startswith("[ERROR"):
                        annotations[ann_file.stem] = txt
                except Exception:
                    continue
        
        # Replace image references
        def replace_img(match):
            img_filename = match.group(1)
            stem = Path(img_filename).stem
            caption = annotations.get(stem, f"[Gambar: {stem} - caption tidak tersedia]")
            return f"\n\n[Gambar: {stem}]\n{caption}\n\n"
        
        content = re.sub(
            r'!\[[^\]]*\]\((?:\./)?images/([^)\s]+?\.(?:png|jpe?g|gif|bmp|webp))\)',
            lambda m: replace_img(m),
            content,
            flags=re.IGNORECASE
        )
        
        # Replace table references
        def replace_tbl(match):
            tbl_filename = match.group(1)
            stem = Path(tbl_filename).stem
            caption = annotations.get(stem, f"[Tabel: {stem} - caption tidak tersedia]")
            return f"\n\n[Tabel: {stem}]\n{caption}\n\n"
        
        content = re.sub(
            r'\[[^\]]*\]\((?:\./)?tables/([^)\s]+?\.(?:md|json))\)',
            lambda m: replace_tbl(m),
            content,
            flags=re.IGNORECASE
        )
        
        # Clean up newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    def extract_fulltext(self, file_path: Path, work_dir: Path) -> str:
        """
        Extract full text from PDF using MinerU
        Returns: full_text string ready for chunking
        """
        try:
            print(f"[MinerU] Starting extraction for: {file_path}")
            print(f"[MinerU] File size: {file_path.stat().st_size / (1024*1024):.2f} MB")
            
            # 1. Request presigned URL and batch_id
            print("[MinerU] Requesting presigned URL...")
            data_apply = {
                "enable_formula": Config.MINERU_ENABLE_FORMULA,
                "language": Config.MINERU_LANGUAGE,
                "enable_table": Config.MINERU_ENABLE_TABLE,
                "files": [{
                    "name": file_path.name,
                    "is_ocr": Config.MINERU_IS_OCR,
                    "data_id": "doc-1"
                }]
            }
            print(f"[MinerU] Request data: {data_apply}")
            
            try:
                apply_resp = self.session.post(
                    f"{self.api_base}/file-urls/batch",
                    headers=self.headers,
                    json=data_apply,
                    timeout=self.api_timeout
                )
                apply_resp.raise_for_status()
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"[MinerU] Connection error during presigned URL request: {e}")
                raise RuntimeError(f"Failed to get presigned URL: {str(e)}")
            
            apply_json = apply_resp.json()
            print(f"[MinerU] Apply response: {apply_json}")
            
            if apply_json.get("code") != 0:
                error_msg = apply_json.get("message", "Unknown error")
                raise RuntimeError(f"MinerU apply failed: {error_msg} (Code: {apply_json.get('code')})")
            
            upload_url = apply_json["data"]["file_urls"][0]
            batch_id = apply_json["data"]["batch_id"]
            print(f"[MinerU] Batch ID: {batch_id}")
            
            # 2. Upload PDF with chunked transfer
            print("[MinerU] Uploading file...")
            max_upload_retries = 3
            upload_attempt = 0
            
            while upload_attempt < max_upload_retries:
                try:
                    with open(file_path, "rb") as f_in:
                        # Read file size for progress tracking
                        file_size = file_path.stat().st_size
                        print(f"[MinerU] Upload attempt {upload_attempt + 1}/{max_upload_retries}")
                        
                        # IMPORTANT: For Aliyun OSS presigned URLs, signature is calculated based on specific headers
                        # Adding extra headers will break the signature
                        # Try uploading with NO extra headers first (presigned URL already has all auth info)
                        print(f"[MinerU] Sending PUT request to OSS presigned URL...")
                        
                        # Upload with no additional headers - just raw PUT
                        put_resp = requests.put(
                            upload_url,
                            data=f_in,
                            timeout=self.upload_timeout,
                            allow_redirects=False
                        )
                        print(f"[MinerU] Upload response status: {put_resp.status_code}")
                        
                        if put_resp.status_code in [200, 201, 204]:
                            print("[MinerU] File uploaded successfully")
                            break
                        elif put_resp.status_code == 403:
                            # SignatureDoesNotMatch - try with minimal headers
                            print("[MinerU] Got 403, trying with minimal headers...")
                            f_in.seek(0)  # Reset file pointer
                            
                            # Try with only Content-Type
                            minimal_headers = {
                                "Content-Type": "application/pdf"
                            }
                            put_resp = requests.put(
                                upload_url,
                                data=f_in,
                                timeout=self.upload_timeout,
                                headers=minimal_headers,
                                allow_redirects=False
                            )
                            print(f"[MinerU] Retry response status: {put_resp.status_code}")
                            
                            if put_resp.status_code in [200, 201, 204]:
                                print("[MinerU] File uploaded successfully on retry")
                                break
                            else:
                                error_detail = put_resp.text[:300] if put_resp.text else "No response body"
                                print(f"[MinerU] Upload failed with status {put_resp.status_code}: {error_detail}")
                                raise requests.exceptions.HTTPError(f"Upload failed with status {put_resp.status_code}")
                        else:
                            # Other status codes
                            error_detail = put_resp.text[:300] if put_resp.text else "No response body"
                            print(f"[MinerU] Upload failed with status {put_resp.status_code}: {error_detail}")
                            raise requests.exceptions.HTTPError(f"Upload failed with status {put_resp.status_code}")
                        
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                    upload_attempt += 1
                    if upload_attempt >= max_upload_retries:
                        raise RuntimeError(f"Upload failed after {max_upload_retries} attempts: {str(e)}")
                    wait_time = 10 * upload_attempt
                    print(f"[MinerU] Upload failed, retrying in {wait_time}s... ({str(e)})")
                    time.sleep(wait_time)
            
            # 3. Poll for results with extended timeout
            print("[MinerU] Polling for results...")
            poll_url = f"{self.api_base}/extract-results/batch/{batch_id}"
            max_retries = 120  # 10 minutes with 5 second intervals
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    poll_resp = self.session.get(
                        poll_url,
                        headers=self.headers,
                        timeout=self.api_timeout
                    )
                    poll_resp.raise_for_status()
                    poll_json = poll_resp.json()
                    print(f"[MinerU] Poll response (attempt {retry_count+1}): {poll_json.get('code')}")
                    
                    if poll_json.get("code") != 0:
                        error_msg = poll_json.get("message", "Unknown error")
                        raise RuntimeError(f"Polling error: {error_msg} (Code: {poll_json.get('code')})")
                    
                    extract_list = poll_json["data"].get("extract_result", [])
                    if extract_list:
                        item = extract_list[0]
                        state = item.get("state")
                        print(f"[MinerU] Current state: {state}")
                        
                        if state == "done":
                            result_item = item
                            break
                        elif state == "failed":
                            error_msg = item.get("message", "Unknown error")
                            raise RuntimeError(f"MinerU extraction failed: {error_msg}")
                    
                    retry_count += 1
                    time.sleep(5)
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"[MinerU] Poll request timeout/connection error: {e}, retrying...")
                    retry_count += 1
                    time.sleep(5)
            
            if retry_count >= max_retries:
                raise RuntimeError("MinerU extraction timeout (10 minutes exceeded)")
            
            if result_item.get("state") != "done":
                raise RuntimeError(f"MinerU parsing failed: {result_item}")
            
            zip_url = result_item.get("full_zip_url")
            if not zip_url:
                raise RuntimeError("No ZIP URL from MinerU")
            
            print(f"[MinerU] Downloading ZIP file...")
            # 4. Download ZIP with retry logic
            download_attempt = 0
            max_download_retries = 3
            
            while download_attempt < max_download_retries:
                try:
                    zip_path = work_dir / "result.zip"
                    print(f"[MinerU] Download attempt {download_attempt + 1}/{max_download_retries}")
                    
                    with self.session.get(
                        zip_url,
                        stream=True,
                        timeout=self.download_timeout,
                        headers=self.headers
                    ) as r_zip:
                        r_zip.raise_for_status()
                        total_size = 0
                        with open(zip_path, "wb") as f_zip:
                            for chunk in r_zip.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f_zip.write(chunk)
                                    total_size += len(chunk)
                        print(f"[MinerU] ZIP downloaded: {total_size / (1024*1024):.2f} MB")
                        break
                        
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError) as e:
                    download_attempt += 1
                    if download_attempt >= max_download_retries:
                        raise RuntimeError(f"Download failed after {max_download_retries} attempts: {str(e)}")
                    wait_time = 10 * download_attempt
                    print(f"[MinerU] Download failed, retrying in {wait_time}s... ({str(e)})")
                    time.sleep(wait_time)
            
            print("[MinerU] Extracting and organizing files...")
            # 5. Extract and organize
            self.extract_and_organize(zip_path, work_dir)
            
            print("[MinerU] Annotating images and tables...")
            # 6. Annotate
            self.annotate_dir(work_dir)
            
            print("[MinerU] Assembling final text...")
            # 7. Assemble final text
            final_text = self.assemble_full_text_in_order(work_dir)
            
            print(f"[MinerU] Final text length: {len(final_text)} characters")
            
            # 8. Clean the text to remove all symbols and special characters
            from app.utils.text_processor import TextProcessor
            final_text = TextProcessor.clean_text(final_text)
            
            print("[MinerU] Extraction completed successfully!")
            return final_text
            
        except Exception as e:
            print(f"[MinerU] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


# Singleton instance
mineru_processor = MinerUProcessor()
