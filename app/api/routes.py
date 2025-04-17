from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any
import logging
import json

from ..core.auth import get_current_user, validate_token
from ..core.schema import QuestionRequest, QuestionResponse, HealthResponse, WebhookResponse, TokenData
from ..services.whatsapp_service import WhatsAppService
from ..services.llm_service import LLMService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
whatsapp_service = WhatsAppService()
llm_service = LLMService()

# Health check endpoint
@router.get("/healthcheck", response_model=HealthResponse)
async def healthcheck():
    """Health check endpoint to verify service is running"""
    return {"status": "OK"}

# API endpoint to ask a question
@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a question from a client application
    
    This endpoint accepts a question and optional configuration,
    and returns a response from the LLM.
    """
    try:
        # Extract profile_id from request or use current user
        profile_id = request.overrideConfig.get("profile_id") if request.overrideConfig else current_user.get("profile_id", "anonymous")
        
        # Process the question
        response = await llm_service.process_message(
            profile_id=profile_id,
            question=request.question
        )
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing your request"
        )

# WhatsApp webhook verification endpoint
@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    """
    Verify webhook for WhatsApp integration
    
    This endpoint is called by WhatsApp to verify the webhook.
    """
    try:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        # Verify token should come from settings
        verify_token = settings.WHATSAPP_VERIFY_TOKEN
        
        if mode == "subscribe" and token == verify_token:
            logger.info("Webhook verified successfully")
            return challenge
            
        logger.warning(f"Invalid verification attempt: mode={mode}, token={token}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification token invalid"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook verification"
        )

# WhatsApp webhook for incoming messages
@router.post("/webhook", response_model=WebhookResponse)
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Process incoming WhatsApp webhook
    
    This endpoint receives messages from WhatsApp and processes them.
    Responses are sent asynchronously using background tasks.
    """
    try:
        # Parse the webhook body
        body = await request.json()
        
        # Skip status updates
        if "statuses" in str(body):
            logger.info("Received status update - ignoring")
            return {"status": "success"}
        
        # Process the webhook
        responses = await whatsapp_service.process_webhook(body)
        
        # Send responses in the background
        for response in responses:
            background_tasks.add_task(
                whatsapp_service.send_message,
                response["recipient"],
                response["message"]
            )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Always return success to WhatsApp, handle errors internally
        return {"status": "success"}