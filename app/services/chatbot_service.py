import time
import uuid
import json
import boto3
import logging
from datetime import datetime


def _get_xray_trace_header() -> str:
    """현재 OTEL span의 trace context를 X-Amzn-Trace-Id 형식으로 반환."""
    try:
        from opentelemetry import trace as otel_trace
        span = otel_trace.get_current_span()
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return ""
        trace_hex = format(ctx.trace_id, '032x')
        span_hex = format(ctx.span_id, '016x')
        sampled = "1" if ctx.trace_flags.sampled else "0"
        return f"Root=1-{trace_hex[:8]}-{trace_hex[8:]};Parent={span_hex};Sampled={sampled}"
    except Exception:
        return ""


_chatbot_logger = logging.getLogger(__name__)


def _send_xray_segment(start_time: float, end_time: float, success: bool) -> None:
    """
    ECS cdci-prd-chatbot → AgentCore cdci-prd-supervisor-agent 호출을 X-Ray에 기록.
    OTEL sidecar의 awsxrayreceiver(UDP 2000)를 통해 전송 → OTEL sidecar가 X-Ray API로 forwarding.
    """
    import socket
    try:
        trace_id = f"1-{int(start_time):08x}-{uuid.uuid4().hex[:24]}"
        segment = {
            "id": uuid.uuid4().hex[:16],
            "name": "cdci-prd-chatbot",
            "trace_id": trace_id,
            "start_time": start_time,
            "end_time": end_time,
            "fault": not success,
            "origin": "AWS::ECS::Fargate",
            "subsegments": [{
                "id": uuid.uuid4().hex[:16],
                "name": "cdci-prd-supervisor-agent",
                "start_time": start_time,
                "end_time": end_time,
                "namespace": "remote",
                "fault": not success,
            }],
        }
        header = b'{"format": "json", "version": 1}\n'
        doc = header + json.dumps(segment).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(doc, ("127.0.0.1", 2000))
        finally:
            sock.close()
    except Exception as exc:
        _chatbot_logger.warning("X-Ray UDP send failed: %s", exc)
from app.repositories.chatbot_repository import ChatbotRepository
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatMessage
from app.core.config import settings
from app.services.user_client import get_codef_data
from app.core.metrics import put_metric

