from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
#from fastapi.responses import HTMLResponse
import ollama
import asyncio
import json
import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime
import os
from typing import List, Dict, Any
import faiss
import pickle

app = FastAPI(title="Student Chatbot")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models and analyzers
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
sentiment_analyzer = SentimentIntensityAnalyzer()

# In-memory storage (replace with database later)
course_content = {}
chat_history = []
student_interactions = {}
wellbeing_flags = []

class WellbeingMonitor:
    def __init__(self):
        self.stress_keywords = [
            'overwhelmed', 'stressed', 'can\'t handle', 'too much', 'giving up',
            'impossible', 'hopeless', 'failing', 'behind', 'panic', 'anxiety'
        ]
        self.confusion_keywords = [
            'confused', 'don\'t understand', 'makes no sense', 'stuck',
            'lost', 'help', 'struggling', 'difficult', 'hard'
        ]
    
    def analyze_message(self, message: str, student_id: str) -> Dict[str, Any]:
        # Sentiment analysis
        blob = TextBlob(message)
        vader_scores = sentiment_analyzer.polarity_scores(message)
        
        # Keyword detection
        message_lower = message.lower()
        stress_count = sum(1 for keyword in self.stress_keywords if keyword in message_lower)
        confusion_count = sum(1 for keyword in self.confusion_keywords if keyword in message_lower)
        
        # Calculate wellbeing score (0-10, lower is concerning)
        base_score = 5
        sentiment_adjustment = (vader_scores['compound'] + 1) * 2.5  # Scale to 0-5
        stress_penalty = stress_count * 1.5
        confusion_penalty = confusion_count * 0.5
        
        wellbeing_score = max(0, base_score + sentiment_adjustment - stress_penalty - confusion_penalty)
        
        analysis = {
            'timestamp': datetime.datetime.now().isoformat(),
            'student_id': student_id,
            'message': message,
            'sentiment': {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'vader': vader_scores
            },
            'wellbeing_score': wellbeing_score,
            'stress_indicators': stress_count,
            'confusion_indicators': confusion_count,
            'flag_for_review': wellbeing_score < 3.0 or stress_count > 2
        }
        
        if analysis['flag_for_review']:
            wellbeing_flags.append(analysis)
            print(f"⚠️  WELLBEING FLAG: Student {student_id} scored {wellbeing_score:.1f}")
        
        return analysis

wellbeing_monitor = WellbeingMonitor()

class CourseKnowledgeBase:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.index = None
    
    def add_document(self, content: str, source: str):
        # Split into chunks for better retrieval
        chunks = self.chunk_text(content, 500)
        for i, chunk in enumerate(chunks):
            self.documents.append({
                'content': chunk,
                'source': source,
                'chunk_id': i
            })
            embedding = sentence_model.encode([chunk])[0]
            self.embeddings.append(embedding)
        
        # Build FAISS index
        if self.embeddings:
            embeddings_array = np.array(self.embeddings)
            self.index = faiss.IndexFlatIP(embeddings_array.shape[1])
            self.index.add(embeddings_array)
    
    def chunk_text(self, text: str, chunk_size: int) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self.index:
            return []
        
        query_embedding = sentence_model.encode([query])
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(score)
                results.append(doc)
        
        return results

knowledge_base = CourseKnowledgeBase()

@app.post("/upload_syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    
    try:
        content = await file.read()
        
        if file.filename.endswith('.pdf'):
            # Extract text from PDF
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            text = content.decode('utf-8')
        
        knowledge_base.add_document(text, file.filename)
        return {"message": f"Successfully uploaded {file.filename}"}
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/wellbeing_dashboard")
async def get_wellbeing_dashboard():
    return {
        "total_flags": len(wellbeing_flags),
        "recent_flags": [flag for flag in wellbeing_flags if 
                        datetime.datetime.fromisoformat(flag['timestamp']) > 
                        datetime.datetime.now() - datetime.timedelta(days=7)],
        "student_summary": {}
    }

@app.websocket("/ws/{student_id}")
async def websocket_endpoint(websocket: WebSocket, student_id: str):
    await websocket.accept()
    
    if student_id not in student_interactions:
        student_interactions[student_id] = []
    
    try:
        while True:
            # Receive message from student
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get('message', '')
            
            # Log interaction
            interaction = {
                'timestamp': datetime.datetime.now().isoformat(),
                'student_id': student_id,
                'message': user_message,
                'type': 'user'
            }
            student_interactions[student_id].append(interaction)
            chat_history.append(interaction)
            
            # Analyze wellbeing
            wellbeing_analysis = wellbeing_monitor.analyze_message(user_message, student_id)
            
            # Search knowledge base for relevant content
            relevant_docs = knowledge_base.search_similar(user_message)
            context = "\n".join([doc['content'] for doc in relevant_docs[:2]])
            
            # Generate response using Ollama
            prompt = f"""You are a helpful academic assistant for undergraduate students in C++ programming and algorithms courses.

Context from course materials:
{context}

Student question: {user_message}

Please provide a helpful, encouraging response. If the question is about course content, use the context provided. If it's about programming, provide clear explanations and examples. Always be supportive and understanding of student stress.

Response:"""

            try:
                response = ollama.generate(
                    model='llama3.1:8b',
                    prompt=prompt,
                    stream=False
                )
                bot_response = response['response']
                
            except Exception as e:
                bot_response = "I'm sorry, I'm having trouble processing your request right now. Please try again or contact your instructor."
            
            # Log bot response
            bot_interaction = {
                'timestamp': datetime.datetime.now().isoformat(),
                'student_id': student_id,
                'message': bot_response,
                'type': 'bot',
                'wellbeing_score': wellbeing_analysis['wellbeing_score']
            }
            student_interactions[student_id].append(bot_interaction)
            chat_history.append(bot_interaction)
            
            # Send response back to student
            await websocket.send_text(json.dumps({
                'message': bot_response,
                'wellbeing_score': wellbeing_analysis['wellbeing_score'],
                'flagged': wellbeing_analysis['flag_for_review']
            }))
            
    except WebSocketDisconnect:
        print(f"Student {student_id} disconnected")

# Serve static files (HTML frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def get_homepage():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)