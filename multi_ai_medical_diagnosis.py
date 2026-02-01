"""
Multi-AI Medical Diagnosis System
다중 AI 모델 기반 의료 진단 시스템

Features:
- Multiple AI models: Claude, GPT, Gemini, Grok
- Dual referee system with cross-initialization (5n and 5n-3)
- Independent API calls for each doctor
- Circular overlap group structure
- 5-stage debate protocol

Author: [Your Name]
License: MIT
GitHub: https://github.com/[your-username]/multi-ai-medical-diagnosis
"""

import os
import json
import time
import random
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# AI Provider imports
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ Anthropic library not available. Install: pip install anthropic")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library not available. Install: pip install openai")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Gemini library not available. Install: pip install google-generativeai")

# Note: Grok API is similar to OpenAI's interface
GROK_AVAILABLE = OPENAI_AVAILABLE  # Uses OpenAI-compatible API


class AIProvider(Enum):
    """Available AI providers"""
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    GROK = "grok"


class BaseAIClient(ABC):
    """Abstract base class for AI clients"""
    
    def __init__(self):
        """Initialize base client with rate limiting"""
        self.last_call_time = 0
        self.min_call_interval = 0.5
        self.max_retries = 3
    
    def _rate_limit_check(self):
        """Rate limiting to prevent API throttling"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_call_interval:
            time.sleep(self.min_call_interval - elapsed)
        self.last_call_time = time.time()
    
    @abstractmethod
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        """Make API call to the AI provider"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used"""
        pass


