"""
Aplicação Flask mínima para receber webhooks do Ultramsg e endpoint de envio.

Uso:
  - Defina ULTRAMSG_INSTANCE e ULTRAMSG_TOKEN como variáveis de ambiente.
  - Rode: set FLASK_APP=pydora.webhook; flask run  (Windows)

Rotas:
  POST /send
    JSON: {"to": "5511999...", "body": "mensagem"}

  POST /webhook/whatsapp
    Recebe posts do Ultramsg. A carga é armazenada em logs e retornada.
"""

from __future__ import annotations

import os
import logging
from flask import Flask, request, jsonify
from .ultramsg import UltramsgClient

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/send', methods=['POST'])
def send_message():
    payload = request.get_json() or {}
    to = payload.get('to')
    body = payload.get('body')
    if not to or not body:
        return jsonify({'error': 'invalid payload, require to and body'}), 400

    client = UltramsgClient()
    try:
        res = client.send_text(to, body)
    except Exception as exc:
        app.logger.exception('Falha ao enviar mensagem')
        return jsonify({'error': str(exc)}), 500

    return jsonify({'result': res})


@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    # Ultramsg pode enviar form-encoded ou JSON dependendo da configuração.
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()

    app.logger.info('Webhook Ultramsg recebido: %s', data)

    # Exemplo de auto-resposta opcional: se ULTRAMSG_AUTO_REPLY estiver definida,
    # envia uma resposta simples de volta para o remetente quando possível.
    auto_reply = os.getenv('ULTRAMSG_AUTO_REPLY', '')
    if auto_reply:
        sender = data.get('from') or data.get('sender') or data.get('wa_id')
        if sender:
            try:
                client = UltramsgClient()
                client.send_text(sender, auto_reply)
            except Exception:
                app.logger.exception('Falha enviando auto-reply')

    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # Execução local para testes: definir FLASK_APP=pydora.webhook e rodar flask.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
