"""
Cliente simples para Ultramsg (WhatsApp) usando variáveis de ambiente.
Configuração via variáveis de ambiente:
- ULTRAMSG_INSTANCE: ID da instância Ultramsg
- ULTRAMSG_TOKEN: token de API
- ULTRAMSG_API_URL: (opcional) URL base da API, padrão https://api.ultramsg.com

Este módulo não comete segredos em código: leia as credenciais de env.
"""

from __future__ import annotations

import os
import requests
from typing import Any, Dict


class UltramsgClient:
    """Cliente mínimo para enviar mensagens de texto via Ultramsg.

    Exemplo:
        client = UltramsgClient()
        client.send_text('5511999999999', 'Olá do Base44!')
    """

    def __init__(self, instance: str | None = None, token: str | None = None, api_url: str | None = None):
        self.instance = instance or os.getenv('ULTRAMSG_INSTANCE')
        self.token = token or os.getenv('ULTRAMSG_TOKEN')
        self.api_url = api_url or os.getenv('ULTRAMSG_API_URL', 'https://api.ultramsg.com')

        if not self.instance or not self.token:
            raise ValueError('ULTRAMSG_INSTANCE and ULTRAMSG_TOKEN must be set in env or passed explicitly')

    def _endpoint(self, path: str) -> str:
        return f"{self.api_url}/{self.instance}{path}"

    def send_text(self, to: str, body: str, timeout: int = 10) -> Dict[str, Any]:
        """Envia uma mensagem de texto.

        Args:
            to: número no formato internacional sem +, ex: 5511999999999
            body: texto da mensagem

        Returns:
            Decodificação JSON da resposta do Ultramsg.
        """
        url = self._endpoint('/messages/chat')
        payload = {
            'token': self.token,
            'to': to,
            'body': body,
        }

        resp = requests.post(url, data=payload, timeout=timeout)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            # tentar devolver corpo em caso de erro para diagnóstico
            raise
        return resp.json()


__all__ = ['UltramsgClient']