class ChatbotService:
    def __init__(self):
        self._repository = None
        self._boto_session = boto3.Session(region_name=settings.aws_region)

    @property
    def repository(self):
        if self._repository is None:
            self._repository = ChatbotRepository()
        return self._repository

    def send_message(self, request: ChatMessageRequest, token: str) -> ChatMessageResponse:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        conversation_id = request.result_id

        history = self.repository.get_conversation(request.cognito_id, conversation_id) or {"messages": []}
        history["messages"].append({"type": "user", "content": request.message, "timestamp": timestamp})
        
        chat_history = f"사용자: {request.message}"
        codef_data = get_codef_data(request.cognito_id, token)
        bot_message = self._call_supervisor(
            request.cognito_id,
            conversation_id,
            chat_history,
            codef_data["codef_health_data"],
            codef_data["codef_medication_info"]
        )
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'

        history["messages"].append({"type": "bot", "content": bot_message, "timestamp": bot_timestamp})
        history["conversation_id"] = conversation_id
        history["cognito_id"] = request.cognito_id
        history["last_activity"] = bot_timestamp  # 마지막 활동 시간 추적
        self.repository.save_conversation(request.cognito_id, conversation_id, history)

        return ChatMessageResponse(bot_message=bot_message, timestamp=bot_timestamp)

    def get_history(self, result_id: str, cognito_id: str) -> ChatHistoryResponse:
        data = self.repository.get_conversation(cognito_id, result_id)
        if not data:
            return ChatHistoryResponse(result_id=result_id, messages=[])
        messages = [
            ChatMessage(type=msg['type'], content=msg['content'], timestamp=msg['timestamp'])
            for msg in data.get('messages', [])
        ]
        return ChatHistoryResponse(result_id=result_id, messages=messages)

    def end_session(self, cognito_id: str, conversation_id: str):
        """세션 종료 시 Redis → S3 동기화"""
        self.repository.sync_to_s3(cognito_id, conversation_id)

    def _build_chat_history(self, messages: list) -> str:
        lines = []
        for msg in messages:
            role = "사용자" if msg["type"] == "user" else "봇"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def _call_supervisor(
        self,
        cognito_id: str,
        chat_result_id: str,
        chat_history: str,
        codef_health_data: dict | None,
        codef_medication_info: list | None
    ) -> str:
        import logging
        logger = logging.getLogger(__name__)
        
        if settings.supervisor_agent_arn == "placeholder":
            return "Supervisor Agent ARN이 설정되지 않았습니다."
        
        payload = {
            "cognito_id": cognito_id,
            "chat_result_id": int(chat_result_id),
            "codef_health_data": codef_health_data or {},
            "codef_medication_info": codef_medication_info or [],
            "chat_history": chat_history,
            "_xray_trace": _get_xray_trace_header(),
        }
        
        logger.info(f"[{cognito_id}] Supervisor Agent 호출 시작: ARN={settings.supervisor_agent_arn}")
        
        # HTTP URL이면 직접 호출 (로컬 테스트용)
        if settings.supervisor_agent_arn.startswith("http"):
            import httpx
            response = httpx.post(
                settings.supervisor_agent_arn + "/invocations",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("response", "")
        
        # AgentCore ARN이면 boto3 호출 (실제 배포용)
        start = time.time()
        success = False
        try:
            from botocore.config import Config
            client = self._boto_session.client(
                "bedrock-agentcore",
                config=Config(read_timeout=300, connect_timeout=10),
            )
            response = client.invoke_agent_runtime(
                agentRuntimeArn=settings.supervisor_agent_arn,
                payload=json.dumps(payload, ensure_ascii=False),
            )
            raw = response["response"].read()
            result = json.loads(raw)
            logger.info(f"[{cognito_id}] Supervisor Agent 응답 성공")
            put_metric("agent_invocation_total", 1, extra_dims=[{"Name": "status", "Value": "success"}])
            put_metric("agent_latency_seconds", time.time() - start, unit="Seconds")
            success = True
            return result.get("response", "")
        except Exception as e:
            logger.error(f"[{cognito_id}] Supervisor Agent 호출 실패: {type(e).__name__}: {e}")
            logger.error(f"[{cognito_id}] ARN: {settings.supervisor_agent_arn}")
            logger.error(f"[{cognito_id}] Payload keys: {list(payload.keys())}")
            put_metric("agent_invocation_total", 1, extra_dims=[{"Name": "status", "Value": "error"}])
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        finally:
            end = time.time()
            _send_xray_segment(start, end, success=success)
            try:
                from opentelemetry import trace as otel_trace
                from opentelemetry.context import Context
                tracer = otel_trace.get_tracer(__name__)
                root = tracer.start_span(
                    "cdci-prd-chatbot",
                    context=Context(),
                    kind=otel_trace.SpanKind.SERVER,
                    start_time=int(start * 1e9),
                    attributes={"http.method": "POST", "http.route": "/chat/message"},
                )
                root_ctx = otel_trace.set_span_in_context(root)
                child = tracer.start_span(
                    "cdci-prd-supervisor-agent",
                    context=root_ctx,
                    kind=otel_trace.SpanKind.CLIENT,
                    start_time=int(start * 1e9),
                    attributes={
                        "peer.service": "cdci-prd-supervisor-agent",
                        "rpc.system":   "aws-api",
                        "rpc.service":  "bedrock-agentcore",
                        "error":        not success,
                    },
                )
                child.end(end_time=int(end * 1e9))
                root.end(end_time=int(end * 1e9))
            except Exception as otel_err:
                logger.debug("OTEL span 생성 실패: %s", otel_err)
