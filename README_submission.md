# Báo cáo Nộp bài Lab 17 - Multi-Memory Agent

## 1. Ba câu hỏi cốt lõi
- **Layer quan trọng nhất:** **Long-term Memory** (chiếm 4/11 case: E02, E03, E08, E09 và 1 phần E07). Layer này quản lý preferences, open-loops/deadlines, xử lý cập nhật recency và cô lập dữ liệu người dùng qua nhiều session.
- **Trade-off Zep Context Block vs Redis+Qdrant:**
  - *Zep Context Block:* Tự động trích xuất fact, liên kết entity graph, quản lý temporal validity (recency) và tự động đóng gói context block tối ưu token budget.
  - *Redis+Qdrant:* Độ trễ cực thấp (0.1ms KV / 5-10ms vector) và toàn quyền kiểm soát dữ liệu on-premise, nhưng tốn nhiều chi phí tự code chunking, deduplication, conflict resolution và cross-session state.
- **Guardrail chống Memory Poisoning:**
  1. *Provenance Tagging:* Gắn nhãn nguồn (user vs system vs tool) và timestamp; không cho user prompt ghi đè system rules.
  2. *Input Sanitization & Redaction:* Lọc PII và injection patterns trước khi đưa vào durable storage.
  3. *Reconciliation/Audit:* Sử dụng heartbeat script định kỳ quét và dọn dẹp các tri thức/quan hệ bất thường.

## 2. Phân tích kết quả Benchmark
1. **Layer hit rate thấp nhất:** Long-term, Episodic và Semantic đều đạt 0% ở `no_memory` (chỉ Short-term đạt 100% nhờ local context).
2. **Query nhiều token nhất:** Case **E03** (`1406 tokens`) và **E08** (`1399 tokens`) do Context Block truy xuất danh sách facts quan hệ và user summary chi tiết.
3. **Case Mixed (E07):** Cần kết hợp **Long-term** (preference Minh: `Python`) và **Semantic** (policy retry: `Idempotency-Key`).
4. **Token reduction vs Hit rate:** `no_memory` có reduction cao (81.8%) do không truy xuất gì, dẫn đến hit rate rất thấp (18.2%). Token reduction chỉ có giá trị khi đi kèm hit rate cao (student đạt 100% với 14.2% reduction).

## 3. Recency & Compaction
- **E08 (Recency):** Zep ưu tiên fact mới nhất (`BLUEBIRD-42` dùng `TypeScript` + `NestJS`) ghi đè preference `Python` cũ nhưng vẫn lưu vết lịch sử.
- **E10 (Compaction):** Sliding window kết hợp summary và durable notes giữ nguyên vẹn constraint `REVIEW-DEADLINE-1600` (Friday 16:00) dù message raw đã bị evict.
