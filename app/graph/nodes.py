import logging
from typing import Dict, Any, Literal

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_qdrant import Qdrant
from langgraph.types import interrupt, Command
from numpy.f2py.crackfortran import previous_context
from qdrant_client import QdrantClient

from app.graph.state import State, AmbiguityClassification, VehicleInfo
from app.config.settings import LLM_MODEL, QDRANT_URL, QDRANT_API_KEY

from app.services.document_service import DocumentService
from app.services.location_services_map_box import get_district_coordinates, PLANTS, calculate_distances
from app.util.prompt import SALES_TALK_PROMPT, IMPORTANT_INFO_PROMPT

logger = logging.getLogger(__name__)

# Singleton document service
_document_service = None


def get_document_service() -> DocumentService:
    """Get or create a DocumentService singleton."""
    global _document_service
    if _document_service is None:
        try:
            _document_service = DocumentService()
        except Exception as e:
            logger.error(f"Error initializing document service: {str(e)}")
            raise
    return _document_service


def retrieve_context(state: State) -> dict:
    """
    Retrieve relevant context based on the user's input.

    In a more advanced implementation, this would use a vector store
    to retrieve relevant documents based on the user's query.

    Args:
        state: The current state

    Returns:
        The updated state with context
    """
    query_text = state["input"]

    # Get the document service
    document_service = get_document_service()

    # Search for relevant documents
    search_results = document_service.search_documents(query_text, limit=5)

    # Convert to LangChain Document objects
    documents = []
    for result in search_results:
        doc = Document(
            page_content=result["content"],
            metadata={
                **result["metadata"],
                "score": result["score"],
                "document_id": result["id"]
            }
        )
        documents.append(doc)

    # Build context text from documents
    if documents:
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Extract title or use a default
            title = doc.metadata.get("name", f"Document {i}")
            # Add source info and content
            context_parts.append(f"Document {i}: {title}\n{doc.page_content}")

        # Join all parts with clear separators
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = ""

    # Update state
    state["context"] = context

    logger.info(f"Retrieved {len(documents)} relevant documents for query: {query_text[:50]}...")
    return {"context": context}

def capture_important_info(state: State) -> dict:
    """
    Analiza la conversación para extraer y almacenar información importante
    sobre el vehículo y las necesidades del usuario.
    """
    llm = ChatOpenAI(model=LLM_MODEL)

    # Obtenemos los mensajes recientes para analizar
    messages = state["messages"][-5:] if len(state["messages"]) > 5 else state["messages"]
    #logger.info(f"messages: {messages}")
    question = state["input"]

    system_instructions = IMPORTANT_INFO_PROMPT.format(
        question=question,
        messages=messages
    )
    # gf
    # Configuramos el LLM para obtener salida estructurada
    structured_llm = llm.with_structured_output(VehicleInfo)

    # Invocamos el modelo
    result = structured_llm.invoke([
        SystemMessage(content=system_instructions),
        HumanMessage(content="Extrae los puntos clave de la conversación")
    ])

    # Con reducers, simplemente devolvemos los resultados
    # La función reducer se encargará de preservar los valores existentes
    return {
        "vehicle_info": result,
    }


def generate_response(state: State) -> Dict[str, Any]:
    """
    Generate a response based on chat history, context, and summary.

    Args:
        state: The current state including user input, chat history, and context.

    Returns:
        Updated state with the generated answer.
    """
    try:
        llm = ChatOpenAI(model=LLM_MODEL)
        context = state["context"]
        summary = state["summary"]
        vehicle_info = state["vehicle_info"]
        user_query = state["input"]
        # Limitar la cantidad de mensajes en el historial
        recent_messages = state["messages"][-7:] if len(state["messages"]) > 7 else state["messages"]

        # Construir el mensaje del sistema con el contexto y resumen
        system_message = SALES_TALK_PROMPT.format(
            user_query=user_query,
            context=context,
            chat_history=summary,
            recent_messages=recent_messages,
            vehicle_info=vehicle_info
        )

        # Construir el prompt con historial y nuevo input
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])

        # Ejecutar la cadena del modelo
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "messages": state["messages"],
            "input": state["input"]
        })

        # Guardar la respuesta y actualizar el historial de chat
        # state["answer"] = response
        # state["messages"] += [
        #     HumanMessage(content=state["input"]),
        #     AIMessage(content=response)
        # ]
        updated_messages = state.get("messages", []) + [
            HumanMessage(content=state["input"]),
            AIMessage(content=response)
        ]
        logger.info(f"Generated response for input: {state['input'][:50]}...")

        return {
            "answer": response,
            "messages": updated_messages,
        }

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise Exception("I'm sorry, I encountered an error generating a response.")


def summarize_conversation(state: State) -> Dict[str, Any]:
    """
    Summarizes the conversation and removes old messages.

    Args:
        state: The current state including chat history.

    Returns:
        Updated state with summary and trimmed messages.
    """
    llm = ChatOpenAI(model=LLM_MODEL)

    summary = state.get("summary", "")
    summary_prompt = (
        f"This is the current summary: {summary}\nExtend it with the new messages:"
        if summary else "Create a summary of the conversation above:"
    )

    # Agregar el prompt al historial y ejecutar el resumen con el modelo
    messages = state["messages"] + [HumanMessage(content=summary_prompt)]
    response = llm.invoke(messages)

    # Eliminar todos los mensajes excepto los 2 más recientes
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

    return {"summary": response.content, "messages": delete_messages}


def human_feedback(state: State) -> Command:
    """
    Nodo de feedback humano para una conversación multi-turno.
    Espera la retroalimentación del usuario y actualiza el estado.
    Si el usuario escribe "done", "gracias" o "adiós", finaliza la conversación;
    en caso contrario, retorna al nodo de generación para continuar.
    """
    print("\n[human_feedback] Esperando retroalimentación del usuario...")

    # Utiliza interrupt() para pausar la ejecución y solicitar la entrada del usuario.
    user_input = interrupt({
        "answer": state["answer"],
        "message": "Proporcione su feedback o escriba 'done' para finalizar la conversación:"
    })
    print(f"[human_feedback] Feedback recibido: {user_input}")

    # Actualiza el historial de feedback; si no existe, inicialízalo.
    updated_feedback = state.get("feedback", []) + [user_input]

    # Actualiza el campo 'input' para que el siguiente turno (en generate_response) utilice el feedback.
    new_input = user_input

    # Si el usuario indica que quiere terminar la conversación,
    # redirige al nodo final (end_node).
    # Si el usuario indica que desea terminar la conversación, redirige al nodo final.
    if user_input.strip().lower() in ["done", "gracias", "adiós"]:
        return Command(update={"feedback": updated_feedback, "input": new_input}, goto="end_node")

    # En caso contrario, continúa el ciclo volviendo al nodo generate_response.
    return Command(update={"feedback": updated_feedback, "input": new_input}, goto="generate_response")

def end_node(state: State) -> Dict[str, Any]:
    """
    Nodo final para cerrar la conversación.

    Args:
        state: El estado actual de la conversación.

    Returns:
        Estado final con información de resumen.
    """
    logger.info("Conversation completed successfully.")
    return {
        "answer": f"Gracias por su consulta sobre vehículos Toyota. Esperamos haberle sido de ayuda.",
        "feedback": state.get("feedback", [])
    }