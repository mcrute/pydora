Integração Ultramsg (WhatsApp)
=================================

Este repositório inclui um cliente mínimo para enviar mensagens via Ultramsg
e uma aplicação Flask de exemplo para receber webhooks.

Configuração (variáveis de ambiente)
------------------------------------

- ULTRAMSG_INSTANCE: ID da sua instância Ultramsg
- ULTRAMSG_TOKEN: token da API Ultramsg
- ULTRAMSG_API_URL: (opcional) URL base da API. Padrão: https://api.ultramsg.com
- ULTRAMSG_AUTO_REPLY: (opcional) texto a ser enviado automaticamente ao receber uma mensagem

Executando a app de webhook
--------------------------

1. Instale dependências (recomendado num virtualenv):

   pip install flask requests

2. Exporte as variáveis de ambiente (Windows exemplo):

   set ULTRAMSG_INSTANCE=SEU_INSTANCE_ID
   set ULTRAMSG_TOKEN=SEU_TOKEN
   set FLASK_APP=pydora.webhook

3. Rode a aplicação Flask:

   flask run --host=0.0.0.0 --port=5000

Rotas úteis
-----------

- POST /send  -> Envia mensagem. JSON: {"to": "5511999...", "body": "texto"}
- POST /webhook/whatsapp -> Recebe callbacks do Ultramsg (configurar no painel Ultramsg)

Segurança
--------

- Não comite credenciais no repositório. Use variáveis de ambiente ou um cofre de segredos.
- Quando expor o webhook à internet, proteja com TLS e, se possível, validação adicional
  (token compartilhado, assinatura HMAC, IP allowlist).

Observações
-----------

- O cliente implementado é mínimo e focado em enviar mensagens de texto.
- Se desejar, pode-se estender para suportar templates, mídia e parsing avançado dos webhooks.
