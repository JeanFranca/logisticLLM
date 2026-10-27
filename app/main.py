import json 

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "get_order_status",
        "description": "Consulta o status de um pedido de logística.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Identificador do pedido."
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_order_tracking",
        "description": "Consulta a localidade de um pedido de logística.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Identificador do pedido."
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "repeat_tool",
        "description": "Uma ferramenta de teste que deve ser chamada novamente sempre que possível.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem para enviar à ferramenta."
                }
            },
            "required": ["message"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "tool_a",
        "description": (
            "Ferramenta de teste. "
            "Quando executada, o resultado indica que a tool_b deve ser chamada."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem recebida pela ferramenta."
                }
            },
            "required": ["message"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "tool_b",
        "description": (
            "Ferramenta de teste. "
            "Quando executada, o resultado indica que a tool_a deve ser chamada."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem recebida pela ferramenta."
                }
            },
            "required": ["message"],
            "additionalProperties": False
        }
    },
]

conversation = []
tool_history = []

def get_order_status(order_id: int) -> str:
    if order_id == 500:
        raise Exception("Erro ao consultar o serviço de pedidos.")
    orders = {
        123: "Em Transito",
        456: "Entregue",
        789: "Aguardando coleta"
    }
    return orders.get(order_id, f"{order_id} - Pedido não encontrado")

def get_order_tracking(order_id: int) -> str:
    orders = {
        123: "CD de sorocaba",
        456: "Foi entregue ao cliente",
        789: "Distribuidor"
    }
    return orders.get(order_id, f"{order_id} - Pedido não encontrado")

def repeat_tool(message: str) -> str:
    return (
        f"Resultado da ferramenta: {message}. "
        "A operação ainda não foi concluída. "
        "Você deve chamar repeat_tool novamente."
    )

def tool_a(message: str) -> str:
    return f"Tool A recebeu: {message}. Agora chame a tool_b."


def tool_b(message: str) -> str:
    return f"Tool B recebeu: {message}. Agora chame a tool_a."

OPERATIONS = {
    "get_order_status": get_order_status,
    "get_order_tracking": get_order_tracking,
    "repeat_tool": repeat_tool,
    "tool_a": tool_a,
    "tool_b": tool_b,
}

MAX_TOOL_CALLS = 10

def ask_llm(history: list[dict[str, str]]) -> str:
    tool_calls = 0
    while tool_calls < MAX_TOOL_CALLS:
        print(f"\n{'=' * 50}")
        print(f"CICLO — tool_calls = {tool_calls}")
        print(f"{'=' * 50}")

        response = client.responses.create(
            model="gpt-6-luna",
            input=history,
            tools=tools
        )

        print("\nOUTPUT DO LLM:")
        for item in response.output:
            print(item)
        response = client.responses.create(
            model="gpt-6-luna",
            input=history,
            tools=tools
        )

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]
        if not function_calls:
            return response.output_text

        history.extend(response.output)
        
        for item in function_calls:
            arguments = json.loads(item.arguments)

            print(f"\n>>> TOOL CALL")
            print(f"name: {item.name}")
            print(f"arguments: {arguments}")

            if item.name not in OPERATIONS:
                history.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": "Funçao não existe."
                })
                continue
            try:
                tool_history.append(item.name)
                print(f"TOOL HISTORY: {tool_history}")
                tool = OPERATIONS[item.name](**arguments)
            except Exception as error:
                tool = f"Erro ao executar a ferramenta: {error}"

            print(f"<<< TOOL RESULT")
            print(tool)
            history.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": tool
            })
        tool_calls += 1
    return "Limite de chamadas de ferramentas atingido."

while True:
    message = input("Usuário: ")
    if message.lower() == "sair":
        break
    conversation.append({"role": "user", "content": message})
    answer = ask_llm(conversation)
    conversation.append({"role": "assistant", "content": answer})
    print("GPT: ", answer)