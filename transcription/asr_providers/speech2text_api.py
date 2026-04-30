from __future__ import annotations

import mimetypes
import os
import time
from datetime import datetime

import requests

from .base import AsrError, AsrRequest, AsrResult


PROVIDER_ID = "speech2text-transcriptions"
PROVIDER_VERSION = "speech2text-api-v1"
DEFAULT_BASE_URL = "https://speech2text.ru/api"
DEFAULT_TIMEOUT_SEC = 120
DEFAULT_POLL_INTERVAL_SEC = 5
DEFAULT_MAX_WAIT_SEC = 1800


class Speech2TextApiProvider:
    provider_id = PROVIDER_ID

    def __init__(self, *, model: str, device: str, compute_type: str) -> None:
        # Keep the same constructor signature as other providers.
        self.model = model
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, request: AsrRequest) -> AsrResult:
        audio_path = request.audio_path
        if not audio_path.is_file():
            raise AsrError(
                category="input_not_found",
                message=f"Audio file not found: {audio_path}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=False,
            )

        runtime = request.runtime_options or {}
        base_url = str(runtime.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
        timeout_sec = int(runtime.get("timeout_sec") or DEFAULT_TIMEOUT_SEC)
        poll_interval_sec = int(runtime.get("poll_interval_sec") or DEFAULT_POLL_INTERVAL_SEC)
        max_wait_sec = int(runtime.get("max_wait_sec") or DEFAULT_MAX_WAIT_SEC)
        result_format = str(runtime.get("result_format") or "txt")
        api_key_env = str(runtime.get("api_key_env") or "SPEECH2TEXT_API_KEY")
        api_key = os.environ.get(api_key_env, "").strip()
        if not api_key:
            raise AsrError(
                category="auth_error",
                message=f"Missing API key in env var: {api_key_env}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=False,
                details={"api_key_env": api_key_env},
            )

        create_task_endpoint = f"{base_url}/recognitions/task/file"
        mime_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        data = {
            "language": request.language or "ru",
            "lang": request.language or "ru",
        }
        speakers = runtime.get("speakers")
        if speakers is not None:
            data["speakers"] = str(speakers)

        task_id: str | None = None
        try:
            with audio_path.open("rb") as f:
                files = {"file": (audio_path.name, f, mime_type)}
                response = requests.post(
                    f"{create_task_endpoint}?api-key={api_key}",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=timeout_sec,
                )
        except requests.Timeout as exc:
            raise AsrError(
                category="timeout",
                message=str(exc),
                provider_id=self.provider_id,
                model=self.model,
                retryable=True,
                details={"endpoint": create_task_endpoint, "timeout_sec": timeout_sec},
            ) from exc
        except requests.RequestException as exc:
            raise AsrError(
                category="network_error",
                message=str(exc),
                provider_id=self.provider_id,
                model=self.model,
                retryable=True,
                details={"endpoint": create_task_endpoint},
            ) from exc

        if response.status_code not in (200, 201):
            category, retryable = self._http_error_category(response.status_code)
            raise AsrError(
                category=category,
                message=f"HTTP {response.status_code}: {response.text[:500]}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=retryable,
                details={"http_status": response.status_code, "endpoint": create_task_endpoint},
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise AsrError(
                category="api_error",
                message=f"Invalid JSON in task create response: {response.text[:500]}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=True,
                details={"endpoint": create_task_endpoint},
            ) from exc

        if isinstance(payload, dict):
            raw_id = payload.get("id")
            if raw_id is not None:
                task_id = str(raw_id)
        if not task_id:
            raise AsrError(
                category="api_error",
                message=f"Task id not found in response: {response.text[:500]}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=True,
                details={"endpoint": create_task_endpoint},
            )

        self._wait_for_task_complete(
            base_url=base_url,
            api_key=api_key,
            task_id=task_id,
            headers=headers,
            timeout_sec=timeout_sec,
            poll_interval_sec=poll_interval_sec,
            max_wait_sec=max_wait_sec,
            model=self.model,
        )

        transcript = self._fetch_result(
            base_url=base_url,
            api_key=api_key,
            task_id=task_id,
            result_format=result_format,
            headers=headers,
            timeout_sec=timeout_sec,
            model=self.model,
        )

        quality_flags: list[str] = []
        if not transcript:
            quality_flags.append("empty_output")

        return AsrResult(
            text=transcript,
            segments=[],
            language_detected=request.language,
            duration_sec=None,
            provider_id=self.provider_id,
            provider_version=PROVIDER_VERSION,
            model=self.model,
            runtime_options_effective={
                **runtime,
                "base_url": base_url,
                "timeout_sec": timeout_sec,
                "poll_interval_sec": poll_interval_sec,
                "max_wait_sec": max_wait_sec,
                "result_format": result_format,
                "api_key_env": api_key_env,
            },
            quality_flags=quality_flags,
            usage={"task_id": task_id},
            artifacts=[f"{base_url}/recognitions/{task_id}"],
            created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )

    def _wait_for_task_complete(
        self,
        *,
        base_url: str,
        api_key: str,
        task_id: str,
        headers: dict[str, str],
        timeout_sec: int,
        poll_interval_sec: int,
        max_wait_sec: int,
        model: str,
    ) -> None:
        status_url = f"{base_url}/recognitions/{task_id}?api-key={api_key}"
        started = time.time()
        while True:
            if time.time() - started > max_wait_sec:
                raise AsrError(
                    category="timeout",
                    message=f"Task {task_id} not completed in {max_wait_sec}s",
                    provider_id=self.provider_id,
                    model=model,
                    retryable=True,
                    details={"task_id": task_id, "status_url": status_url},
                )
            try:
                response = requests.get(status_url, headers=headers, timeout=timeout_sec)
            except requests.Timeout as exc:
                raise AsrError(
                    category="timeout",
                    message=str(exc),
                    provider_id=self.provider_id,
                    model=model,
                    retryable=True,
                    details={"task_id": task_id, "status_url": status_url},
                ) from exc
            except requests.RequestException as exc:
                raise AsrError(
                    category="network_error",
                    message=str(exc),
                    provider_id=self.provider_id,
                    model=model,
                    retryable=True,
                    details={"task_id": task_id, "status_url": status_url},
                ) from exc

            if response.status_code != 200:
                category, retryable = self._http_error_category(response.status_code)
                raise AsrError(
                    category=category,
                    message=f"HTTP {response.status_code}: {response.text[:500]}",
                    provider_id=self.provider_id,
                    model=model,
                    retryable=retryable,
                    details={"task_id": task_id, "status_url": status_url},
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise AsrError(
                    category="api_error",
                    message=f"Invalid JSON in status response: {response.text[:500]}",
                    provider_id=self.provider_id,
                    model=model,
                    retryable=True,
                    details={"task_id": task_id, "status_url": status_url},
                ) from exc

            status = payload.get("status")
            if not isinstance(status, dict):
                raise AsrError(
                    category="api_error",
                    message=f"Missing status in response: {response.text[:500]}",
                    provider_id=self.provider_id,
                    model=model,
                    retryable=True,
                    details={"task_id": task_id, "status_url": status_url},
                )
            code_raw = status.get("code")
            code = int(code_raw) if isinstance(code_raw, (int, str)) and str(code_raw).isdigit() else None
            if code == 200:
                return
            if code == 501:
                raise AsrError(
                    category="decode_failed",
                    message=f"Recognition failed (status=501): {status}",
                    provider_id=self.provider_id,
                    model=model,
                    retryable=False,
                    details={"task_id": task_id, "status": status},
                )
            time.sleep(max(1, poll_interval_sec))

    def _fetch_result(
        self,
        *,
        base_url: str,
        api_key: str,
        task_id: str,
        result_format: str,
        headers: dict[str, str],
        timeout_sec: int,
        model: str,
    ) -> str:
        result_url = f"{base_url}/recognitions/{task_id}/result/{result_format}?api-key={api_key}"
        try:
            response = requests.get(result_url, headers=headers, timeout=timeout_sec)
        except requests.Timeout as exc:
            raise AsrError(
                category="timeout",
                message=str(exc),
                provider_id=self.provider_id,
                model=model,
                retryable=True,
                details={"task_id": task_id, "result_url": result_url},
            ) from exc
        except requests.RequestException as exc:
            raise AsrError(
                category="network_error",
                message=str(exc),
                provider_id=self.provider_id,
                model=model,
                retryable=True,
                details={"task_id": task_id, "result_url": result_url},
            ) from exc

        if response.status_code != 200:
            category, retryable = self._http_error_category(response.status_code)
            raise AsrError(
                category=category,
                message=f"HTTP {response.status_code}: {response.text[:500]}",
                provider_id=self.provider_id,
                model=model,
                retryable=retryable,
                details={"task_id": task_id, "result_url": result_url},
            )
        return response.text.strip()

    @staticmethod
    def _http_error_category(status_code: int) -> tuple[str, bool]:
        if status_code in (401, 403):
            return "auth_error", False
        if status_code == 402:
            return "quota_exceeded", False
        if status_code == 429:
            return "rate_limited", True
        if status_code in (408,):
            return "timeout", True
        if status_code >= 500:
            return "api_error", True
        return "api_error", False
