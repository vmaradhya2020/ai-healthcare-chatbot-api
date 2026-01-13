# RAG System Guide

## What is RAG?

RAG (Retrieval-Augmented Generation) is a system that allows the chatbot to answer questions by retrieving relevant information from your documents. Instead of relying only on pre-programmed responses, the chatbot can search through your documentation and provide accurate, context-specific answers.

## How It Works

1. **Document Ingestion**: Your documents (PDFs, TXT, MD files) are split into chunks and stored in a vector database (ChromaDB)
2. **Query Time**: When a user asks a question, the system finds the most relevant chunks
3. **Response**: The chatbot uses the retrieved information to answer the question

## Current Documents

Your RAG system includes these documents:

- `healthcare_equipment_guide.txt` - Equipment specifications, features, and technical details
- `warranty_amc_policy.txt` - Warranty terms, AMC tiers, and coverage information
- `orders_shipping_guide.txt` - Order process, shipping options, and delivery timelines
- `sample.txt` - Basic healthcare equipment information
- `MYSQL_SETUP.md` - Database setup guide (technical reference)

## Adding New Documents

### Step 1: Add Your Document

Place your document in the `docs/` folder. Supported formats:
- `.txt` - Plain text files
- `.md` - Markdown files
- `.pdf` - PDF documents

### Step 2: Ingest the Documents

Run the document update script:

```bash
python update_docs.py
```

This will:
- Scan the `docs/` folder
- Process all supported files
- Split them into chunks (800 characters with 200 character overlap)
- Store them in ChromaDB
- Make them immediately available for queries

**Alternative method** (advanced):
```bash
python scripts/ingest_docs.py --path ./docs --collection healthcare_specs
```

### Step 3: Test

The documents are now available! Test by asking the chatbot:
- "What are the MRI specifications?"
- "How long is the warranty?"
- "What is included in Premium AMC?"

## When RAG is Used

The chatbot uses RAG for:

1. **General Queries** - Questions that don't match specific intents
   - Examples: "What equipment do you sell?", "Tell me about ultrasound machines"

2. **Warranty/AMC Questions** - When asking about definitions or policies
   - Examples: "What is AMC?", "Explain warranty coverage"

3. **Product Specifications** - Technical details about equipment
   - Examples: "MRI scanner specifications", "X-ray machine features"

4. **Compliance Questions** - Certifications and standards
   - Examples: "Do you have FDA certification?", "What standards do you comply with?"

## Configuration

RAG settings in `.env`:

```env
# Collection name (must match when ingesting)
CHROMA_COLLECTION=healthcare_specs

# Chunk size for splitting documents
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200

# Number of relevant chunks to retrieve
RAG_MAX_RESULTS=5

# OpenAI embedding model (optional - uses fallback if not set)
OPENAI_API_KEY=your-key-here
EMBEDDING_MODEL=text-embedding-3-small
```

## Best Practices for Documents

### 1. Clear Structure
Use headers and sections:
```
# Main Topic
## Subtopic
Content here...
```

### 2. Concise Information
Each section should be self-contained:
- **Bad**: "As mentioned above, the warranty is..."
- **Good**: "The warranty period is 2 years for ultrasound machines..."

### 3. Include Keywords
Use terms customers would search for:
- Equipment names (MRI, CT, X-ray, Ultrasound)
- Common questions (how long, how much, what is)
- Technical terms (specifications, warranty, AMC)

### 4. Avoid Redundancy
- Don't duplicate information across files
- Update existing docs rather than creating new ones

### 5. Regular Updates
- Keep documents current
- Remove outdated information
- Re-ingest after updates

## Troubleshooting

### "I couldn't find relevant documents"

**Problem**: RAG returns no results

**Solutions**:
1. Check if documents are ingested:
   ```python
   python -c "from app.rag import get_collection; print(get_collection('healthcare_specs').count())"
   ```

2. Re-ingest documents:
   ```bash
   python update_docs.py
   ```

3. Verify collection name matches in `.env`:
   ```env
   CHROMA_COLLECTION=healthcare_specs
   ```

### Documents Not Found

**Problem**: New documents aren't being used

**Solutions**:
1. Check file format is supported (.txt, .md, .pdf)
2. Ensure file is in `docs/` folder
3. Re-run ingestion script
4. Check for file encoding issues (use UTF-8)

