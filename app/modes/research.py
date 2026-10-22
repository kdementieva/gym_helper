from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.tools import tavily


llm = get_llm(temperature=0.2)


class AgentState(TypedDict):
    goal: str
    steps: List[str]
    completed_tasks: List[str]
    finished: bool
    iteration: int
    final_answer: str
    language: str


async def plan(state: AgentState) -> AgentState:
    goal = state["goal"]
    completed_tasks = state["completed_tasks"]

    messages = [
        SystemMessage(content="""
        You are a planner.

        Break the goal into 4 to 6 distinct research tasks.
        Each task should require finding information on the web.

        Do not create duplicate or overlapping tasks.
        Do not create tasks that are already listed in completed_tasks.
        Only create tasks that are still necessary to achieve the goal.
        """),
        HumanMessage(
            content=f"""
            My goal is: {goal}

            Completed tasks:
            {completed_tasks}
            """
        ),
    ]

    response = await llm.ainvoke(messages)

    steps = [
        step.strip()
        for step in response.content.split("\n")
        if step.strip()
    ]

    return {
        "goal": goal,
        "steps": steps,
        "completed_tasks": completed_tasks,
        "finished": state["finished"],
        "iteration": state["iteration"],
        "final_answer": state["final_answer"],
        "language": state["language"],
    }


async def execute(state: AgentState) -> AgentState:
    steps = state["steps"]
    completed = []
    completed_tasks = state["completed_tasks"].copy()

    for step in steps:
        search_result = await tavily.ainvoke({
            "query": step
        })

        messages = [
            SystemMessage(content="""
            You are a fitness research assistant.

            Analyze the search results and make a clear,
            practical conclusion for the given task.
            """),
            HumanMessage(content=f"""
            Task:
            {step}

            Search results:
            {search_result}
            """),
        ]

        response = await llm.ainvoke(messages)

        completed.append(
            f"{step}\n-> {response.content}"
        )

        completed_tasks.append(step)

    return {
        "goal": state["goal"],
        "steps": completed,
        "completed_tasks": completed_tasks,
        "finished": state["finished"],
        "iteration": state["iteration"],
        "final_answer": state["final_answer"],
        "language": state["language"],
    }


async def reflect(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(content="""
        You are a reflector.

        Evaluate whether the goal has been sufficiently achieved
        based on the completed research.

        If enough information has been collected to create the
        final answer, answer FINISH.

        Otherwise answer CONTINUE and briefly explain what is missing.
        """),
        HumanMessage(
            content="\n".join(state["steps"])
        ),
    ]

    response = await llm.ainvoke(messages)
    result = response.content

    finished = "FINISH" in result.upper()

    return {
        "goal": state["goal"],
        "steps": state["steps"] + [
            f"Reflection:\n{result}"
        ],
        "completed_tasks": state["completed_tasks"],
        "finished": finished,
        "iteration": state["iteration"] + 1,
        "final_answer": state["final_answer"],
        "language": state["language"],
    }


async def finalize(state: AgentState) -> AgentState:
    language = state["language"]

    messages = [
        SystemMessage(content=f"""
        You are Gym Helper, a personal fitness assistant.

        Create the final answer based on the completed research.

        The user's preferred language is {language}.
        Write the entire final answer in {language},
        unless the user explicitly requested another language.

        Make the answer clear, practical, and easy to read.
        Do not invent facts that were not found during the research.
        Do not mention internal research tasks, planning,
        reflection, tools, agents, or implementation details.

        Use plain text suitable for Telegram.
        """),
        HumanMessage(content=f"""
        User's question:
        {state["goal"]}

        Completed research:
        {"\n\n".join(state["steps"])}
        """),
    ]

    response = await llm.ainvoke(messages)

    final_answer = response.content

    return {
        "goal": state["goal"],
        "steps": state["steps"],
        "completed_tasks": state["completed_tasks"],
        "finished": True,
        "iteration": state["iteration"],
        "final_answer": final_answer,
        "language": state["language"],
    }


def should_continue(state: AgentState) -> str:
    if state["finished"]:
        return "finalize"

    if state["iteration"] >= 3:
        return "finalize"

    return "continue"


workflow = StateGraph(AgentState)

workflow.add_node("plan", plan)
workflow.add_node("execute", execute)
workflow.add_node("reflect", reflect)
workflow.add_node("finalize", finalize)

workflow.set_entry_point("plan")

workflow.add_edge("plan", "execute")
workflow.add_edge("execute", "reflect")

workflow.add_conditional_edges(
    "reflect",
    should_continue,
    {
        "continue": "plan",
        "finalize": "finalize",
    },
)

workflow.add_edge("finalize", END)

graph = workflow.compile()