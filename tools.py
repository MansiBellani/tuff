import os
from arcadepy import Arcade
from dotenv import load_dotenv

load_dotenv()

# --- Initialize Arcade Client ---
ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
USER_ID = os.getenv("ARCADE_USER_ID")
client = Arcade(api_key=ARCADE_API_KEY)

# --- Tool 1: Google Docs ---
def add_content_to_document(content: str, file_name: str = "R&D Intelligence Report"):
    """
    Creates a new Google Doc with the provided text content.
    """
    if not USER_ID:
        return "Error: ARCADE_USER_ID is not set in the .env file."
    print(f"TOOL CALLED: Creating Google Doc titled '{file_name}'...")
    try:
        result = client.tools.execute(
            tool_name="GoogleDocs.CreateDocumentFromText@4.0.0",
            input={"title": file_name, "text_content": content},
            user_id=USER_ID,
        )

        # --- NEW DEBUGGING CODE ---
        # This will print the exact structure of the response object to your terminal
        print("\n--- DEBUGGING ARCADE RESPONSE ---")
        print(f"Type of result object: {type(result)}")
        print(f"Result object itself: {result}")
        print(f"Available attributes: {dir(result)}")
        print("--- END DEBUGGING ---\n")
        # --- END OF DEBUGGING CODE ---

        # The old logic is temporarily bypassed to allow us to see the debug info
        # We will fix this in the next step based on the debug output
        return "Debugging complete. Please check your terminal output."

    except Exception as e:
        print(f"ERROR: Arcade tool execution failed: {e}")
        return "Failed to create the Google Document due to an error."


# --- Tool 2: Send Email ---
def send_email(content: str, subject: str, recipient: str):
    """
    Sends an email with the provided content, subject, and recipient.
    Use this tool when a user wants to 'email', 'send', or 'share' a report or summary.
    """
    if not USER_ID:
        return "Error: ARCADE_USER_ID is not set in the .env file."
    print(f"TOOL CALLED: Sending email to {recipient} with subject '{subject}'...")
    try:
        result = client.tools.execute(
            tool_name="Gmail.SendEmail@3.0.0",
            input={"body": content, "subject": subject, "recipient": recipient},
            user_id=USER_ID,
        )
        
        # --- CORRECTED PART ---
        # Access the results via the .value attribute
        if result and result.status == "completed" and result.value and result.value.get("status") == "success":
            print(f"Successfully sent email to {recipient}")
            return f"Success! The email has been sent to {recipient}."
        else:
            return f"An unknown error occurred while sending the email. Response: {result.value}"

    except Exception as e:
        print(f"ERROR: Arcade tool execution failed: {e}")
        return f"Failed to send the email due to an error: {e}"

# --- Tool 3: Speak Summary (Placeholder) ---
def speak_summary(summary_text: str):
    """
    Speaks the provided text summary out loud using a voice model.
    Use this tool ONLY when the user gives an explicit voice command.
    """
    print(f"TOOL CALLED: Speaking summary out loud via Vapi SDK.")
    # Placeholder for Vapi SDK call
    return "The summary has been spoken out loud."