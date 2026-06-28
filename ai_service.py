import os
import json
import requests

# =============================================================================
# CẤU HÌNH GEMINI API
# =============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# =============================================================================
# RAG NỘI BỘ
# =============================================================================
HOSPITAL_DOCS_DIR = 'hospital_docs'

def _load_documents():
    documents = []
    if not os.path.exists(HOSPITAL_DOCS_DIR):
        return documents
    for filename in os.listdir(HOSPITAL_DOCS_DIR):
        if filename.endswith('.txt'):
            filepath = os.path.join(HOSPITAL_DOCS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            documents.append({'filename': filename, 'content': content})
    return documents

def _chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def _find_relevant_chunks(query, documents, top_k=3):
    query_lower = query.lower()
    keywords = [kw.strip() for kw in query_lower.split() if len(kw.strip()) > 1]
    scored_chunks = []
    for doc in documents:
        chunks = _chunk_text(doc['content'])
        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for kw in keywords if kw in chunk_lower)
            if score > 0:
                scored_chunks.append({'chunk': chunk, 'source': doc['filename'], 'score': score})
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:top_k]

def _extract_json(text):
    try:
        start = text.rfind('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end + 1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    return None

# =============================================================================
# UNIFIED AI ASSISTANT
# =============================================================================
UNIFIED_SYSTEM_PROMPT = """Bạn là "Trợ lý AI phòng khám", một trí tuệ nhân tạo chuyên nghiệp, thân thiện và tận tâm.

QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT):

1. GIỚI HẠN PHẠM VI (RẤT QUAN TRỌNG):
Nếu người dùng hỏi những vấn đề KHÔNG liên quan đến y tế, sức khỏe, hoặc dịch vụ phòng khám (ví dụ: lập trình, toán học, nấu ăn, thời tiết, chính trị...), bạn PHẢI TỪ CHỐI lịch sự. 
Cách trả lời: "Xin lỗi, câu hỏi này nằm ngoài phạm vi hỗ trợ của tôi. Tôi chỉ có thể giúp bạn các vấn đề liên quan đến y tế và dịch vụ khám chữa bệnh."

2. HỎI ĐÁP DỊCH VỤ phòng khám:
Nếu người dùng hỏi về bảng giá, quy trình, thủ tục, hãy TÌM CÂU TRẢ LỜI TRONG [TÀI LIỆU NỘI BỘ phòng khám] (được gửi kèm ở mỗi tin nhắn nếu có).
- Nếu tài liệu không có đề cập, hãy nói: "Tôi không tìm thấy thông tin này trong tài liệu phòng khám. Vui lòng liên hệ quầy lễ tân."

3. TƯ VẤN TRIỆU CHỨNG BỆNH (TRIAGE):
Nếu người dùng mô tả triệu chứng bệnh, hãy phân tích và ĐỀ XUẤT CHUYÊN KHOA PHÙ HỢP.
- Danh sách chuyên khoa có sẵn: Tim mạch, Da liễu, Nhi khoa, Tai mũi họng, Nội tổng quát.
- ĐẶC BIỆT: Khi tư vấn triệu chứng, bạn LUÔN phải đặt một khối mã JSON ở DÒNG CUỐI CÙNG của câu trả lời theo đúng định dạng sau:
```json
{"specialty": "Tên chuyên khoa", "symptoms": "triệu chứng 1, triệu chứng 2", "urgency": "low/medium/high"}
```
(Nếu không đủ thông tin, specialty là "Chưa xác định").
"""

def unified_ai_chat(user_message, chat_history=None):
    """
    Xử lý chung toàn bộ logic RAG và Triage qua một kênh hội thoại duy nhất.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Chưa cấu hình API Key Gemini. Vui lòng liên hệ quản trị viên.", None

    # Lấy tài liệu RAG tương ứng với câu hỏi
    documents = _load_documents()
    relevant_chunks = _find_relevant_chunks(user_message, documents)
    
    context_text = "Không tìm thấy tài liệu nội bộ nào liên quan."
    if relevant_chunks:
        context_text = "\n\n---\n\n".join([f"[Nguồn: {c['source']}]\n{c['chunk']}" for c in relevant_chunks])

    # Khởi tạo history nếu chưa có
    if not chat_history:
        chat_history = [
            {"role": "user", "parts": [{"text": UNIFIED_SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": "Xin chào! Tôi là Trợ lý AI phòng khám. Tôi có thể giúp gì cho bạn hôm nay?"}]}
        ]

    # Normalize chat history to strict REST format
    formatted_history = []
    for msg in chat_history:
        formatted_parts = []
        for part in msg.get("parts", []):
            if isinstance(part, str):
                formatted_parts.append({"text": part})
            elif isinstance(part, dict) and "text" in part:
                formatted_parts.append(part)
        formatted_history.append({"role": msg["role"], "parts": formatted_parts})

    # Đóng gói user_message cùng với context
    user_prompt_with_context = f"""[TÀI LIỆU NỘI BỘ phòng khám TÌM ĐƯỢC CHO CÂU HỎI NÀY]:
{context_text}

[TIN NHẮN TỪ BỆNH NHÂN]:
{user_message}
"""

    # Tạo request payload
    payload = {
        "contents": formatted_history + [
            {"role": "user", "parts": [{"text": user_prompt_with_context}]}
        ]
    }
    
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    try:
        # Giới hạn thời gian kết nối là 15 giây để tránh treo UI
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        
        if resp.status_code == 429:
            return "⚠️ Hệ thống AI đang quá tải (Hết hạn ngạch miễn phí). Vui lòng thử lại sau ít phút.", None
        elif resp.status_code != 200:
            return f"❌ Lỗi từ server AI ({resp.status_code}): {resp.text}", None
            
        data = resp.json()
        
        try:
            ai_text = data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "❌ AI không phản hồi đúng định dạng.", None

        # Trích xuất JSON (nếu có)
        parsed_json = _extract_json(ai_text)
        if parsed_json:
            # Xóa khối JSON khỏi văn bản hiển thị cho người dùng
            start = ai_text.rfind('{')
            if start != -1:
                block_start = ai_text.rfind('```', 0, start)
                if block_start != -1:
                    ai_text = ai_text[:block_start].strip()
                else:
                    ai_text = ai_text[:start].strip()

        return ai_text, parsed_json

    except requests.exceptions.Timeout:
        return "⏳ AI phản hồi quá lâu. Vui lòng thử lại sau.", None
    except Exception as e:
        return f"❌ Lỗi kết nối AI: {str(e)}", None
