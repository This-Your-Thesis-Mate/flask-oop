import time
from typing import Optional
from app.utils.openai_client import groq_client, azure_openai_client


class AnnotationClient:
    """
    Annotation client with automatic fallback.
    - Uses Groq by default (faster)
    - Falls back to Sumopod (GPT-4o-mini) when Groq returns 429 (Too Many Requests)
    - Switches back to Groq after 20 seconds cooldown
    """
    
    def __init__(self):
        self.using_fallback = False
        self.fallback_start_time = None
        self.fallback_cooldown = 20  # 20 seconds before switching back to Groq
        self.rate_limit_errors = 0
        
    def _check_fallback_timeout(self) -> bool:
        """Check if fallback cooldown period has expired"""
        if not self.using_fallback:
            return False
        
        if self.fallback_start_time is None:
            return False
        
        elapsed = time.time() - self.fallback_start_time
        if elapsed >= self.fallback_cooldown:
            print(f"\n✅ [FALLBACK] Cooldown expired ({elapsed:.1f}s). Switching back to Groq.")
            self.using_fallback = False
            self.fallback_start_time = None
            self.rate_limit_errors = 0
            return True
        
        return False
    
    def _activate_fallback(self):
        """Activate fallback to Sumopod/GPT"""
        self.using_fallback = True
        self.fallback_start_time = time.time()
        self.rate_limit_errors += 1
        print(f"\n⚠️  [FALLBACK] Rate limited by Groq. Switching to Sumopod (GPT-4o-mini)")
        print(f"   Error count: {self.rate_limit_errors}")
        print(f"   Fallback mode active for {self.fallback_cooldown} seconds\n")
    
    def vision_annotate(self, data_url: str, prompt: str) -> str:
        """
        Generate image annotation with fallback mechanism.
        
        Primary: Groq vision
        Fallback: Sumopod (GPT-4o-mini) vision when Groq rate-limited
        """
        # Check if we should switch back to Groq
        self._check_fallback_timeout()
        
        if self.using_fallback:
            # Use Sumopod (GPT-4o-mini)
            try:
                print(f"📸 [ANNOTATION] Using Sumopod (GPT-4o-mini) for image annotation...")
                result = azure_openai_client.vision_annotate(data_url, prompt)
                return result
            except Exception as e:
                error_msg = f"[ERROR] Sumopod vision annotation failed: {e}"
                print(error_msg)
                return error_msg
        else:
            # Try Groq first (primary)
            try:
                print(f"📸 [ANNOTATION] Using Groq for image annotation...")
                result = groq_client.vision_annotate(data_url, prompt)
                return result
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "too many" in error_str.lower():
                    self._activate_fallback()
                    # Recursively call to use fallback
                    return self.vision_annotate(data_url, prompt)
                else:
                    # Other error - try fallback anyway
                    print(f"\n⚠️  [ANNOTATION] Groq error: {e}. Trying fallback...")
                    self._activate_fallback()
                    return self.vision_annotate(data_url, prompt)
    
    def text_annotate(self, prompt: str) -> str:
        """
        Generate table annotation with fallback mechanism.
        
        Primary: Groq text
        Fallback: Sumopod (GPT-4o-mini) text when Groq rate-limited
        """
        # Check if we should switch back to Groq
        self._check_fallback_timeout()
        
        if self.using_fallback:
            # Use Sumopod (GPT-4o-mini)
            try:
                print(f"📋 [ANNOTATION] Using Sumopod (GPT-4o-mini) for table annotation...")
                result = azure_openai_client.text_annotate(prompt)
                return result
            except Exception as e:
                error_msg = f"[ERROR] Sumopod text annotation failed: {e}"
                print(error_msg)
                return error_msg
        else:
            # Try Groq first (primary)
            try:
                print(f"📋 [ANNOTATION] Using Groq for table annotation...")
                result = groq_client.text_annotate(prompt)
                return result
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "too many" in error_str.lower():
                    self._activate_fallback()
                    # Recursively call to use fallback
                    return self.text_annotate(prompt)
                else:
                    # Other error - try fallback anyway
                    print(f"\n⚠️  [ANNOTATION] Groq error: {e}. Trying fallback...")
                    self._activate_fallback()
                    return self.text_annotate(prompt)
    
    def get_status(self) -> dict:
        """Get current annotation client status"""
        return {
            "using_fallback": self.using_fallback,
            "fallback_start_time": self.fallback_start_time,
            "rate_limit_errors": self.rate_limit_errors,
            "current_client": "Sumopod (GPT-4o-mini)" if self.using_fallback else "Groq",
            "fallback_cooldown": self.fallback_cooldown
        }


# Singleton instance
annotation_client = AnnotationClient()
