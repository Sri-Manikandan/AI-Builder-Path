import os

from langfuse.langchain import CallbackHandler


def get_langfuse_handler():
    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not os.environ.get("LANGFUSE_SECRET_KEY"):
        print("LangFuse keys not set - running without tracing.")
        return None
    return CallbackHandler()
