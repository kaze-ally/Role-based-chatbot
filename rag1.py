from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_community.document_loaders import UnstructuredURLLoader, UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import  Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

load_dotenv()



VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "Role_Based"
llm = None
vector_store = None

# Initialize components for the RAG system
# This includes the LLM and vector store for document retrieval and processing
def initialize_components():
    global llm, vector_store
    
    if llm is None:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=2000
        )
        print("LLM initialized successfully")
    
    if vector_store is None:
        ef = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"trust_remote_code": True}
        )
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=ef,
            persist_directory=str(VECTORSTORE_DIR)
        )
        print("Embeddings initialized successfully")
        
    
# Check access rights based on the user's position
# This function returns a list of folders the user can access based on their position
def check_access(position):
    access_rights = {
        'finance': ['finance', 'marketing', 'general'],
        'marketing': ['marketing'],
        'hr': ['hr'],
        'engineering': ['engineering'],
        'executive': ['marketing', 'finance', 'general', 'hr', 'engineering'],
        "employee": ['general']
    }
    position = position.lower()
    if position in access_rights:
        return access_rights[position]
    return []

# Return documents based on the user's position
# This function loads documents from the allowed folders based on the user's position
def return_docs(position):
    global vector_store

    allowed_folders = check_access(position)
    if not allowed_folders:
        print("Invalid position or no access rights.")
        return []
    
    print(f"Access granted to folders: {', '.join(allowed_folders)}")
    
    initialize_components()

    all_docs = []
    # Set base path directly
    base_path = Path("F:\python\DS-RPC-01\data")
    
    print(f"Base path set to: {base_path}")

    # Only load documents from allowed folders
    for folder in allowed_folders:
        folder_path = base_path / folder
        print(f"Checking folder: {folder_path} - Exists: {folder_path.exists()}")
        
        if folder_path.exists():
            # List all files in the folder
            all_files = list(folder_path.glob("*"))
            print(f"Files in {folder}: {[f.name for f in all_files]}")
            for file in all_files:
                if file.suffix in ['.md', '.csv']:
                    loader = UnstructuredFileLoader(file)
                    docs = loader.load()
                    all_docs.extend(docs)
    return all_docs


# Split documents into smaller chunks for processing
# This function uses RecursiveCharacterTextSplitter to split documents into manageable chunks
def split_documents(docs, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_documents(docs)

# Process documents by splitting them into chunks and adding to the vector store
# This function checks if there are documents to process, splits them, and adds them to the vector store
def process_docs(all_docs):
    if all_docs:
        split_docs = split_documents(docs=all_docs, chunk_size=1000, chunk_overlap=200)
        print(f"Split into {len(split_docs)} chunks.")
        
        uuids = [str(uuid4()) for _ in range(len(split_docs))]
        vector_store.add_documents(split_docs, ids=uuids)
        print("Documents processed and added to vector store.")
    else:
        print("No documents to process.")

# Generate an answer based on a query using the vector store
# This function retrieves relevant documents from the vector store and generates an answer using the LLM
def generate_answer(query):
    if not vector_store:
        raise RuntimeError("Vector database is not initialized")
    
    chain = RetrievalQAWithSourcesChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever()
    )
    result = chain.invoke({"question": query}, return_only_outputs=True)
    sources = result.get("sources", "")
    
    return result['answer'], sources


if __name__ == "__main__":
    initialize_components()
    position = "finance"  
    all_docs = return_docs(position)
    
    if all_docs:
        process_docs(all_docs)
    else:
        print("No documents found for the given position.")
        
    query = "What is the budget for the marketing department?"
    answer, sources = generate_answer(query)
    print(f"Answer: {answer}")
    print(f"Sources: {sources}")
