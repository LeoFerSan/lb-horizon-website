LB Horizon Landing Page V1.3 (PT / EN / ES) — com SEO

COMO O SITE ESTÁ ORGANIZADO
- src/index.html ...... ARQUIVO-FONTE. Todos os textos ficam no bloco I18N, no script ao
                        final dele, separados por idioma (en, pt, es). Edite sempre aqui.
- build.py ............ gera as páginas publicadas a partir do src/index.html.
- index.html .......... página em português (gerada; não edite à mão)
- en/index.html ....... página em inglês (gerada)
- es/index.html ....... página em espanhol (gerada)
- sitemap.xml ......... lista das páginas para o Google (gerada)
- robots.txt .......... instruções para buscadores
- og-image.png ........ imagem que aparece ao compartilhar o link (WhatsApp, LinkedIn...)
- logo.png ............ logo usada nos dados estruturados do Google

PARA ALTERAR UM TEXTO
1. Edite o texto nos três idiomas no bloco I18N de src/index.html.
2. Rode:  python3 build.py
3. Faça commit de tudo (src, index.html, en/, es/, sitemap.xml) e envie ao GitHub.

IDIOMAS
- Cada idioma tem a sua própria URL: lbhorizon.com.br/ (PT), /en/ e /es/.
  Isso permite que o Google indexe as três versões.
- O seletor PT / EN / ES leva à URL do idioma e lembra a escolha do visitante.

DADOS DA EMPRESA PARA O GOOGLE
- Telefone, e-mail, cidade, data de abertura e perfis sociais ficam no topo do build.py
  (BUSINESS). Quando tiver as URLs do LinkedIn e do Instagram da empresa, coloque-as
  em "sameAs" e rode o build de novo.

WHATSAPP
- Número: 5521983769654. Para trocar, edite a variável WHATSAPP_NUMBER e o link do botão
  em src/index.html e rode o build.

PESQUISA DE CAMPO ADEMICON (iPad 2)
- pesquisa/index.html ........ página da pesquisa (lbhorizon.com.br/pesquisa/), funciona offline
- pesquisa/pesquisa.appcache . cache offline do iPad. Ao alterar o index.html, mude a linha "# v3".
- functions/api/leads.js ..... função da Cloudflare (POST /api/leads) que grava no Neon,
                               projeto "Dashboard Ademicon", tabela pesquisa_campo.
- _headers ................... cabeçalhos do cache offline
- Variáveis secretas no projeto Pages (Settings > Variables and Secrets):
  DATABASE_URL (usuário pesquisa_writer, só grava) e LEADS_TOKEN (mesmo token do iPad).
- O build.py não mexe nesses arquivos.
