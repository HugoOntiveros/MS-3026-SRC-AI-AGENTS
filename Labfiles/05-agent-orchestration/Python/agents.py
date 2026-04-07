# Add references
import asyncio
from typing import cast
from agent_framework import ChatMessage, Role, SequentialBuilder,WorkflowOutputEvent
from agent_framework.azure import AzureAIAgentClient
from azure.identity import AzureCliCredential

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentsSettings
from semantic_kernel.agents.strategies import TerminationStrategy, SequentialSelectionStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_decorator import kernel_function


async def main():
    # Agent instructions
    summarizer_instructions="""
    Summarize the customer's feedback in one short sentence. Keep it neutral and concise.
    Example output:
    App crashes during photo upload.
    User praises dark mode feature.
    """

    classifier_instructions="""
    Classify the feedback as one of the following: Positive, Negative, or Feature request.
    """

    action_instructions="""
    Based on the summary and classification, suggest the next action in one short sentence.
    Example output:
    Escalate as a high-priority bug for the mobile team.
    Log as positive feedback to share with design and marketing.
    Log as enhancement request for product backlog.
    """

    # Create the chat client
    ai_agent_settings = AzureAIAgentsSettings()

    async with (
        DefaultAzureCredential(exclude_environment_credential = True,
                               exclude_managed_identity_credential = True) as creds,
        AzureAIAgent.create_client(credential = creds) as client,
    ):

        # Create agents
        # Summarizer agent
        summarizer_agent_definition = await client.agents.create_agent(
            model = ai_agent_settings.model_deployment_name,
            name = "summarizer_agent",
            instructions = summarizer_instructions
        )

        agent_summarizer = AzureAIAgent(
            client = client,
            definition = summarizer_agent_definition,
        )


        # Classifier agent
        classifier_agent_definition = await client.agents.create_agent(
            model = ai_agent_settings.model_deployment_name,
            name = "classifier_agent",
            instructions = classifier_instructions
        )

        agent_classifier = AzureAIAgent(
            client = client,
            definition = classifier_agent_definition,
        )


        # Action agent
        action_agent_definition = await client.agents.create_agent(
            model = ai_agent_settings.model_deployment_name,
            name = "action_agent",
            instructions = action_instructions
        )

        agent_action = AzureAIAgent(
            client = client,
            definition = action_agent_definition,
        )
    
        # Add the agents to a group chat
        chat = AgentGroupChat(
            agents = [agent_summarizer, agent_classifier, agent_action].
            termination_strategy = ApprovalTerminationStrategy(
                agents = [agent_summarizer],
                maximum_iterations = 10,
                automatic_reset = True
            ),
            selection_strategy = SelectionStrategy(agents=[agent_summarizer,agent_classifier,agent_action]),
        )

        # Initialize the current feedback
        feedback="""
                I use the dashboard every day to monitor metrics, and it works well overall. 
                But when I'm working late at night, the bright screen is really harsh on my eyes. 
                If you added a dark mode option, it would make the experience much more comfortable.
        """
    

        # Build sequential orchestration
    
    
        # Run and collect outputs
    
    
        # Display outputs
    
# class for selection strategy
class SelectionStrategy(SequentialSelectionStrategy):
    """A strategy for determining which agent should take the next turn in the chat."""

    # Select the next agent that should take the next turn in the chat
    async def select_agent(self, agents, history):
        """Check which agent should take the next turn in the chat."""

        # The Action agent should go after the classifier agent, which in turn, goes after the summarizer agent
        if (history[-1].name == "action_agent" or history[-1].role == AuthorRole.User):
            agent_name = "summarizer_agent"
            return next((agent for agent in agents if agent.name == agent_name), None)

        if (history[-1].name == "summarizer_agent"):
            agent_name = "classifier_agent"
            return next((agent for agent in agents if agent.name == agent_name), None)

        # Otherwise it is the Action's agent turn
        return next((agent for agent in agents if agent.name == "action_agent"), None)

# class for termination strategy
class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    #End chat if the agent has indicated that there is no action needed
    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return await super().should_agent_terminate(agent, history)
    
if __name__ == "__main__":
    asyncio.run(main())