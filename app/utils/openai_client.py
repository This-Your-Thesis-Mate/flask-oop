"""
OpenAI and Azure OpenAI client utilities
"""
import requests
import json
from openai import AzureOpenAI
from groq import Groq
from app.config import Config


class EmbeddingClient:
    """Client for Azure OpenAI Embedding"""
    
    def __init__(self):
        self.url = Config.AZURE_EMBEDDING_URL
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': Config.AZURE_EMBEDDING_API_KEY
        }
    
    def get_embedding(self, text):
        """Get embedding for a single text"""
        payload = json.dumps({"input": text})
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        return response.json()['data'][0]['embedding']
    
    def get_embeddings(self, texts):
        """Get embeddings for multiple texts"""
        payload = json.dumps({"input": texts})
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        return response.json()['data']


class AzureOpenAIClient:
    """Client for Azure OpenAI Chat Completion"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT
    
    def generate_completion(self, messages, temperature=0.2, top_p=0.95):
        """Generate chat completion"""
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=temperature,
            top_p=top_p
        )
        return response.choices[0].message.content


class GroqClient:
    """Client for Groq AI"""
    
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.vision_model = Config.GROQ_VISION_MODEL
        self.text_model = Config.GROQ_TEXT_MODEL
    
    def vision_annotate(self, data_url, prompt, temperature=0.2, max_tokens=450):
        """Generate annotation using vision model"""
        resp = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    
    def text_annotate(self, prompt, temperature=0.2, max_tokens=600):
        """Generate annotation using text model"""
        resp = self.client.chat.completions.create(
            model=self.text_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()


# Singleton instances
embedding_client = EmbeddingClient()
azure_openai_client = AzureOpenAIClient()
groq_client = GroqClient()
