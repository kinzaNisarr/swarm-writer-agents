import nltk
from nltk.tokenize import sent_tokenize
from typing import Dict
from openai import OpenAI


class NewsSummarizer:
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.client = OpenAI(base_url=base_url, api_key="ollama")  # required but unused
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

    def _create_messages(self, article: Dict) -> list:
        # Extract first few sentences for context
        content = article["summary"]
        sentences = sent_tokenize(content)
        context = " ".join(sentences[:3])

        return [
            {
                "role": "system",
                "content": """You are an expert news editor skilled at creating 
             concise, informative summaries of local news articles. Focus on key facts and 
             local impact while maintaining objectivity.""",
            },
            {
                "role": "user",
                "content": f"""Summarize this local news article:
            
            Title: {article['title']}
            Category: {article.get('category', 'general')}
            Content: {context}
            
            Format your response as:
            1. Main point (1 sentence)
            2. Key details (1-2 sentences)
            3. Local impact (1 sentence)""",
            },
        ]

    def generate_summary(self, article: Dict) -> str:
        try:
            response = self.client.chat.completions.create(
                model="llama3.2",
                messages=self._create_messages(article),
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating summary: {str(e)}"
