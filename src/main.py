"""
Main entry point for the E-commerce Store Manager application.
"""
import uvicorn
from fastapi import FastAPI
from core.config import settings
from orchestrator import Orchestrator

app = FastAPI(
    title="E-commerce Store Manager",
    description="AI-powered E-commerce Store Management System",
    version="0.1.0"
)

# Initialize the orchestrator
orchestrator = Orchestrator()

@app.get("/")
async def root():
    """Root endpoint to verify the API is running."""
    return {
        "status": "ok", 
        "message": "E-commerce Store Manager API is running",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }

@app.post("/chat")
async def chat(message: str):
    """Endpoint for chatting with the AI agents."""
    response = orchestrator.handle_user_message(message)
    return {"response": response}

def test_agents():
    """Test function to verify agent functionality."""
    test_messages = [
        # Information Agent Tests
        "תראה לי את המוצרים",
        "הצג דוח מכירות לחודש האחרון",
        "מה הקופונים הפעילים?",
        
        # Action Agent Tests
        "הוסף מוצר חדש בשם חולצת כותנה במחיר 99",
        "צור קופון של 20 אחוז",
        "צור קופון של 50 שקל",
        
        # Research Agent Tests
        "תבדוק מחקר על מתחרים בתחום האופנה",
        "השוואת מחירים למוצרים דומים",
        
        # Unknown Queries
        "משהו אחר...",
        "מה השעה?"
    ]

    print("\nבדיקת מערכת הסוכנים:")
    print("-" * 50)
    for msg in test_messages:
        print(f"\nמשתמש: {msg}")
        response = orchestrator.handle_user_message(msg)
        print(f"בוט: {response}")
    print("-" * 50)

def main():
    """Main function to run the application."""
    # Debug information
    print("Configuration loaded:")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Store URL: {settings.WC_STORE_URL}")
    
    # Test agents if in debug mode
    if settings.DEBUG:
        test_agents()
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    main() 