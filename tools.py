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
    Returns the document URL string when available (so the UI can link to it).
    """
    if not USER_ID:
        return "Error: ARCADE_USER_ID is not set in the .env file."
    if not ARCADE_API_KEY:
        return "Error: ARCADE_API_KEY is not set in the .env file."

    safe_text = (content or "").strip()
    if not safe_text:
        return "Error: No content to insert into the Google Doc."

    print(f"TOOL CALLED: Creating Google Doc titled '{file_name}'...")
    try:
        result = client.tools.execute(
            tool_name="GoogleDocs.CreateDocumentFromText@4.0.0",
            input={"title": file_name, "text_content": safe_text},
            user_id=USER_ID,
        )

        # Try common Arcade result shapes
        def _extract(res):
            out = getattr(res, "output", None)
            if out is not None:
                val = getattr(out, "value", None)
                if isinstance(val, dict):
                    url = val.get("documentUrl") or val.get("url") or val.get("webViewLink") or val.get("alternateLink")
                    doc_id = val.get("documentId")
                    return url, doc_id

            val2 = getattr(res, "value", None)
            if isinstance(val2, dict):
                url = val2.get("documentUrl") or val2.get("url") or val2.get("webViewLink") or val2.get("alternateLink")
                doc_id = val2.get("documentId")
                return url, doc_id

            if isinstance(res, dict):
                url = res.get("documentUrl") or res.get("url") or res.get("webViewLink") or res.get("alternateLink")
                doc_id = res.get("documentId")
                return url, doc_id

            if isinstance(res, str) and res.startswith("http"):
                return res, None

            return None, None

        url, doc_id = _extract(result)
        status = getattr(result, "status", None)
        success_flag = getattr(result, "success", None)

        if url:
            return url
        if success_flag or status == "success":
            return f"Success! Document created{f' (id: {doc_id})' if doc_id else ''}, but no URL was returned."
        return f"Unknown response from Arcade: {getattr(result, 'output', None) or getattr(result, 'value', None) or result}"

    except Exception as e:
        print(f"ERROR: Arcade tool execution failed: {e}")
        return f"Failed to create the Google Document due to an error: {e}"



# --- Tool 2: Send Email ---
def send_email(content: str, subject: str, recipient: str):
    """
    Sends an email with the provided content, subject, and recipient.
    """
    if not USER_ID:
        return "Error: ARCADE_USER_ID is not set in the .env file."
    if not ARCADE_API_KEY:
        return "Error: ARCADE_API_KEY is not set in the .env file."
    if not recipient:
        return "Error: recipient email is required."

    print(f"TOOL CALLED: Sending email to {recipient} with subject '{subject}'...")
    try:
        result = client.tools.execute(
            tool_name="Gmail.SendEmail@3.0.0",
            input={"body": content or "", "subject": subject or "", "recipient": recipient},
            user_id=USER_ID,
        )

        status = getattr(result, "status", None)
        success_flag = getattr(result, "success", None)

        out = getattr(result, "output", None)
        val = getattr(out, "value", None) if out is not None else None
        if isinstance(val, dict):
            tool_state = (val.get("status") or val.get("state") or "").lower()
            if tool_state == "success":
                print(f"Successfully sent email to {recipient}")
                return f"Success! The email has been sent to {recipient}."

        if success_flag or status == "success":
            print(f"Successfully sent email to {recipient}")
            return f"Success! The email has been sent to {recipient}."

        raw_val = val if val is not None else getattr(result, "value", None)
        return f"An unknown error occurred while sending the email. Response: {raw_val or result}"

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
