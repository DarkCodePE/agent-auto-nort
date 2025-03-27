# Define State structure
# LangChain imports
from operator import add

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.documents import Document
from typing import List, Optional, TypedDict, Annotated

from langgraph.graph import add_messages


class AmbiguityClassification(TypedDict):
    is_ambiguous: Optional[bool]  # For tracking whether the user's input is ambiguous
    ambiguity_category: Optional[str]  # For storing the category of ambiguity
    clarification_question: Optional[str]


class VehicleInfo(TypedDict):
    name: Optional[str]  # nombre del vehículo
    image: Optional[str]  # url de la imagen del vehículo
    url: Optional[str]  # url del vehículo
    price: Optional[float]  # precio del vehículo
    motor: Optional[str]  # motor del vehículo
    transmission: Optional[str]  # transmisión del vehículo
    capacity: Optional[int]  # capacidad del vehículo
    features: Optional[List[str]]  # características del vehículo


class State(TypedDict):
    input: str
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    answer: str
    documents: Optional[List[Document]]  # For storing retrieved documents
    web_search: Optional[str]  # For deciding whether to perform a web search
    summary: Optional[str]  # For storing the summary of the conversation
    vehicle_info: VehicleInfo
    feedback: Annotated[List[str], add]
