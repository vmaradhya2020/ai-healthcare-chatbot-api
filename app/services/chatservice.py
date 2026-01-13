import logging
import os
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

import openai
from sqlalchemy.orm import Session

from .ragservice import RAGService
from ..models import ChatLog, UsageStats
from ..models import User
from dotenv import load_dotenv 


load_dotenv() 
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.openai_client = openai.OpenAI(api_key=api_key)
        self.rag_service = RAGService()
        
    async def process_message(
        self, 
        message: str, 
        user: User, 
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a chat message with RAG integration and logging."""
        start_time = time.time()
        
        try:
            # Determine if RAG should be used
            should_use_rag = await self._should_use_rag(message)
            
            if should_use_rag:
                response_data = await self._process_with_rag(message, user, db)
            else:
                response_data = await self._process_without_rag(message, user)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the interaction
            await self._log_chat_interaction(
                user=user,
                session_id=session_id,
                user_message=message,
                bot_response=response_data['response'],
                intent=response_data.get('intent'),
                data_source=response_data.get('data_source'),
                confidence_score=response_data.get('confidence_score'),
                response_time_ms=response_time_ms,
                rag_used=should_use_rag,
                relevant_documents=response_data.get('relevant_documents'),
                db=db
            )
            
            # Update usage stats
            await self._update_usage_stats(db, response_time_ms, should_use_rag)
            
            return {
                'response': response_data['response'],
                'intent': response_data.get('intent'),
                'data_source': response_data.get('data_source'),
                'session_id': session_id
            }
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise