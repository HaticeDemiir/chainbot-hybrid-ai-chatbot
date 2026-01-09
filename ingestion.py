import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import fitz
from langchain.schema import Document


load_dotenv()


urls = [
    "https://corporate.lcwaikiki.com/hakkimizda",
    "https://corporate.lcwaikiki.com/ekoloji",
    "https://corporate.lcwaikiki.com/urun-kalite-testleri",
    "https://akademi.lcwaikiki.com/blog/article/6125",
    "https://corporate.lcwaikiki.com/kariyer-firsatlari",
    "https://www.lcw.com/site-haritasi",
    "https://www.lcw.com/yardim/siparis-islemleri",
    "https://www.lcwaikiki.de/tr-TR/DE/yardim/8",
    "https://www.lcw.com/yardim/siparis-islemleri/siparisimi-iptal-edebilir-misiniz",

]

docs_list = []
for url in urls:
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        docs_list.extend(docs)
    except Exception as e:
        print(f"{url} yüklenirken hata oluştu: {e}")


pdf_paths = [
    "data/Beden.pdf",
    "data/MagazaBilgisi.pdf",
    "data/SSS.pdf"
]

pdf_docs = []
for path in pdf_paths:
    try:
        doc = fitz.open(path)
        text = "\n".join([page.get_text() for page in doc])
        pdf_docs.append(Document(page_content=text, metadata={"source": path}))
    except Exception as e:
        print(f" {path} yüklenirken hata oluştu: {e}")



csv_docs = []
try:
    csv_loader = CSVLoader(file_path="data/train-00000-of-00001.csv")
    csv_docs = csv_loader.load()
except Exception as e:
    print(f" CSV dosyası yüklenirken hata oluştu: {e}")




all_docs = docs_list + pdf_docs + csv_docs


text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=500,
    chunk_overlap=50
)

doc_splits = text_splitter.split_documents(all_docs)


vectorstore = Chroma.from_documents(
     documents=doc_splits,
     collection_name="rag-chroma",
     embedding=OpenAIEmbeddings(),
     persist_directory="./.chroma",
 )


retriever = Chroma(
    collection_name="rag-chroma",
    persist_directory="./.chroma",
    embedding_function=OpenAIEmbeddings(),
).as_retriever()

print("Veri başarıyla yüklendi ve Chroma'ya kaydedildi.")
