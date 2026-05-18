# Econpost / E-Com Plus — Skills para Claude Code

Conjunto de skills para o Claude Code interagir com a API REST da E-Com Plus, focado em relatórios, edição de lojas/produtos/clientes e diagnóstico de integrações (Bling, Pagar.me, etc.). O objetivo final é embedar isso numa interface chat-like para os usuários da plataforma.

---

## Arquitetura das skills

Cada skill é uma pasta independente com um `SKILL.md` (frontmatter `name` + `description`) que o Claude carrega *só quando o gatilho da description casar*. Isso é importante: skills pequenas e focadas funcionam melhor do que uma skill gigante, porque o Claude consegue decidir com mais precisão qual usar.

### Roadmap sugerido (em ordem de prioridade)

```
ecomplus-skills/
├── ecomplus-reports/         ✅ pronto (esta primeira entrega)
│   └── Relatórios de vendas, estoque, financeiro, top produtos
│
├── ecomplus-auth/            🔲 próxima
│   └── Como autenticar (X-Store-ID, X-Access-Token, X-My-ID, refresh)
│
├── ecomplus-orders/          🔲
│   └── Buscar, listar, atualizar status de pedidos
│
├── ecomplus-products/        🔲
│   └── CRUD de produtos, variações, estoque, preços
│
├── ecomplus-customers/       🔲
│   └── CRUD de clientes, endereços, histórico de compras
│
├── ecomplus-stores/          🔲
│   └── Configurações da loja, pagamento, frete
│
└── ecomplus-integrations/    🔲
    └── Diagnóstico Bling, Pagar.me, webhooks, logs Cloud Run
```

Por que `ecomplus-auth` é a segunda e não a primeira? Porque a `ecomplus-reports` já incorpora o mínimo de autenticação que ela precisa, mas autenticação merece skill própria porque é transversal (todas as outras vão referenciar). Crie-a logo após validar a `reports`.

---

## Anatomia de uma skill (formato canônico)

```
nome-da-skill/
├── SKILL.md           ← obrigatório. Frontmatter + instruções
├── scripts/           ← scripts executáveis (Python, Node, Bash)
├── references/        ← docs carregados sob demanda
└── assets/            ← templates, imagens, JSONs de exemplo
```

**Regra de ouro do SKILL.md:**
- A `description` no frontmatter é o que decide *quando* a skill é usada. Seja específico e cheio de gatilhos. Não economize palavras-chave.
- O corpo do SKILL.md deve ter < 500 linhas. Conteúdo extenso vai pra `references/` e é carregado sob demanda.
- "Progressive disclosure": Claude lê só a metadata sempre, o corpo quando a skill ativa, e references só quando o corpo manda ler.

### Exemplo de description fraca vs forte

❌ Fraca: *"Gera relatórios de vendas."*

✅ Forte: *"Use esta skill SEMPRE que o usuário pedir relatórios, métricas ou análises de uma loja E-Com Plus — vendas por período, ticket médio, top produtos, conversão, estoque crítico, faturamento. Gatilhos: 'relatório', 'vendas do mês', 'quanto faturei', 'produtos mais vendidos', 'estoque baixo', 'curva ABC', 'comparar períodos'. Funciona com store_id da plataforma Econpost/E-Com Plus."*

A versão forte tem: o que faz, quando usar, gatilhos linguísticos típicos do usuário, contexto da plataforma.

---

## Como o Claude Code carrega skills

No Claude Code, você coloca a pasta em `~/.claude/skills/` (ou no path configurado). O Claude vê todas as descriptions no system prompt e decide qual `SKILL.md` ler com base na intent do usuário.

Para a sua interface chat embedada futura: você vai usar a API do Anthropic com o parâmetro `skills` (ou um system prompt que descreva quando acionar cada uma) e expor as ferramentas que as skills assumem disponíveis — basicamente `bash_tool` ou um wrapper HTTP equivalente.

---

## Decisões de design importantes

1. **API REST oficial, não acesso direto ao banco.** Mais lento em alguns casos, mas seguro (respeita as regras de negócio da plataforma) e funciona em qualquer ambiente sem credenciais de infra.

2. **Cada skill assume autenticação resolvida.** Os scripts esperam variáveis de ambiente (`ECOMPLUS_STORE_ID`, `ECOMPLUS_ACCESS_TOKEN`, `ECOMPLUS_MY_ID`). Isso vai ser preenchido pela `ecomplus-auth` ou pelo backend da sua interface.

3. **Saídas em tabela markdown por padrão**, com opção de CSV/JSON. Por que? A interface chat renderiza markdown bem, e o usuário final da Econpost quer ver "quanto vendi essa semana", não JSON.

4. **Rate limit awareness.** A API E-Com Plus aceita ~6 req/s autenticadas. Scripts implementam retry com backoff e batch quando possível.

---

## Próximos passos depois da primeira skill

1. Testar a `ecomplus-reports` num caso real (uma loja sua, sandbox preferencialmente)
2. Validar o formato de saída com você
3. Iterar a description se ela não disparar nos prompts que você espera
4. Criar a `ecomplus-auth` separada
5. Replicar o padrão para `orders`, `products`, etc.

Depois disso, a interface chat embedada vira basicamente: API Anthropic + as skills + uma camada fina de auth/UI.
