// Cloudflare Pages Function: POST /api/leads
// Recebe lotes de respostas do tablet e grava no Neon (idempotente pelo id).
// Sem dependências: usa a API HTTP do Neon diretamente.
// Variáveis no painel da Cloudflare (Settings > Variables and Secrets, tipo "Secret"):
//   DATABASE_URL  -> connection string do usuário pesquisa_writer (só pode gravar)
//   LEADS_TOKEN   -> token longo, o mesmo digitado na tela CONFIGURAR do iPad

const MAX_BATCH = 100;
const s = (v, n) => (v == null ? '' : String(v)).trim().slice(0, n);

function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

// ep-xxx-pooler.c-2.sa-east-1.aws.neon.tech -> https://api.c-2.sa-east-1.aws.neon.tech/sql
function sqlEndpoint(databaseUrl) {
  const host = new URL(databaseUrl).hostname;
  return 'https://' + host.replace(/^[^.]+\./, 'api.') + '/sql';
}

async function query(env, text, params) {
  const res = await fetch(sqlEndpoint(env.DATABASE_URL), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Neon-Connection-String': env.DATABASE_URL },
    body: JSON.stringify({ query: text, params }),
  });
  if (!res.ok) throw new Error(`neon ${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

const INSERT = `
  INSERT INTO pesquisa_campo (
    id, respondido_em, local_acao, dispositivo, objetivo, prazo, valor_estimado,
    conhece_consorcio, interesse, nome, whatsapp, email, aceite_contato, aceite_texto
  ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
  ON CONFLICT (id) DO NOTHING`;

export async function onRequestPost({ request, env }) {
  if (!env.LEADS_TOKEN || !env.DATABASE_URL) {
    return new Response('servidor nao configurado', { status: 503 });
  }
  if (!safeEqual(request.headers.get('X-Device-Token') || '', env.LEADS_TOKEN)) {
    return new Response('unauthorized', { status: 401 });
  }

  let body;
  try { body = await request.json(); } catch { return new Response('bad json', { status: 400 }); }
  const recs = Array.isArray(body?.records) ? body.records.slice(0, MAX_BATCH) : [];
  const ok = [];

  for (const r of recs) {
    const id = s(r.id, 64);
    const quando = new Date(r.respondido_em);
    if (!id || isNaN(quando)) continue;
    try {
      await query(env, INSERT, [
        id, quando.toISOString(), s(r.local_acao, 60), s(r.dispositivo, 30),
        s(r.objetivo, 60), s(r.prazo, 40), s(r.valor, 40) || null, s(r.consorcio, 40),
        s(r.interesse, 10), s(r.nome, 80) || null,
        s(r.whatsapp, 20).replace(/\D/g, '') || null,
        s(r.email, 120).toLowerCase() || null,
        r.aceite === true, s(r.aceite_texto, 400) || null,
      ]);
      ok.push(id); // já existente também conta: o tablet marca como enviado
    } catch (e) {
      console.error('insert falhou', id, e.message);
    }
  }
  return Response.json({ ok });
}

