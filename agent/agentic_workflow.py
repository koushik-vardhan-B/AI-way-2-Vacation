from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT, CONVERSATION_PROMPT, get_system_prompt
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Importing all tool modules
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool


class GraphBuilder:
    """
    GraphBuilder integrates LLM + Tools + Prompt logic into a cohesive LangGraph-based workflow.
    It uses multiple external tool modules (Weather, Places, Expense, Currency).
    """

    def __init__(self, model_provider: str = "groq"):
        # Load the LLM from the selected provider (Groq / OpenAI / Gemini)
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()

        # Initialize memory to maintain context between user queries
        self.memory = MemorySaver()

        # Initialize tools
        self.tools = []
        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConverterTool()

        # Combine all tools from different modules
        self.tools.extend([
            *self.weather_tools.weather_tool_list,
            *self.place_search_tools.get_tools(),          # ✅ Use the updated method
            *self.calculator_tools.calculator_tool_list,
            *self.currency_converter_tools.currency_converter_tool_list,
        ])

        # Bind tools to the loaded LLM
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)

        # Store prompts
        self.system_prompt = SYSTEM_PROMPT
        self.conversation_prompt = CONVERSATION_PROMPT

        # Graph object (to be built later)
        self.graph = None

    # -----------------------------------------------------
    # AGENT FUNCTION: Core brain that manages conversations
    # -----------------------------------------------------
    def agent_function(self, state: MessagesState):
        """Main agent logic. Handles both initial and follow-up user messages."""
        user_question = state["messages"]

        # Check if it’s a new session or follow-up
        is_initial = len(user_question) <= 1

        # Choose which system prompt to use
        system_prompt = get_system_prompt(is_initial_request=is_initial)

        # Combine prompt + user conversation history
        input_question = [system_prompt] + user_question

        # Let the model think with tool access
        response = self.llm_with_tools.invoke(input_question)

        return {"messages": [response]}

    # -----------------------------------------------------
    # BUILD GRAPH: Defines workflow of LLM ↔ Tools ↔ Memory
    # -----------------------------------------------------
    def build_graph(self):
        """Construct and compile the conversation + tool flow graph."""
        graph_builder = StateGraph(MessagesState)

        # Define the nodes
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))

        # Define the edges (flow)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("agent", END)

        # Compile the graph with checkpointing (conversation memory)
        self.graph = graph_builder.compile(checkpointer=self.memory)
        return self.graph

    # -----------------------------------------------------
    # CALLABLE ENTRYPOINT: Return a ready-to-use graph
    # -----------------------------------------------------
    def __call__(self):
        return self.build_graph()
