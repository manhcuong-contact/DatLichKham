import os
import json
import google.generativeai as genai

# =============================================================================
# CẤU HÌNH GEMINI API
# =============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def _get_model():
    """Khởi tạo model Gemini."""
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

# =============================================================================
# TASK 4.1: AI LỄ TÂN — PHÂN LOẠI TRIỆU CHỨNG
# =============================================================================
TRIAGE_PROMPT = """Bạn là một AI lễ tân bệnh viện thông minh. Nhiệm vụ của bạn:

1. Lắng nghe mô tả triệu chứng của bệnh nhân.
2. Phân tích và xác định chuyên khoa phù hợp nhất.
3. Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.

CÁC CHUYÊN KHOA CÓ SẴN trong hệ thống:
- Tim mạch (triệu chứng: đau ngực, khó thở, hồi hộp, tức ngực, tim đập nhanh, huyết áp cao, phù chân)
- Da liễu (triệu chứng: mẩn ngứa, nổi mụn, phát ban, dị ứng da, nấm da, rụng tóc, chàm, vẩy nến)
- Nhi khoa (triệu chứng: sốt cao, ho, sổ mũi, tiêu chảy, biếng ăn, quấy khóc, nôn trớ)
- Tai mũi họng (triệu chứng: đau họng, nghẹt mũi, ù tai, chảy máu mũi, khó nuốt, ho khan, viêm xoang)
- Nội tổng quát (triệu chứng: đau đầu, mệt mỏi, chóng mặt, đau bụng, buồn nôn, sốt nhẹ, mất ngủ, đau lưng)

QUY TẮC TRẢ LỜI:
- Luôn hỏi thêm nếu triệu chứng chưa rõ ràng.
- Đưa ra lời khuyên sơ bộ và gợi ý chuyên khoa.
- Cuối mỗi câu trả lời, LUÔN đính kèm một dòng JSON kết quả theo đúng định dạng sau:
  ```json
  {"specialty": "Tên chuyên khoa", "symptoms": "triệu chứng 1, triệu chứng 2", "urgency": "low/medium/high"}
  ```
- Nếu chưa đủ thông tin để phân loại, trả về: {"specialty": "Chưa xác định", "symptoms": "", "urgency": "low"}
"""

def ai_triage_chat(user_message, chat_history=None):
    """
    Gửi tin nhắn tới AI lễ tân để phân loại triệu chứng.
    
    Tham số:
        user_message (str): Tin nhắn/triệu chứng bệnh nhân nhập
        chat_history (list): Lịch sử hội thoại [{role, parts}]
    
    Trả về:
        (ai_response_text, parsed_json_or_None)
    """
    model = _get_model()
    if model is None:
        return "⚠️ Chưa cấu hình API Key Gemini. Vui lòng liên hệ quản trị viên.", None

    try:
        # Tạo chat session với lịch sử
        if chat_history:
            chat = model.start_chat(history=chat_history)
        else:
            chat = model.start_chat(history=[
                {"role": "user", "parts": [TRIAGE_PROMPT]},
                {"role": "model", "parts": ["Xin chào! Tôi là trợ lý AI lễ tân bệnh viện. Bạn hãy mô tả triệu chứng của mình, tôi sẽ giúp bạn tìm chuyên khoa phù hợp nhé! 😊"]},
            ])

        response = chat.send_message(user_message)
        ai_text = response.text

        # Thử trích xuất JSON từ phản hồi
        parsed_json = _extract_json(ai_text)

        return ai_text, parsed_json

    except Exception as e:
        return f"❌ Lỗi kết nối AI: {str(e)}", None


def _extract_json(text):
    """Trích xuất JSON object từ chuỗi phản hồi AI."""
    try:
        # Tìm chuỗi JSON trong phản hồi
        start = text.rfind('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end + 1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    return None


# =============================================================================
# TASK 4.2: RAG — HỎI ĐÁP TÀI LIỆU BỆNH VIỆN
# =============================================================================
HOSPITAL_DOCS_DIR = 'hospital_docs'

def _load_documents():
    """Đọc tất cả file .txt trong thư mục hospital_docs."""
    documents = []
    if not os.path.exists(HOSPITAL_DOCS_DIR):
        return documents

    for filename in os.listdir(HOSPITAL_DOCS_DIR):
        if filename.endswith('.txt'):
            filepath = os.path.join(HOSPITAL_DOCS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            documents.append({
                'filename': filename,
                'content': content
            })
    return documents


def _chunk_text(text, chunk_size=500, overlap=100):
    """Cắt nhỏ văn bản thành các đoạn (chunks) với overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _find_relevant_chunks(query, documents, top_k=3):
    """
    Tìm kiếm đoạn văn bản liên quan nhất tới câu hỏi.
    Sử dụng keyword matching đơn giản (không cần vector DB).
    """
    query_lower = query.lower()
    keywords = [kw.strip() for kw in query_lower.split() if len(kw.strip()) > 1]

    scored_chunks = []
    for doc in documents:
        chunks = _chunk_text(doc['content'])
        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for kw in keywords if kw in chunk_lower)
            if score > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'source': doc['filename'],
                    'score': score
                })

    # Sắp xếp theo score giảm dần, lấy top_k
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:top_k]


RAG_PROMPT_TEMPLATE = """Bạn là trợ lý AI của bệnh viện. Hãy trả lời câu hỏi của bệnh nhân dựa trên các tài liệu nội bộ bệnh viện được cung cấp bên dưới.

QUY TẮC:
- Chỉ trả lời dựa trên thông tin có trong tài liệu.
- Nếu tài liệu không chứa thông tin liên quan, hãy nói rõ: "Tôi không tìm thấy thông tin này trong tài liệu bệnh viện."
- Trả lời bằng tiếng Việt, thân thiện và dễ hiểu.
- Trích dẫn nguồn tài liệu nếu có.

TÀI LIỆU THAM KHẢO:
{context}

CÂU HỎI CỦA BỆNH NHÂN:
{question}
"""

def rag_answer(question):
    """
    Task 4.2: Hỏi đáp tài liệu bệnh viện bằng RAG.
    1. Đọc tài liệu từ hospital_docs/
    2. Tìm các đoạn liên quan bằng keyword matching
    3. Gửi đoạn context + câu hỏi lên Gemini để AI trả lời
    """
    model = _get_model()
    if model is None:
        return "⚠️ Chưa cấu hình API Key Gemini.", []

    documents = _load_documents()
    if not documents:
        return "📂 Chưa có tài liệu nào trong hệ thống. Vui lòng liên hệ quản trị viên.", []

    # Tìm đoạn văn bản liên quan
    relevant_chunks = _find_relevant_chunks(question, documents)

    if not relevant_chunks:
        return "Tôi không tìm thấy thông tin liên quan trong tài liệu bệnh viện. Vui lòng liên hệ trực tiếp quầy lễ tân.", []

    # Ghép context
    context = "\n\n---\n\n".join([
        f"[Nguồn: {c['source']}]\n{c['chunk']}" for c in relevant_chunks
    ])

    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    try:
        response = model.generate_content(prompt)
        sources = list(set(c['source'] for c in relevant_chunks))
        return response.text, sources
    except Exception as e:
        return f"❌ Lỗi AI: {str(e)}", []