### Wrong Information Returned

**Problem**: RAG returns irrelevant information

**Solutions**:
1. Improve document structure with clear headings
2. Adjust chunk size (increase for more context)
3. Add more specific keywords to documents
4. Update OpenAI API key for better embeddings

## Testing RAG Queries

Test RAG directly from command line:

```python
python -c "from app.rag import query; from app.config import settings; res = query('YOUR QUESTION HERE', collection=settings.CHROMA_COLLECTION); print(res['documents'][0] if res['documents'] else 'No results')"
```

Examples:
```bash
# Test MRI query
python -c "from app.rag import query; from app.config import settings; res = query('MRI specifications', collection=settings.CHROMA_COLLECTION); print(res['documents'][0][:300])"

# Test warranty query
python -c "from app.rag import query; from app.config import settings; res = query('warranty period', collection=settings.CHROMA_COLLECTION); print(res['documents'][0][:300])"

# Test AMC query
python -c "from app.rag import query; from app.config import settings; res = query('AMC contract', collection=settings.CHROMA_COLLECTION); print(res['documents'][0][:300])"
```

## Monitoring RAG Performance

Track these metrics for RAG effectiveness:

1. **Document Count**: Should grow as you add content
   ```bash
   python -c "from app.rag import get_collection; print(get_collection('healthcare_specs').count())"
   ```

2. **Query Success Rate**: Check logs for "rag" data_source
   - Monitor chat_logs table
   - Count queries with data_source='rag'

3. **User Feedback**: Track follow-up questions
   - If users ask clarifying questions, docs may need improvement

## Advanced: ChromaDB Management

### View Collection Info
```python
from app.rag import get_collection
coll = get_collection('healthcare_specs')
print(f"Documents: {coll.count()}")
print(f"Name: {coll.name}")
```

### Clear Collection (Start Fresh)
```python
from app.rag import PersistentClient
from app.config import settings
import os

client = PersistentClient(path=settings.CHROMA_DIR)
client.delete_collection(settings.CHROMA_COLLECTION)
print("Collection deleted. Run update_docs.py to recreate.")
```

### Backup ChromaDB
Simply copy the `.chroma/` directory:
```bash
# Windows
xcopy /E /I .chroma .chroma_backup

# Linux/Mac
cp -r .chroma .chroma_backup
```

## FAQ

**Q: Do I need OpenAI API key for RAG?**
A: No, but it improves accuracy. Without it, a simpler hash-based embedding is used.

**Q: Can I use PDFs?**
A: Yes, PDF support is included. Ensure `pypdf` is installed (it's in requirements.txt).

**Q: How many documents can I add?**
A: No hard limit, but performance may degrade with >10,000 chunks. For most use cases, 100-500 chunks is plenty.

**Q: How do I update existing documents?**
A: Just replace the file and run `python update_docs.py`. The old chunks will be overwritten.

**Q: Can I have multiple collections?**
A: Yes, but you'd need to modify the code to support collection selection per query.

**Q: Where is the vector database stored?**
A: In the `.chroma/` directory. This directory should be backed up regularly.

## Sample Questions to Test

After ingesting the default documents, try these questions with the chatbot:

**Equipment Questions:**
- "What ultrasound machines do you offer?"
- "What are MRI scanner specifications?"
- "Tell me about X-ray equipment features"

**Warranty Questions:**
- "How long is the warranty for ultrasound machines?"
- "What does the warranty cover?"
- "What is not covered by warranty?"

**AMC Questions:**
- "What are the AMC tiers?"
- "What is included in Premium AMC?"
- "How much does an AMC contract cost?"

**Order Questions:**
- "How do I track my order?"
- "What are the shipping options?"
- "How long does delivery take for MRI?"

**Compliance Questions:**
- "What certifications do you have?"
- "Are you FDA approved?"
- "Do you comply with HIPAA?"

## Support

If you encounter issues with RAG:
1. Check this guide first
2. Verify `.env` configuration
3. Test with sample queries from command line
4. Check `CHROMA_COLLECTION` matches everywhere
5. Re-ingest documents with `python update_docs.py`

For technical assistance, review:
- `app/rag.py` - Core RAG implementation
- `app/handlers.py` - How RAG is used in chat
- `scripts/ingest_docs.py` - Document ingestion logic