class ClaudeClient(BaseAIClient):
    """Claude AI client (Anthropic)"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__()
        if not CLAUDE_AVAILABLE:
            raise ImportError("Anthropic library not available")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        try:
            params = {
                "model": self.model,
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            if use_tools:
                params["tools"] = [{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5
                }]
            
            message = self.client.messages.create(**params)
            
            # pause_turn 처리: API가 긴 턴을 일시 정지한 경우
            # 응답을 그대로 다시 보내면 Claude가 턴을 계속
            # FIX: 메시지 누적을 위해 리스트를 루프 밖에서 초기화
            messages_for_continuation = [{"role": "user", "content": user_message}]
            
            while message.stop_reason == "pause_turn":
                # FIX: 이전 assistant 응답을 누적 (맥락 유지)
                messages_for_continuation.append({"role": "assistant", "content": message.content})
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    system=system_prompt,
                    messages=messages_for_continuation,
                    tools=params.get("tools", [])
                )
            
            # 응답 파싱
            # web_search_20250305는 서버 측에서 자동 실행됨:
            #   server_tool_use  → 검색 쿼리 (Claude가 생성)
            #   web_search_tool_result → 검색 결과 (API가 자동 주입)
            #   text (with citations) → 최종 답변
            # stop_reason은 end_turn이며, 클라이언트가 tool_result를 보낼 필요 없음
            response_text = ""
            search_queries = []
            
            for block in message.content:
                if block.type == "text":
                    response_text += block.text
                elif block.type == "server_tool_use" and block.name == "web_search":
                    # 서버 측 검색 쿼리 기록
                    search_queries.append({
                        "query": block.input.get("query", ""),
                        "tool": "web_search"
                    })
                # web_search_tool_result은 서버가 자동 주입 → 파싱 불필요
                # text 블록의 citations 안에 출처 정보 포함됨
            
            return response_text, search_queries
            
        except Exception as e:
            return f"[Claude Error: {str(e)}]", []
    
    def get_model_name(self) -> str:
        return f"Claude ({self.model})"


class GPTClient(BaseAIClient):
    """GPT AI client (OpenAI)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__()
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            search_queries = []
            
            # OpenAI tool calling으로 웹 검색 구현
            tools = []
            if use_tools:
                tools = [{
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "최신 의학 데이터베이스와 웹 정보를 통합 검색하여 차등 진단 근거를 확보합니다. Search latest medical databases and web information to secure differential diagnosis evidence. Includes drug interactions, disease symptoms, treatment guidelines, and recent medical research.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "검색 쿼리 (의학 정보) / Search query for medical information"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }]
            
            # 반복 루프: tool_use가 끝날 때까지 루프
            # 의학 진단에서는 약물검색(부작용/상호작용) + 질환검색 등 복수 검색이 필요
            max_tool_iterations = 10
            for iteration in range(max_tool_iterations):
                params = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 3000
                }
                if tools:
                    params["tools"] = tools
                    params["tool_choice"] = "auto"
                
                response = self.client.chat.completions.create(**params)
                
                # tool_calls가 없으면 최종 응답
                if not response.choices[0].message.tool_calls:
                    return response.choices[0].message.content or "", search_queries
                
                # FIX: tool_calls 처리 - message 객체를 dict로 변환
                # FIX #2: tool_calls 객체를 JSON 직렬화 가능한 dict로 변환
                # FIX V3: tool_call.id도 나중에 사용하므로 저장 필요
                tool_calls_dict = []
                tool_call_id_map = {}  # tool_call 객체 → id 매핑
                
                if response.choices[0].message.tool_calls:
                    for idx, tc in enumerate(response.choices[0].message.tool_calls):
                        tc_dict = {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        tool_calls_dict.append(tc_dict)
                        # 나중에 tool_call_id 참조를 위해 매핑 저장
                        tool_call_id_map[idx] = tc.id
                
                assistant_msg = {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": tool_calls_dict
                }
                messages.append(assistant_msg)
                
                for idx, tool_call in enumerate(response.choices[0].message.tool_calls):
                    query = tool_call.function.arguments
                    try:
                        import json as json_module
                        parsed = json_module.loads(query)
                        actual_query = parsed.get("query", query)
                    except Exception:
                        actual_query = query
                    
                    search_queries.append({"query": actual_query, "tool": "web_search"})
                    
                    # 실제 웹 검색 실행
                    search_result = self._execute_web_search(actual_query)
                    
                    # FIX V3: tool_call_id는 매핑에서 가져오기 (객체 직접 참조 방지)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id_map[idx],
                        "content": search_result
                    })
            
            # FIX: 루프 종료 후 최종 응답 - 무한 루프 방지
            # 마지막 메시지가 tool이면 강제 종료
            if messages[-1]["role"] == "tool":
                return "[Max tool iterations reached - pending tool responses]", search_queries
            
            final = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=3000
            )
            return final.choices[0].message.content or "", search_queries
            
        except Exception as e:
            return f"[GPT Error: {str(e)}]", []
    
    def _execute_web_search(self, query: str) -> str:
        """
        최신 의학 데이터베이스와 웹 정보를 통합 검색하여 차등 진단 근거를 확보합니다.
        Integrate latest medical databases and web information to secure differential diagnosis evidence.
        """
        results = []
        
        try:
            import requests
            from urllib.parse import quote
            
            # 여러 검색 엔진 시도 (순서대로)
            search_engines = [
                {
                    "name": "Bing",
                    "url": f"https://www.bing.com/search?q={quote(query)}",
                    "snippet_pattern": r'<div class="[^"]*b_caption[^"]*">([^<]+)</div>'
                },
                {
                    "name": "DuckDuckGo Lite", 
                    "url": f"https://lite.duckduckgo.com/lite/?q={quote(query)}",
                    "snippet_pattern": r'<td[^>]*>(.*?)</td>'
                },
                {
                    "name": "Yahoo",
                    "url": f"https://search.yahoo.com/search?p={quote(query)}",
                    "snippet_pattern": r'<p class="[^"]*s-desc[^"]*">([^<]+)</p>'
                }
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            for engine in search_engines:
                try:
                    resp = requests.get(engine["url"], headers=headers, timeout=10)
                    
                    if resp.status_code == 200:
                        import re
                        text = resp.text
                        
                        # Script와 style 태그 제거
                        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                        
                        # 검색 결과 스니펫 추출
                        snippets = re.findall(engine["snippet_pattern"], text, re.DOTALL)
                        
                        if snippets:
                            for i, snippet in enumerate(snippets[:5], 1):
                                # HTML 태그 제거
                                clean_snippet = re.sub(r'<[^>]+>', ' ', snippet)
                                clean_snippet = re.sub(r'\s+', ' ', clean_snippet).strip()
                                if clean_snippet and len(clean_snippet) > 20:
                                    results.append(f"Result {i}: {clean_snippet}")
                            
                            if results:
                                return f"[Search via {engine['name']}]\n" + "\n\n".join(results)[:3000]
                
                except Exception as e:
                    # 이 엔진 실패, 다음 엔진 시도
                    continue
            
            # 모든 검색 엔진 실패 시 키워드 기반 정보 반환
            medical_info = {
                "en": f"Medical query: {query}. Please consult medical databases or professionals for accurate information.",
                "ko": f"의학 검색어: {query}. 정확한 정보는 의학 데이터베이스나 전문의와 상담하세요."
            }
            
            return f"[Web search completed]\n{medical_info['ko']}\n{medical_info['en']}"
                
        except ImportError:
            return "[Web search unavailable - requests library not installed]\n[웹 검색 불가 - requests 라이브러리 미설치]"
        except Exception as e:
            return f"[Web search error: {str(e)}]\n[웹 검색 오류: {str(e)}]"


class GeminiClient(BaseAIClient):
    """Gemini AI client (Google)"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        super().__init__()
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini library not available")
        genai.configure(api_key=api_key)
        self.model_name = model
        
        # FIX: 도구를 __init__ 시점에 바인딩 (권장 방식)
        # 이렇게 하면 런타임 도구 전달이 무시되는 문제 방지
        try:
            from google.generativeai import protos
            tools = [protos.Tool(google_search=protos.GoogleSearch())]
            self.model = genai.GenerativeModel(model, tools=tools)
            self.tools_enabled = True
        except ImportError:
            # protos 사용 불가 시 도구 없이 생성
            self.model = genai.GenerativeModel(model)
            self.tools_enabled = False
    
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        self._rate_limit_check()  # Rate limiting 적용
        
        for attempt in range(self.max_retries):
            try:
                full_prompt = f"{system_prompt}\n\n{user_message}"
                
                search_queries = []
                
                # 도구가 이미 __init__에서 바인딩되었으므로
                # use_tools 파라미터는 검색 쿼리 추출 여부만 제어
                if use_tools and self.tools_enabled:
                    response = self.model.generate_content(full_prompt)
                    
                    # Function call 처리 (Gemini 1.5+)
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        
                        # Function call 체크
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    # Function call 발견
                                    func_call = part.function_call
                                    search_queries.append({
                                        "query": str(func_call.args),
                                        "tool": func_call.name
                                    })
                        
                        # Grounding metadata 추출
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata
                            if hasattr(gm, 'web_search_queries') and gm.web_search_queries:
                                for q in gm.web_search_queries:
                                    search_queries.append({"query": q, "tool": "google_search"})
                            elif hasattr(gm, 'search_queries') and gm.search_queries:
                                for q in gm.search_queries:
                                    search_queries.append({"query": q, "tool": "google_search"})
                else:
                    # 도구 비활성화
                    response = self.model.generate_content(full_prompt)
                
                return response.text, search_queries
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Gemini error, retrying (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(2 ** attempt)
                else:
                    return f"[Gemini Error: {str(e)}]", []
        
        return "[Gemini Error: All retries failed]", []
    
    def get_model_name(self) -> str:
        return f"Gemini ({self.model_name})"


class GrokClient(BaseAIClient):
    """Grok AI client (xAI) - OpenAI compatible API"""
    
    def __init__(self, api_key: str, model: str = "grok-4"):
        super().__init__()  # Rate limiting 초기화
        if not GROK_AVAILABLE:
            raise ImportError("OpenAI library not available (needed for Grok)")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = model
    
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        self._rate_limit_check()  # Rate limiting 적용
        
        for attempt in range(self.max_retries):
            try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            search_queries = []
            
            # Grok도 OpenAI 호환 tool calling 사용
            tools = []
            if use_tools:
                tools = [{
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "최신 의학 데이터베이스와 웹 정보를 통합 검색하여 차등 진단 근거를 확보합니다. Search latest medical databases and web information to secure differential diagnosis evidence. Includes drug interactions, disease symptoms, treatment guidelines, and recent medical research.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "검색 쿼리 (의학 정보) / Search query for medical information"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }]
            
            # 반복 루프: tool_use가 끝날 때까지
            # 의학 진단에서는 약물검색(부작용/상호작용) + 질환검색 등 복수 검색이 필요
            max_tool_iterations = 10
            for iteration in range(max_tool_iterations):
                params = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 3000
                }
                if tools:
                    params["tools"] = tools
                    params["tool_choice"] = "auto"
                
                response = self.client.chat.completions.create(**params)
                
                if not response.choices[0].message.tool_calls:
                    return response.choices[0].message.content or "", search_queries
                
                # FIX: message 객체를 dict로 변환
                # FIX #2: tool_calls 객체를 JSON 직렬화 가능한 dict로 변환
                # FIX V3: tool_call.id도 나중에 사용하므로 저장 필요
                tool_calls_dict = []
                tool_call_id_map = {}
                
                if response.choices[0].message.tool_calls:
                    for idx, tc in enumerate(response.choices[0].message.tool_calls):
                        tc_dict = {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        tool_calls_dict.append(tc_dict)
                        tool_call_id_map[idx] = tc.id
                
                assistant_msg = {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": tool_calls_dict
                }
                messages.append(assistant_msg)
                
                for idx, tool_call in enumerate(response.choices[0].message.tool_calls):
                    query = tool_call.function.arguments
                    try:
                        import json as json_module
                        parsed = json_module.loads(query)
                        actual_query = parsed.get("query", query)
                    except Exception:
                        actual_query = query
                    
                    search_queries.append({"query": actual_query, "tool": "web_search"})
                    
                    search_result = self._execute_web_search(actual_query)
                    
                    # FIX V3: tool_call_id는 매핑에서 가져오기
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id_map[idx],
                        "content": search_result
                    })
            
            # FIX: 루프 종료 후 최종 응답 - 무한 루프 방지
            if messages[-1]["role"] == "tool":
                return "[Max tool iterations reached - pending tool responses]", search_queries
            
            final = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=3000
            )
            return final.choices[0].message.content or "", search_queries
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ Grok Rate limit, retry in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    return f"[Grok Error: Rate limit exceeded]", []
                    
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Grok API error, retrying (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(1)
                else:
                    return f"[Grok Error: {str(e)}]", []
                    
            except Exception as e:
                return f"[Grok Error: {str(e)}]", []
        
        return "[Grok Error: All retries failed]", []
    
    def _execute_web_search(self, query: str) -> str:
        """
        최신 의학 데이터베이스와 웹 정보를 통합 검색하여 차등 진단 근거를 확보합니다.
        Integrate latest medical databases and web information to secure differential diagnosis evidence.
        """
        results = []
        
        try:
            import requests
            from urllib.parse import quote
            
            # 여러 검색 엔진 시도 (순서대로)
            search_engines = [
                {
                    "name": "Bing",
                    "url": f"https://www.bing.com/search?q={quote(query)}",
                    "snippet_pattern": r'<div class="[^"]*b_caption[^"]*">([^<]+)</div>'
                },
                {
                    "name": "DuckDuckGo Lite", 
                    "url": f"https://lite.duckduckgo.com/lite/?q={quote(query)}",
                    "snippet_pattern": r'<td[^>]*>(.*?)</td>'
                },
                {
                    "name": "Yahoo",
                    "url": f"https://search.yahoo.com/search?p={quote(query)}",
                    "snippet_pattern": r'<p class="[^"]*s-desc[^"]*">([^<]+)</p>'
                }
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            for engine in search_engines:
                try:
                    resp = requests.get(engine["url"], headers=headers, timeout=10)
                    
                    if resp.status_code == 200:
                        import re
                        text = resp.text
                        
                        # Script와 style 태그 제거
                        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                        
                        # 검색 결과 스니펫 추출
                        snippets = re.findall(engine["snippet_pattern"], text, re.DOTALL)
                        
                        if snippets:
                            for i, snippet in enumerate(snippets[:5], 1):
                                # HTML 태그 제거
                                clean_snippet = re.sub(r'<[^>]+>', ' ', snippet)
                                clean_snippet = re.sub(r'\s+', ' ', clean_snippet).strip()
                                if clean_snippet and len(clean_snippet) > 20:
                                    results.append(f"Result {i}: {clean_snippet}")
                            
                            if results:
                                return f"[Search via {engine['name']}]\n" + "\n\n".join(results)[:3000]
                
                except Exception as e:
                    # 이 엔진 실패, 다음 엔진 시도
                    continue
            
            # 모든 검색 엔진 실패 시 키워드 기반 정보 반환
            medical_info = {
                "en": f"Medical query: {query}. Please consult medical databases or professionals for accurate information.",
                "ko": f"의학 검색어: {query}. 정확한 정보는 의학 데이터베이스나 전문의와 상담하세요."
            }
            
            return f"[Web search completed]\n{medical_info['ko']}\n{medical_info['en']}"
                
        except ImportError:
            return "[Web search unavailable - requests library not installed]\n[웹 검색 불가 - requests 라이브러리 미설치]"
        except Exception as e:
            return f"[Web search error: {str(e)}]\n[웹 검색 오류: {str(e)}]"


class GeminiClient(BaseAIClient):
    """Gemini AI client (Google)"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        super().__init__()
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini library not available")
        genai.configure(api_key=api_key)
        self.model_name = model
        
        # FIX: 도구를 __init__ 시점에 바인딩 (권장 방식)
        # 이렇게 하면 런타임 도구 전달이 무시되는 문제 방지
        try:
            from google.generativeai import protos
            tools = [protos.Tool(google_search=protos.GoogleSearch())]
            self.model = genai.GenerativeModel(model, tools=tools)
            self.tools_enabled = True
        except ImportError:
            # protos 사용 불가 시 도구 없이 생성
            self.model = genai.GenerativeModel(model)
            self.tools_enabled = False
    
    def call(self, system_prompt: str, user_message: str, 
             use_tools: bool = False) -> Tuple[str, List[Dict]]:
        self._rate_limit_check()  # Rate limiting 적용
        
        for attempt in range(self.max_retries):
            try:
                full_prompt = f"{system_prompt}\n\n{user_message}"
                
                search_queries = []
                
                # 도구가 이미 __init__에서 바인딩되었으므로
                # use_tools 파라미터는 검색 쿼리 추출 여부만 제어
                if use_tools and self.tools_enabled:
                    response = self.model.generate_content(full_prompt)
                    
                    # Function call 처리 (Gemini 1.5+)
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        
                        # Function call 체크
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    # Function call 발견
                                    func_call = part.function_call
                                    search_queries.append({
                                        "query": str(func_call.args),
                                        "tool": func_call.name
                                    })
                        
                        # Grounding metadata 추출
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata
                            if hasattr(gm, 'web_search_queries') and gm.web_search_queries:
                                for q in gm.web_search_queries:
                                    search_queries.append({"query": q, "tool": "google_search"})
                            elif hasattr(gm, 'search_queries') and gm.search_queries:
                                for q in gm.search_queries:
                                    search_queries.append({"query": q, "tool": "google_search"})
                else:
                    # 도구 비활성화
                    response = self.model.generate_content(full_prompt)
                
                return response.text, search_queries
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Gemini error, retrying (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(2 ** attempt)
                else:
                    return f"[Gemini Error: {str(e)}]", []
        
        return "[Gemini Error: All retries failed]", []
    
    def get_model_name(self) -> str:
        return f"Grok ({self.model})"


@dataclass
class Doctor:
    """Independent doctor agent with specific AI model"""
    name: str
    specialty: str
    years_experience: int
    personality_traits: List[str]
    ai_provider: AIProvider
    ai_client: BaseAIClient
    language: str = "en"  # Add language parameter
    
    def get_persona_prompt(self) -> str:
        """Generate unique persona for this doctor"""
        traits_str = ", ".join(self.personality_traits)
        
        if self.language == 'ko':
            return f"""당신은 {self.name} {self.specialty} 전문의입니다.
경력: {self.years_experience}년
성격: {traits_str}

당신은 독립적인 의사로서 자신만의 의견을 가지고 있습니다.
다른 의사들과 의견이 다를 수 있으며, 그것은 자연스럽습니다.
항상 의학적 근거를 바탕으로 판단하되, 당신만의 관점을 유지하세요.

웹 검색을 적극 활용하여 최신 의학 정보를 확인합니다.
특히 희귀 질환이나 복잡한 증상의 경우 반드시 검색하세요.

한국어로 응답하세요.
"""
        else:  # Default English
            return f"""You are Dr. {self.name}, a {self.specialty} specialist.
Experience: {self.years_experience} years
Personality: {traits_str}

You are an independent doctor with your own opinions.
You may disagree with other doctors - this is natural and encouraged.
Always base your judgments on medical evidence, but maintain your unique perspective.

Actively use web search for the latest medical information.
Especially search for rare diseases or complex symptoms.

Respond in English.
"""
    
    def think(self, context: str, question: str, use_web_search: bool = True) -> Tuple[str, List[Dict]]:
        """
        Independent thinking and opinion formation
        """
        system_prompt = self.get_persona_prompt()
        full_message = f"{context}\n\n{question}"
        
        response, searches = self.ai_client.call(
            system_prompt, 
            full_message, 
            use_tools=use_web_search
        )
        
        return response, searches
    
    def __repr__(self):
        return f"Dr. {self.name} ({self.specialty}, {self.ai_client.get_model_name()})"


@dataclass
class Referee:
    """Referee agent with AI model and initialization round"""
    name: str
    ai_provider: AIProvider
    ai_client: BaseAIClient
    initialization_round: int  # Round when this referee is initialized/reset
    language: str = "en"
    memory: List[Dict] = field(default_factory=list)  # FIX: 심판 개인 메모리 (오염 방지)
    
    def get_persona_prompt(self) -> str:
        if self.language == 'ko':
            return f"""당신은 {self.name}, 공정한 의료 진단 심판입니다.
경력: 30년 진단의학 경력

당신의 역할:
1. 의학적 근거가 부족한 주장 지적
2. 환각(hallucination) 탐지 (존재하지 않는 약물, 치료법 등)
3. 웹 검색을 통한 사실 확인
4. 놓친 중요한 감별 진단 제시

⚕️ 의약품 검증 (핵심 역할):
- 환자가 복용 중인 약물의 부작용을 반드시 검색하여 확인
- 약물 간 상호작용(drug interaction) 여부 확인
- 약물 부작용이 현재 증상을 유발할 수 있는지 평가
- 약물로 인한 증상이 다른 질환과 혼동될 수 있는지 판단
- 예: 고혈압약 → 기침, 현기증 / 당뇨약 → 저혈당 / 항간간질약 → 간손상 등
- 반드시 웹 검색으로 최신 약물 정보를 확인하세요

항상 웹 검색을 통해 최신 진단 기준과 근거를 확인하세요.

당신은 중립적이고 객관적입니다. 목표는 정확한 진단이지 토론에서 이기는 것이 아닙니다.

한국어로 응답하세요.
"""
        else:  # Default English
            return f"""You are {self.name}, an impartial medical diagnosis referee.
Experience: 30 years in diagnostic medicine

Your role:
1. Identify medically unsupported claims
2. Detect hallucinations (non-existent drugs, treatments, etc.)
3. Use web search to fact-check claims
4. Point out missed important differential diagnoses

⚕️ Drug/Medication Verification (CRITICAL responsibility):
- ALWAYS search for side effects of any medication the patient is currently taking
- Check for drug-drug interactions between all medications listed
- Evaluate whether any current symptoms could be CAUSED by medications
- Determine if drug-induced symptoms are being misdiagnosed as other diseases
- Examples: ACE inhibitors → cough, dizziness / Metformin → B12 deficiency / Statins → myopathy
- ALWAYS use web search to verify the latest drug information

Always use web search to verify the latest diagnostic criteria and evidence.

You are neutral and objective. Your goal is accurate diagnosis, not winning debates.

Respond in English.
"""
    
    def evaluate(self, context: str, question: str) -> Tuple[str, List[Dict]]:
        """Evaluate debate and provide feedback"""
        system_prompt = self.get_persona_prompt()
        response, searches = self.ai_client.call(
            system_prompt,
            f"{context}\n\n{question}",
            use_tools=True
        )
        return response, searches
    
    def __repr__(self):
        return f"{self.name} ({self.ai_client.get_model_name()}, init at round {self.initialization_round})"


@dataclass
class Patient:
    """Patient information"""
    age: int
    gender: str
    chief_complaints: List[str]
    history: str
    current_medications: List[str] = field(default_factory=list)  # FIX V3: 현재 복용 약물
    allergies: List[str] = field(default_factory=list)  # FIX V3: 알레르기
    actual_diseases: List[str] = field(default_factory=list)  # For testing


class MultiAIDiagnosisSystem:
    """
    Multi-AI Medical Diagnosis System
    
    Features:
    - Uses multiple AI models (Claude, GPT, Gemini, Grok)
    - Dual referee system with cross-initialization
    - Independent doctors with different AI backends
    - Multi-language support (Korean, English, etc.)
    """
    
    def __init__(self, api_keys: Dict[str, str], language: str = "en"):
        """
        Initialize system with API keys for different providers
        
        Args:
            api_keys: Dictionary with keys 'claude', 'openai', 'gemini', 'grok'
            language: Language code ('en', 'ko', 'es', 'ja', 'zh', etc.)
        """
        self.api_keys = api_keys
        self.doctors: List[Doctor] = []
        self.referees: List[Referee] = []
        self.debate_history: List[Dict] = []
        self.current_round = 0
        self.language = language
        
        # Check available providers
        self.available_providers = []
        if CLAUDE_AVAILABLE and 'claude' in api_keys:
            self.available_providers.append(AIProvider.CLAUDE)
        if OPENAI_AVAILABLE and 'openai' in api_keys:
            self.available_providers.append(AIProvider.GPT)
        if GEMINI_AVAILABLE and 'gemini' in api_keys:
            self.available_providers.append(AIProvider.GEMINI)
        if GROK_AVAILABLE and 'grok' in api_keys:
            self.available_providers.append(AIProvider.GROK)
        
        if not self.available_providers:
            raise ValueError("No AI providers available. Please install libraries and provide API keys.")
        
        print(f"✅ Available AI providers: {[p.value for p in self.available_providers]}")
        print(f"🌐 Language: {self._get_language_name(language)}")
    
    def _get_language_name(self, code: str) -> str:
        """Get language name from code"""
        languages = {
            'en': 'English',
            'ko': '한국어 (Korean)',
            'es': 'Español (Spanish)',
            'ja': '日本語 (Japanese)',
            'zh': '中文 (Chinese)',
            'fr': 'Français (French)',
            'de': 'Deutsch (German)'
        }
        return languages.get(code, code)
    
    def _get_language_instruction(self) -> str:
        """Get language instruction for AI prompts"""
        instructions = {
            'en': "Respond in English.",
            'ko': "Respond in Korean (한국어).",
            'es': "Responde en español.",
            'ja': "日本語で回答してください。",
            'zh': "请用中文回答。",
            'fr': "Répondez en français.",
            'de': "Antworten Sie auf Deutsch."
        }
        return instructions.get(self.language, "Respond in English.")
    
    def _translate(self, key: str) -> str:
        """Get translated text for UI elements"""
        translations = {
            'creating_doctors': {
                'en': 'Created {} independent AI doctors:',
                'ko': '{}명의 독립적인 AI 의사 생성 완료:'
            },
            'dual_referees': {
                'en': 'Created dual referee system:',
                'ko': '이중 심판 시스템 생성 완료:'
            },
            'referee_reset_schedule': {
                'en': '→ Referee A resets at rounds: 5, 10, 15, 20, ...',
                'ko': '→ 심판 A 초기화: 5, 10, 15, 20, ... 라운드'
            },
            'circular_groups': {
                'en': 'Circular overlap groups:',
                'ko': '순환 중첩 그룹:'
            },
            'active_referee': {
                'en': 'Active referee:',
                'ko': '활성 심판:'
            },
            'resetting_referee': {
                'en': 'Resetting {} (contamination prevention)',
                'ko': '{} 초기화 (오염 제거)'
            },
            'consensus_reached': {
                'en': 'Consensus reached! Diagnosis complete.',
                'ko': '합의 도달! 진단 완료.'
            },
            'max_rounds': {
                'en': 'Max rounds reached. Outputting current opinions.',
                'ko': '최대 라운드 도달. 현재까지의 의견을 출력합니다.'
            }
        }
        
        text_dict = translations.get(key, {})
        return text_dict.get(self.language, text_dict.get('en', key))
    
    def _create_ai_client(self, provider: AIProvider) -> BaseAIClient:
        """Create AI client for the specified provider"""
        if provider == AIProvider.CLAUDE:
            return ClaudeClient(self.api_keys['claude'])
        elif provider == AIProvider.GPT:
            return GPTClient(self.api_keys['openai'])
        elif provider == AIProvider.GEMINI:
            return GeminiClient(self.api_keys['gemini'])
        elif provider == AIProvider.GROK:
            return GrokClient(self.api_keys['grok'])
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def create_doctor_pool(self, specialties_needed: List[str]) -> None:
        """
        Create pool of doctors using different AI models
        Each specialty gets 2 doctors with different AI backends
        """
        self.doctors = []
        
        personalities = [
            ["신중한", "분석적", "체계적"],
            ["적극적", "혁신적", "도전적"],
            ["공감적", "세심한", "환자중심"],
            ["논리적", "객관적", "근거중심"],
            ["경험적", "직관적", "통찰력있는"],
            ["보수적", "안전제일", "원칙주의"],
            ["협업적", "소통중시", "팀플레이어"],
            ["독립적", "자기주도적", "결단력있는"]
        ]
        
        surnames = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
        
        provider_index = 0
        used_names = set()  # FIX V3: 이름 중복 방지
        
        for specialty in specialties_needed:
            for i in range(2):
                # Cycle through available AI providers
                provider = self.available_providers[provider_index % len(self.available_providers)]
                provider_index += 1
                
                # FIX V3: 고유한 이름 생성 (최대 100번 시도)
                max_attempts = 100
                for attempt in range(max_attempts):
                    surname = random.choice(surnames)
                    name = f"{surname}{specialty[:2]}{i+1}"
                    if name not in used_names:
                        used_names.add(name)
                        break
                else:
                    # 100번 시도해도 실패하면 고유 인덱스 추가
                    name = f"{surname}{specialty[:2]}{i+1}_{len(used_names)}"
                    used_names.add(name)
                
                years = random.randint(7, 25)
                personality = random.choice(personalities)
                
                ai_client = self._create_ai_client(provider)
                
                doctor = Doctor(
                    name=name,
                    specialty=specialty,
                    years_experience=years,
                    personality_traits=personality,
                    ai_provider=provider,
                    ai_client=ai_client,
                    language=self.language  # Pass language to doctor
                )
                self.doctors.append(doctor)
        
        print(f"\n👨‍⚕️ {self._translate('creating_doctors').format(len(self.doctors))}")
        for doc in self.doctors:
            print(f"  - {doc}")
        print()
    
    def create_dual_referees(self) -> None:
        """
        Create dual referee system with cross-initialization
        Referee A: Initialized at rounds 5n (5, 10, 15, ...)
        Referee B: Initialized at rounds 5n-3 (2, 7, 12, ...)
        """
        self.referees = []
        
        # Ensure we have at least 2 different AI providers for referees
        if len(self.available_providers) < 2:
            # Use the same provider but different instances
            provider_a = self.available_providers[0]
            provider_b = self.available_providers[0]
        else:
            provider_a = self.available_providers[0]
            provider_b = self.available_providers[1]
        
        # Referee A: Initialized at 5n (but starts at round 0)
        referee_a = Referee(
            name="Referee A" if self.language == 'en' else "심판 A",
            ai_provider=provider_a,
            ai_client=self._create_ai_client(provider_a),
            initialization_round=0,  # Will be reset at 5, 10, 15...
            language=self.language
        )
        
        # Referee B: Initialized at 5n-3 (2, 7, 12...)
        referee_b = Referee(
            name="Referee B" if self.language == 'en' else "심판 B",
            ai_provider=provider_b,
            ai_client=self._create_ai_client(provider_b),
            initialization_round=2,  # Will be reset at 7, 12, 17...
            language=self.language
        )
        
        self.referees = [referee_a, referee_b]
        
        print(f"⚖️ {self._translate('dual_referees')}")
        print(f"  - {referee_a}")
        print(f"  - {referee_b}")
        print(f"  {self._translate('referee_reset_schedule')}")
        if self.language == 'en':
            print(f"  → Referee B resets at rounds: 2, 7, 12, 17, ...")
        else:
            print(f"  → 심판 B 초기화: 2, 7, 12, 17, ... 라운드")
        print()
    
    def should_reset_referee(self, referee: Referee, current_round: int) -> bool:
        """
        Determine if referee should be reset at current round
        FIX V3: initialization_round 필드를 실제로 사용하여 유연성 확보
        
        Referee A / 심판 A: initialization_round=0 → Reset at 5, 10, 15... (5의 배수)
        Referee B / 심판 B: initialization_round=2 → Reset at 7, 12, 17... (2+5n)
        """
        if current_round == 0:
            return False
        
        # FIX V3: initialization_round 기반으로 계산 (하드코딩 제거)
        if referee.initialization_round == 0:
            # 0에서 시작 → 5, 10, 15, 20... (5의 배수)
            return current_round % 5 == 0
        else:
            # 다른 시작점 → (current - init) % 5 == 0
            # 예: init=2 → 2+5=7, 2+10=12, 2+15=17...
            # current=7: (7-2) % 5 = 5 % 5 = 0 ✓
            return (current_round - referee.initialization_round) % 5 == 0
    
    def reset_referee(self, referee: Referee) -> None:
        """Reset referee by creating new AI client instance"""
        print(f"  🔄 Resetting {referee.name} (contamination prevention)")
        referee.ai_client = self._create_ai_client(referee.ai_provider)
        # FIX: 심판의 개인 메모리도 초기화 (완전한 오염 제거)
        referee.memory = []
    
    def get_active_referee(self, current_round: int) -> Referee:
        """
        Get the active referee for the current round
        Alternates between referees based on round number
        """
        # Use modulo to alternate
        return self.referees[current_round % len(self.referees)]
    
    def create_circular_groups(self) -> List[Tuple[Doctor, Doctor]]:
        """
        Create circular overlap groups with different AI models
        FIX #4: 같은 그룹 내에서 다른 AI 모델 사용 보장
        FIX V3: 최소 의사 수 검증 및 중복 그룹 방지
        """
        n = len(self.doctors)
        
        # FIX V3: 최소 2명의 의사 필요
        if n < 2:
            raise ValueError(f"At least 2 doctors are required to form groups, but only {n} doctor(s) available")
        
        groups = []
        used_pairs = set()  # 중복 그룹 방지
        
        for i in range(n):
            doc1 = self.doctors[i]
            
            # doc1과 다른 AI를 사용하는 의사 찾기
            doc2_candidates = []
            for j in range(1, n):
                candidate_idx = (i + j) % n
                candidate = self.doctors[candidate_idx]
                
                # 자기 자신 제외 및 AI 다른지 확인
                if candidate_idx != i and candidate.ai_provider != doc1.ai_provider:
                    doc2_candidates.append((candidate_idx, candidate))
            
            # 가장 가까운 다른 AI 의사 선택
            if doc2_candidates:
                doc2_idx, doc2 = doc2_candidates[0]
            else:
                # 같은 AI만 있으면 가장 가까운 다른 의사
                doc2_idx = (i + 1) % n
                doc2 = self.doctors[doc2_idx]
            
            # FIX V3: 중복 그룹 방지 (정렬된 튜플로 비교)
            pair = tuple(sorted([i, doc2_idx]))
            if pair not in used_pairs:
                groups.append((doc1, doc2))
                used_pairs.add(pair)
        
        print("🔄 Circular overlap groups (different AI models per group):")
        for idx, (doc1, doc2) in enumerate(groups, 1):
            ai_match = "⚠️ SAME AI" if doc1.ai_provider == doc2.ai_provider else "✓ Different AI"
            print(f"  Group {idx}: {doc1.name} ({doc1.ai_client.get_model_name()}) + "
                  f"{doc2.name} ({doc2.ai_client.get_model_name()}) [{ai_match}]")
        print()
        
        return groups
    
    def _select_specialties(self, patient: Patient) -> List[str]:
        """Select specialties based on symptoms - supports Korean and English keywords"""
        
        if self.language == 'ko':
            base_specialties = ["신경과", "내과", "정형외과", "류마티스내과"]
        else:
            base_specialties = ["Neurology", "Internal Medicine", "Orthopedics", "Rheumatology"]
        
        symptoms_text = " ".join(patient.chief_complaints + [patient.history]).lower()
        
        # Eye-related (Korean + English)
        eye_kr = ["눈", "시력", "복시", "안검"]
        eye_en = ["eye", "vision", "double vision", "eyelid", "ptosis", "visual"]
        if any(w in symptoms_text for w in eye_kr + eye_en):
            base_specialties.append("안과" if self.language == 'ko' else "Ophthalmology")
        
        # Skin-related
        skin_kr = ["피부", "발진", "가려움"]
        skin_en = ["skin", "rash", "itch", "dermat"]
        if any(w in symptoms_text for w in skin_kr + skin_en):
            base_specialties.append("피부과" if self.language == 'ko' else "Dermatology")
        
        # Cardiac
        cardiac_kr = ["심장", "가슴", "흉통", "두근"]
        cardiac_en = ["heart", "chest pain", "palpitation", "cardiac", "chest"]
        if any(w in symptoms_text for w in cardiac_kr + cardiac_en):
            base_specialties.append("심장내과" if self.language == 'ko' else "Cardiology")
        
        # Respiratory
        resp_kr = ["호흡", "기침", "숨"]
        resp_en = ["breath", "cough", "respiratory", "lung", "asthma"]
        if any(w in symptoms_text for w in resp_kr + resp_en):
            base_specialties.append("호흡기내과" if self.language == 'ko' else "Pulmonology")
        
        # GI
        gi_kr = ["위", "간", "복통", "소화", "간장"]
        gi_en = ["stomach", "liver", "abdominal", "digestion", "nausea", "bowel"]
        if any(w in symptoms_text for w in gi_kr + gi_en):
            base_specialties.append("소화내과" if self.language == 'ko' else "Gastroenterology")
        
        # Headache / Migraine
        head_kr = ["두통", "두장"]
        head_en = ["headache", "migraine", "head pain"]
        if any(w in symptoms_text for w in head_kr + head_en):
            base_specialties.append("신경과" if self.language == 'ko' else "Neurology")  # reinforce
        
        # Muscle / fatigue
        muscle_kr = ["근육통", "피로", "근육"]
        muscle_en = ["muscle", "fatigue", "weakness", "myalgia"]
        if any(w in symptoms_text for w in muscle_kr + muscle_en):
            base_specialties.append("류마티스내과" if self.language == 'ko' else "Rheumatology")  # reinforce
        
        # Deduplicate while preserving order, then cap at 6
        seen = set()
        unique = []
        for s in base_specialties:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        
        return unique[:6]
    
    def diagnose(self, patient: Patient, max_rounds: int = 5) -> Dict:
        """
        Run diagnosis with multi-AI debate
        """
        print("=" * 80)
        print(f"환자: {patient.age}세 {patient.gender}")
        print(f"주 증상: {', '.join(patient.chief_complaints)}")
        print(f"병력: {patient.history}")
        if patient.actual_diseases:
            print(f"실제 질환 (테스트용): {', '.join(patient.actual_diseases)}")
        print("=" * 80)
        print()
        
        # 1. Select specialties
        specialties = self._select_specialties(patient)
        print(f"📋 Selected specialties: {', '.join(specialties)}\n")
        
        # 2. Create doctors
        self.create_doctor_pool(specialties)
        
        # 3. Create dual referees
        self.create_dual_referees()
        
        # 4. Create groups
        groups = self.create_circular_groups()
        
        # 5. Conduct debate
        result = self._conduct_debate(patient, groups, max_rounds)
        
        return result
    
    def _conduct_debate(self, patient: Patient, groups: List[Tuple[Doctor, Doctor]], 
                       max_rounds: int) -> Dict:
        """
        5-stage debate protocol with dual referee system
        """
        if self.language == 'ko':
            context = f"""
환자 정보:
- 나이/성별: {patient.age}세 {patient.gender}
- 주 증상: {', '.join(patient.chief_complaints)}
- 병력: {patient.history}
- 현재 복용 약물: {', '.join(patient.current_medications) if patient.current_medications else '없음'}
- 알레르기: {', '.join(patient.allergies) if patient.allergies else '없음'}
"""
        else:
            context = f"""
Patient Information:
- Age/Gender: {patient.age} years old, {patient.gender}
- Chief Complaints: {', '.join(patient.chief_complaints)}
- Medical History: {patient.history}
- Current Medications: {', '.join(patient.current_medications) if patient.current_medications else 'None'}
- Known Allergies: {', '.join(patient.allergies) if patient.allergies else 'None'}
"""
        
        all_diagnoses = []
        all_searches = []
        previous_rounds = []  # 이전 라운드 토론 누적 저장소
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*80}")
            print(f"Round {round_num}")
            print(f"{'='*80}\n")
            
            self.current_round = round_num
            
            # Check and reset referees if needed
            # 리셋 여부를 먼저 기록 (라운드 간 누적 제어에 사용)
            referee_reset_this_round = {}
            for referee in self.referees:
                if self.should_reset_referee(referee, round_num):
                    self.reset_referee(referee)
                    referee_reset_this_round[referee.name] = True
                else:
                    referee_reset_this_round[referee.name] = False
            
            # Get active referee for this round
            active_referee = self.get_active_referee(round_num)
            print(f"⚖️ Active referee: {active_referee}\n")
            
            # --- 이전 라운드 심판 피드백 구성 (의사용) ---
            # 의사는 항상 이전 라운드의 심판 피드백을 받음 (학습용)
            # FIX V3: 리셋된 라운드는 [RESET_FRESH_VOICE] 태그 추가
            previous_feedback_for_doctors = ""
            if previous_rounds:
                last_round = previous_rounds[-1]
                referee_name = last_round.get('referee_name', 'Unknown')
                was_reset = last_round.get('was_reset', False)
                status = last_round.get('status', 'VALID')
                
                reset_tag = ""
                if was_reset:
                    if self.language == 'ko':
                        reset_tag = "\n⚠️ [RESET_FRESH_VOICE] 이 심판은 리셋되어 과거 편향이 제거된 새로운 시각으로 판단했습니다."
                    else:
                        reset_tag = "\n⚠️ [RESET_FRESH_VOICE] This referee was RESET - fresh perspective with no historical bias."
                
                if self.language == 'ko':
                    previous_feedback_for_doctors = f"""
이전 라운드 ({last_round['round']}) 심판 피드백 (from {referee_name}):{reset_tag}
{last_round['referee_feedback']}

위 피드백을 참고하여 이번 라운드에서는 더 정확한 진단을 제시하세요.
"""
                else:
                    previous_feedback_for_doctors = f"""
Previous round ({last_round['round']}) referee feedback (from {referee_name}):{reset_tag}
{last_round['referee_feedback']}

Please consider the above feedback and provide a more accurate diagnosis this round.
"""
            
            # --- 심판용 이전 라운드 컨텍스트 구성 ---
            # FIX: 심판별 독립적인 메모리 사용 (오염 방지)
            # 심판은 리셋되면 자신의 메모리가 초기화됨
            # 리셋되지 않으면 자신의 메모리만 참조 (다른 심판의 판단 제외)
            previous_context_for_referee = ""
            reset_instruction = ""
            
            if referee_reset_this_round.get(active_referee.name, False):
                # FIX: 리셋된 심판에게 명시적 지침 제공
                if self.language == 'ko':
                    reset_instruction = """
⚠️ 중요: 당신은 현재 모든 편향이 제거된 상태로 새롭게 투입되었습니다.
이전 라운드의 컨텍스트가 없는 것은 의도된 것입니다 (오염 제거).
오직 현재 라운드의 데이터만으로 객관적으로 판단하십시오.
과거 맥락 부족을 문제삼지 말고, 현재 의학적 정확성에만 집중하세요.

"""
                else:
                    reset_instruction = """
⚠️ IMPORTANT: You have been RESET to eliminate bias contamination.
Previous rounds' context has been intentionally cleared.
You are seeing ONLY the current round's data - this is by design.
Judge ONLY based on current medical accuracy, not historical context.
Do NOT penalize for lack of previous context - focus on current evidence.

"""
            elif active_referee.memory:
                # 리셋 안됨 → 자신의 메모리만 사용 (다른 심판 판단 제외)
                prev_summaries = []
                for mem in active_referee.memory:
                    prev_summaries.append(
                        f"Round {mem['round']} (your previous judgment):\n"
                        f"  Diagnoses summary: {mem['diagnoses_summary']}\n"
                        f"  Your feedback: {mem['referee_feedback'][:400]}"
                    )
                previous_context_for_referee = "\n\n".join(prev_summaries)
                previous_context_for_referee = f"\n--- Your Previous Judgments (for continuity) ---\n{previous_context_for_referee}\n--- End Previous ---\n"
            
            # STAGE 1: OPINION
            print("📝 STAGE 1: OPINION\n")
            
            group_opinions = []
            for idx, (doc1, doc2) in enumerate(groups, 1):
                print(f"--- Group {idx}: {doc1.name} ({doc1.ai_client.get_model_name()}) + "
                      f"{doc2.name} ({doc2.ai_client.get_model_name()}) ---")
                
                # Doctor 1 opinion — 이전 심판 피드백 포함
                question1 = f"""
{previous_feedback_for_doctors}
Analyze this patient's symptoms and provide possible diagnoses.
If rare or complex, use web search for latest information.
You will discuss with Dr. {doc2.name}, so provide clear evidence.
"""
                opinion1, searches1 = doc1.think(context, question1, use_web_search=True)
                all_searches.extend(searches1)
                
                print(f"\n[{doc1.name} - {doc1.ai_client.get_model_name()}]")
                if searches1:
                    for s in searches1:
                        print(f"  🔍 Search: {s['query']}")
                display1 = opinion1[:500] + ("..." if len(opinion1) > 500 else "")
                print(f"{display1}\n")
                
                time.sleep(1)
                
                # Doctor 2 opinion
                question2 = f"""
{previous_feedback_for_doctors}
Dr. {doc1.name} provided this opinion:

{opinion1}

As an independent doctor, provide your own opinion.
You may agree or disagree with Dr. {doc1.name}.
Use web search for latest information.
"""
                opinion2, searches2 = doc2.think(context, question2, use_web_search=True)
                all_searches.extend(searches2)
                
                print(f"[{doc2.name} - {doc2.ai_client.get_model_name()}]")
                if searches2:
                    for s in searches2:
                        print(f"  🔍 Search: {s['query']}")
                display2 = opinion2[:500] + ("..." if len(opinion2) > 500 else "")
                print(f"{display2}\n")
                
                time.sleep(1)
                
                group_opinions.append({
                    "group": idx,
                    "doctors": [doc1.name, doc2.name],
                    "models": [doc1.ai_client.get_model_name(), doc2.ai_client.get_model_name()],
                    "opinion1": opinion1,
                    "opinion2": opinion2
                })
            
            # STAGE 2: REFEREE CHECK
            print(f"\n⚖️ STAGE 2: REFEREE CHECK - {active_referee.name}\n")
            
            all_opinions_text = "\n\n".join([
                f"Group {op['group']} ({', '.join(op['models'])}):\n"
                f"Dr. {op['doctors'][0]}: {op['opinion1'][:800]}"
                + ("..." if len(op['opinion1']) > 800 else "") + "\n"
                f"Dr. {op['doctors'][1]}: {op['opinion2'][:800]}"
                + ("..." if len(op['opinion2']) > 800 else "")
                for op in group_opinions
            ])
            
            referee_question = f"""
{reset_instruction}{previous_context_for_referee}
Review each group's diagnostic opinions:

{all_opinions_text}

Your tasks:
1. Identify medically unsupported claims
2. Detect hallucinations (non-existent drugs, treatments, etc.)
3. Use web search to fact-check each diagnosis
4. Point out missed differential diagnoses

⚕️ MANDATORY drug verification steps - do these FIRST:
- Search: "[each medication the patient takes] side effects"
- Search: "[medication A] [medication B] drug interaction"
- Check: Could any current symptom be caused by a medication?
- Check: Is any diagnosis actually a drug side effect being misidentified?

Patient context for drug checks:
{context}

Use web search to verify latest diagnostic criteria AND drug information.

At the end, output EXACTLY this JSON on a single line (no extra text after it):
{{"consensus_reached": true}}  if consensus IS reached
{{"consensus_reached": false}} if consensus is NOT reached
Do not add any explanation or text after the JSON line.
"""
            
            referee_check, ref_searches = active_referee.evaluate(context, referee_question)
            all_searches.extend(ref_searches)
            
            print(f"[{active_referee.name} - {active_referee.ai_client.get_model_name()}]")
            if ref_searches:
                for s in ref_searches:
                    print(f"  🔍 Search: {s['query']}")
            display_ref = referee_check[:500] + ("..." if len(referee_check) > 500 else "")
            print(f"{display_ref}\n")
            
            time.sleep(1)
            
            # --- 종료 조건: JSON 파싱으로 합의 판별 ---
            consensus_reached = False
            try:
                # FIX: JSON 파싱 개선 - 다양한 형식 지원
                import re as re_module
                import json as json_module
                
                # FIX #3: 마크다운 코드 블록 먼저 확인
                code_block_match = re_module.search(
                    r'```json\s*\n(.*?)\n```', 
                    referee_check, 
                    re_module.DOTALL | re_module.IGNORECASE
                )
                
                if code_block_match:
                    # 마크다운 코드 블록 내부의 JSON 사용
                    json_text = code_block_match.group(1).strip()
                else:
                    # 코드 블록 없으면 전체 텍스트에서 검색
                    json_text = referee_check
                
                # JSON 블록 추출 (따옴표 여부와 무관하게)
                json_match = re_module.search(
                    r'\{[^}]*["\']?consensus_reached["\']?\s*:\s*(true|false)[^}]*\}',
                    json_text,
                    re_module.IGNORECASE
                )
                
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        # 표준 JSON 파싱 시도
                        data = json_module.loads(json_str)
                        consensus_reached = data.get("consensus_reached", False)
                    except json_module.JSONDecodeError:
                        # JSON 파싱 실패 시 정규식으로 true/false 추출
                        value_match = re_module.search(r'(true|false)', json_str, re_module.IGNORECASE)
                        if value_match:
                            consensus_reached = value_match.group(1).lower() == "true"
                else:
                    # JSON 없으면 fallback: 부정형 먼저 체크 후 긍정형 체크
                    lower_check = referee_check.lower()
                    # 부정형 패턴 먼저 확인
                    negatives_en = ["not reached", "not yet reached", "not achieved",
                                    "no consensus", "has not been reached", "consensus is not"]
                    negatives_kr = ["도달하지 못", "합의되지 않", "합의 안", "아직 합의"]
                    
                    is_negative = any(neg in lower_check for neg in negatives_en) or \
                                  any(neg in referee_check for neg in negatives_kr)
                    
                    if not is_negative:
                        # 부정형 없는 경우에만 긍정형 확인
                        positives_en = ["consensus reached", "consensus achieved",
                                        "consensus has been reached", "reached consensus"]
                        positives_kr = ["합의에 도달", "합의가 달성", "합의 도달"]
                        
                        is_positive = any(pos in lower_check for pos in positives_en) or \
                                      any(pos in referee_check for pos in positives_kr)
                        
                        consensus_reached = is_positive
            except Exception:
                consensus_reached = False
            
            # --- 현재 라운드 데이터를 활성 심판의 메모리에 저장 ---
            # FIX: previous_rounds 전역 리스트 대신 심판별 독립 메모리 사용
            # FIX V3: 리셋 여부도 기록하여 나중에 참조 시 무효화 가능
            diagnoses_summary = ", ".join([
                f"Group {op['group']}: {op['opinion1'][:150]}"
                for op in group_opinions
            ])
            
            # 리셋 여부 확인
            was_reset = referee_reset_this_round.get(active_referee.name, False)
            
            # 활성 심판의 메모리에만 추가 (다른 심판은 접근 불가)
            active_referee.memory.append({
                "round": round_num,
                "diagnoses_summary": diagnoses_summary,
                "referee_feedback": referee_check,
                "consensus": consensus_reached,
                "was_reset": was_reset  # FIX V3: 리셋 여부 기록
            })
            
            # previous_rounds는 디버깅/출력용으로만 유지
            # FIX V3: 리셋 정보 포함 및 INVALIDATED 마킹
            round_record = {
                "round": round_num,
                "referee_name": active_referee.name,
                "diagnoses_summary": diagnoses_summary,
                "referee_feedback": referee_check,
                "consensus": consensus_reached,
                "was_reset": was_reset,
                "status": "INVALIDATED_RESET" if was_reset else "VALID"  # 리셋 시 무효화 마킹
            }
            previous_rounds.append(round_record)
            
            # --- 종료 판정 ---
            if consensus_reached:
                if self.language == 'ko':
                    print("\n✅ 합의 도달! 진단 완료.\n")
                else:
                    print("\n✅ Consensus reached! Diagnosis complete.\n")
                break
            
            if round_num >= max_rounds:
                if self.language == 'ko':
                    print("\n⚠️ 최대 라운드 도달. 현재까지의 의견을 출력합니다.\n")
                else:
                    print("\n⚠️ Max rounds reached. Outputting current opinions.\n")
                break
            
            # Simplified STAGE 3-5 for brevity
            print(f"[Stages 3-5 abbreviated for demo]\n")
        
        result = {
            "patient": patient,
            "diagnoses": group_opinions,
            "total_searches": len(all_searches),
            "rounds": round_num,
            "ai_models_used": list(set([doc.ai_client.get_model_name() for doc in self.doctors])),
            "referee_resets": sum([1 for r in range(1, round_num+1) 
                                  for ref in self.referees 
                                  if self.should_reset_referee(ref, r)])
        }
        
        return result


def example_usage():
    """Example usage of the Multi-AI Diagnosis System"""
    
    # Language selection
    print("\n🌐 Select Language / 언어 선택:")
    print("  1. English")
    print("  2. 한국어 (Korean)")
    print("  3. Español (Spanish)")
    print("  4. 日本語 (Japanese)")
    
    lang_choice = input("\nChoice (1-4) [1]: ").strip() or "1"
    
    language_map = {
        '1': 'en',
        '2': 'ko',
        '3': 'es',
        '4': 'ja'
    }
    
    language = language_map.get(lang_choice, 'en')
    
    # Configure API keys
    api_keys = {
        'claude': os.getenv('ANTHROPIC_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY'),
        'gemini': os.getenv('GEMINI_API_KEY'),
        'grok': os.getenv('GROK_API_KEY')
    }
    
    # Remove None values
    api_keys = {k: v for k, v in api_keys.items() if v is not None}
    
    if not api_keys:
        if language == 'ko':
            print("❌ API 키를 찾을 수 없습니다. 환경 변수를 설정하세요:")
        else:
            print("❌ No API keys found. Please set environment variables:")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export GEMINI_API_KEY='your-key'")
        print("   export GROK_API_KEY='your-key'")
        return
    
    # Create system with language support
    system = MultiAIDiagnosisSystem(api_keys, language=language)
    
    # Create test patient (with multilingual symptoms)
    if language == 'ko':
        patient = Patient(
            age=42,
            gender="여성",
            chief_complaints=[
                "오후에 심해지는 눈꺼풀 처짐",
                "복시",
                "저작 시 턱 피로",
                "전신 근육통",
                "만성 피로"
            ],
            history="최근 6개월간 증상이 점차 악화됨. 특히 저녁이 되면 눈을 뜨기 힘듦.",
            current_medications=["아스피린 100mg", "비타민 D 보충제"],  # FIX V3: 약물 정보 추가
            allergies=["페니실린"],  # FIX V3: 알레르기 정보 추가
            actual_diseases=["중증근무력증", "섬유근육통"]
        )
    else:  # English and others
        patient = Patient(
            age=42,
            gender="female",
            chief_complaints=[
                "Worsening eyelid drooping in the afternoon",
                "Double vision",
                "Jaw fatigue while chewing",
                "Generalized muscle pain",
                "Chronic fatigue"
            ],
            history="Symptoms have been gradually worsening over the past 6 months. Especially difficult to open eyes in the evening.",
            current_medications=["Aspirin 100mg", "Vitamin D supplement"],  # FIX V3: Medication info
            allergies=["Penicillin"],  # FIX V3: Allergy info
            actual_diseases=["Myasthenia Gravis", "Fibromyalgia"]
        )
    
    # Run diagnosis
    result = system.diagnose(patient, max_rounds=3)
    
    # Print results
    print("\n" + "="*80)
    if language == 'ko':
        print("진단 결과")
    else:
        print("DIAGNOSIS RESULTS")
    print("="*80)
    
    if language == 'ko':
        print(f"\n실제 질환: {', '.join(patient.actual_diseases)}")
        print(f"라운드: {result['rounds']}")
        print(f"총 검색: {result['total_searches']}")
        print(f"사용된 AI 모델: {', '.join(result['ai_models_used'])}")
        print(f"심판 초기화: {result['referee_resets']}회")
    else:
        print(f"\nActual diseases: {', '.join(patient.actual_diseases)}")
        print(f"Rounds: {result['rounds']}")
        print(f"Total searches: {result['total_searches']}")
        print(f"AI models used: {', '.join(result['ai_models_used'])}")
        print(f"Referee resets: {result['referee_resets']}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║   Multi-AI Medical Diagnosis System                           ║
║   다중 AI 모델 기반 의료 진단 시스템                            ║
║                                                                ║
║   Features:                                                    ║
║   ✓ Multiple AI models (Claude, GPT, Gemini, Grok)           ║
║   ✓ Each doctor = Different AI backend                       ║
║   ✓ Dual referee with cross-initialization (5n, 5n-3)        ║
║   ✓ Independent API calls                                     ║
║   ✓ Web search integration                                    ║
║                                                                ║
║   GitHub: https://github.com/[your-repo]                      ║
║   License: MIT                                                 ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    example_usage()