from dependency_injector import containers, providers
from langchain_openai import OpenAIEmbeddings
from llm.vector_store import VectorStoreManager
from llm.extract import split_chain, summarize_chain, section_chain
from llm.extract import ContentExtractor
from dotenv import load_dotenv
import os
from llm.recommend import QueryInfoExtractor
from llm.result_filter import RerankFilter

load_dotenv()


from typing import Callable, Dict
class ChainRegistry:
   _chains: Dict[str, Callable] = {
       "section": section_chain,
       "split": split_chain,
       "summarize": summarize_chain
   }
   @classmethod
   def get_chain(cls, chain_name: str) -> Callable:
       if chain_name not in cls._chains:
           raise ValueError(f"Unknown chain: {chain_name}")
       return cls._chains[chain_name]

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["main"])
    config = providers.Configuration(yaml_files=["config.yml"])
    

    # content_extractor = providers.Factory(
    #     ContentExtractor,
    #     chain=ChainRegistry.get_chain(config.chain_type.as_str())
    # )

    embeddings = providers.Factory(
        OpenAIEmbeddings,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    vector_store_manager = providers.Factory(
        VectorStoreManager,
        embeddings=embeddings,
        persist_directory=config.vector_store_path
    )

    query_info_extractor = providers.Factory(
        QueryInfoExtractor,
        llm=llm,
        result_filter=RerankFilter()
    )
