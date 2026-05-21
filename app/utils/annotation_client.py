import time
from app.utils.openai_client import groq_client


class AnnotationClient:
    """
    Annotation client using Groq vision.
    If rate limited (429): Wait 20 seconds, then retry (no fallback).
    """
    
    def __init__(self):
        self.rate_limit_errors = 0  # Track 429 errors
    
    def vision_annotate(self, data_url: str, prompt: str) -> str:
        """
        Generate image annotation using Groq with retry on rate limit.
        
        If 429 error: Wait 20 seconds, then retry Groq (no fallback)
        """
        try:
            print(f"📸 [ANNOTATION] Using Groq for image annotation...")
            result = groq_client.vision_annotate(data_url, prompt)
            return result
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "too many" in error_str.lower():
                print(f"\n⚠️  [RATE LIMIT] HTTP 429 from Groq. Waiting 20 seconds...")
                self.rate_limit_errors += 1
                time.sleep(20)
                print(f"✅ [RETRY] Retrying Groq after cooldown...\n")
                # Retry Groq (no fallback)
                try:
                    result = groq_client.vision_annotate(data_url, prompt)
                    return result
                except Exception as retry_error:
                    error_msg = f"[ERROR] Groq vision annotation failed after retry: {retry_error}"
                    print(error_msg)
                    return error_msg
            else:
                # Other error - return error
                error_msg = f"[ERROR] Groq vision annotation failed: {e}"
                print(error_msg)
                return error_msg
    
    def text_annotate(self, prompt: str) -> str:
        """
        Generate table annotation using Groq with retry on rate limit.
        
        If 429 error: Wait 20 seconds, then retry Groq (no fallback)
        """
        try:
            print(f"📋 [ANNOTATION] Using Groq for table annotation...")
            result = groq_client.text_annotate(prompt)
            return result
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "too many" in error_str.lower():
                print(f"\n⚠️  [RATE LIMIT] HTTP 429 from Groq. Waiting 20 seconds...")
                self.rate_limit_errors += 1
                time.sleep(20)
                print(f"✅ [RETRY] Retrying Groq after cooldown...\n")
                # Retry Groq (no fallback)
                try:
                    result = groq_client.text_annotate(prompt)
                    return result
                except Exception as retry_error:
                    error_msg = f"[ERROR] Groq text annotation failed after retry: {retry_error}"
                    print(error_msg)
                    return error_msg
            else:
                # Other error - return error
                error_msg = f"[ERROR] Groq text annotation failed: {e}"
                print(error_msg)
                return error_msg
    
    def get_status(self) -> dict:
        """Get current annotation client status"""
        return {
            "rate_limit_errors": self.rate_limit_errors,
            "current_client": "Groq (with retry on 429)"
        }


# Singleton instance
annotation_client = AnnotationClient()
