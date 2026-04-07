import os
from dotenv import load_dotenv
from typing import Any
from pathlib import Path
import uuid
import json

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool, ToolSet, ListSortOrder, MessageRole

# Create a function to submit a support ticket
def submit_support_ticket(email_address: str, description: str) -> str:
    script_dir = Path(__file__).parent  #Get the directory of the script
    ticket_number = str(uuid.uuid4()).replace('-', '')[:6]
    file_name = f"ticket-{ticket_number}.txt"
    file_path = script_dir / file_name
    text = f"Support ticket: {ticket_number}\nSubmitted by: {email_address}\nDescription:\n{description}"
    file_path.write_text(text)

    message_json = json.dumps({"message: " f"Support ticket {ticket_number} submitted. The ticket file is {file_name}"})
    return message_json

# Define a set of callable functions
#user_functions: Set[Callable[...,Any]] = {
#   submit_support_ticket
#}

def main(): 

    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    # Load environment variables from .env file
    load_dotenv()
    project_endpoint= os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")

    # Connect to the AI Project client
    agent_client = AgentsClient(
        endpoint = project_endpoint,
        credential = DefaultAzureCredential
            (exclude_environment_credential = True,
             exclude_managed_identity_credential = True)
    )
    with agent_client:

        # Create a FunctionTool definition
        functions = FunctionTool({submit_support_ticket})
        toolset = ToolSet()
        toolset.add(functions)
        agent_client.enable_auto_function_calls(toolset)

        # Initialize the agent with the FunctionTool
        agent = agent_client.create_agent(
            model = model_deployment,
            name = "support-agent",
            instructions =  """You are a technical support agent.
                                When a user has a technical issue, you get their email address and a description of the issue.
                                Then you use those values to submit a support ticket using the function available to you.
                                If a file is saved, tell the user the file name.
                            """,
            toolset = toolset,
        )
        print(f"You are chatting with: {agent.name} ({agent.id})")


        # Create a thread for the chat session
        thread = agent_client.threards.create()
       

        # Loop until the user types 'quit'
        while True:
            # Get input text
            user_prompt = input("Enter a prompt (or type 'quit' to exit): ")
            if user_prompt.lower() == "quit":
                break
            if len(user_prompt) == 0:
                print("Please enter a prompt.")
                continue

            # Send a prompt to the agent
            message = agent_client.messages.create(
                thread_id = thread.id,
                role = "user",
                content = user_prompt,
            )
            run = agent_client.runs.create_and_process(thread_id = thread.id, agent_id = agent.id)

            # Get the agent's response
            last_msg = agent_client.messages.get_last_message_text_by_role(
                thread_id = thread.id,
                role=MessageRole.AGENT,
            )
            if last_msg:
                print(f"Last Message: {last_msg.text.value}")

            # Check the run status for failures
            if run.status == "failed":
                print(f"Run failed: {run.last_error}")

            # Process function calls
            

            # If there are function call outputs, send them back to the model
            

        # Clean up
        agent_client.delete_agent(agent.id)

if __name__ == '__main__': 
    main()
