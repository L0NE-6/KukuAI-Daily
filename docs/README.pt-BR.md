# 🧩 KukuAI Daily

**Script de arquivo único para o check-in de 30 dias do Kuku AI, com várias contas, Qinglong e GitHub Actions.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> A documentação chinesa completa está em [../README.md](../README.md).

## Visão geral

O KukuAI Daily executa a atividade de 30 dias chamando, em ordem, a configuração, a página inicial da atividade, o token JS e o endpoint de check-in. As tarefas antigas de pontos só são executadas com `--legacy-freepoint` explícito; não há fallback automático.

O check-in só é bem-sucedido quando a resposta contém `errno=0` e `data.signed_today=true` como booleano. `errno=10152` é um estado neutro de já assinado; `8001` e `8002` são falhas de controle de risco do servidor.

## Fluxo de requisições

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

O Referer é sempre:

```text
https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

## Dois STOKEN separados

| Token | Origem | Uso |
| :--- | :--- | :--- |
| Web STOKEN | `STOKEN` dentro do Cookie completo | Apenas o check-in de 30 dias |
| Business STOKEN | `KUKU_STOKEN`, `business_stoken` por conta, cache ou troca | Apenas `--legacy-freepoint` |

`KUKU_STOKEN` nunca substitui o Web STOKEN. Se o Cookie não tiver Web STOKEN, o fluxo padrão falha e pede para exportar o Cookie completo novamente; ele não troca silenciosamente para o token de negócio.

## Conta única

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

O Business STOKEN opcional é usado somente pelo fluxo legado:

```text
KUKU_STOKEN=<business-stoken>
```

## Várias contas

O formato recomendado é um array JSON. O Cookie completo fica em `cookie` e o token legado em `business_stoken`:

```json
[
  {
    "name": "principal",
    "cookie": "BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  },
  {
    "name": "secundaria",
    "cookie": "BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

Também é possível usar uma linha por conta:

```text
principal|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|business-stoken-opcional
secundaria|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|business-stoken-opcional
```

O formato antigo `nome|BDUSS|PTOKEN[|business-stoken]` continua aceito por compatibilidade, mas não contém Web STOKEN nem os outros campos do navegador. Ele serve apenas para `--legacy-freepoint`; o fluxo padrão reporta a falta do Web STOKEN.

## Qinglong e GitHub Actions

1. Envie `kuku_daily.py`; envie também `kuku_get_cookie.py` quando precisar atualizar Cookies do cliente.
2. Configure `KUKU_COOKIES` para uma conta ou `KUKU_TOKENS` para várias.
3. Execute `task kuku_daily.py` em um agendamento.

```cron
15 8 * * *
```

| Secret | Obrigatório | Finalidade |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | conta única | Cookie completo com Web STOKEN |
| `KUKU_TOKENS` | várias contas | Array JSON ou formato por linhas |
| `KUKU_STOKEN` | opcional | Business STOKEN legado apenas para conta única |
| `QYWX_TOKEN` | opcional | Chave do bot WeCom |
| `PLUSPLUS_TOKEN` | opcional | Token do PushPlus |

## Linha de comando

| Opção | Efeito |
| :--- | :--- |
| nenhuma | Executa o check-in de 30 dias em todas as contas |
| `--only N` | Executa somente a conta N |
| `--legacy-freepoint` | Executa o fluxo freepoint antigo com Business STOKEN |
| `--token` | Troca e imprime o Business STOKEN legado sem fazer check-in |
| `--version` | Mostra a versão do script |

## Critérios de sucesso

| Resultado do servidor | Tratamento local |
| :--- | :--- |
| `errno=0`, `data.signed_today=true` | Sucesso |
| Página inicial `signed_today=true` | Neutro, já assinado |
| `errno=10152` | Neutro, já assinado |
| `errno=8001` / `8002` | Falha de controle de risco |
| `signed_today` ausente ou não booleano | Falha |

## Verificação

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

Os testes usam apenas respostas falsas. Cobrem o fluxo de quatro etapas, sucesso estrito, 10152, 8001/8002, modo legado explícito, separação Web/Business STOKEN, Cookies completos de várias contas, mascaramento e notificações. Consulte [PROTOCOL.md](PROTOCOL.md).

## Privacidade

Os logs mascaram o BDUSS. Não publique `.kuku_stoken.json`, Cookies completos, STOKEN ou arquivos de exportação de contas.

## Uso e redistribuição

O repositório oficial, scripts, instruções e Releases permanecem gratuitos. Sem autorização escrita, não venda o projeto, não ofereça implantação paga, não remova a atribuição, não se passe pelo autor e não use a identidade ou QR codes do autor para sugerir endosso oficial. Consulte [NOTICE.md](../NOTICE.md).

## Versão

- Versão do repositório: `v1.3.0`
- Release: será publicada pelo fluxo principal
- Histórico: [CHANGELOG.md](../CHANGELOG.md)

## Aviso

Este projeto é destinado a aprendizado pessoal e automação. Respeite os termos do Kuku AI, Baidu Wenku e serviços relacionados. O uso é por sua conta e risco.
