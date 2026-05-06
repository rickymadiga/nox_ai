from .agent import PreprocessorAgent

def register(runtime):

    agent = PreprocessorAgent()

    runtime.register_agent("preprocessor", agent)

    runtime.register_capability(
        agent_name="preprocessor",
        intent="preprocess",
        keywords=[
            "preprocess",
            "clean data",
            "prepare data",
            "data preprocessing"
        ]
    )