import requests
import json
from openai import OpenAI
from openai import AzureOpenAI
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


class SumopodClient:
    """Client for Sumopod Chat Completion"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.SUMOPOD_API_KEY,
            base_url=Config.SUMOPOD_BASE_URL
        )
        self.model = Config.SUMOPOD_MODEL
    
    def generate_completion(self, messages, temperature=0.2, top_p=0.95):
        """Generate chat completion"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            top_p=top_p
        )
        return response.choices[0].message.content


class AzureOpenAIClient:
    """Client for Azure OpenAI Chat Completion"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_KEY,
        )
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT
    
    def generate_completion(self, messages, temperature=0.2, top_p=0.95, max_tokens=16384):
        """Generate chat completion"""
        # Note: Azure OpenAI model only supports default temperature (1), so we don't pass temperature/top_p
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def vision_annotate(self, data_url, prompt, temperature=0.2, max_tokens=450):
        """Generate annotation using vision model"""
        # Note: Azure OpenAI model only supports default temperature (1), so we don't pass temperature
        resp = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            max_completion_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    
    def text_annotate(self, prompt, temperature=0.2, max_tokens=600):
        """Generate annotation using text model"""
        # Note: Azure OpenAI model only supports default temperature (1), so we don't pass temperature
        resp = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()


# Singleton instances
embedding_client = EmbeddingClient()
azure_openai_client = AzureOpenAIClient()
