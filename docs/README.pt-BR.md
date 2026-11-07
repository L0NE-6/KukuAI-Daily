# KukuAI Daily

**Script de arquivo único para o check-in diário atual `kukuai30` do Kuku AI, com suporte a várias contas, Qinglong e GitHub Actions.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

## Visão geral

O fluxo padrão lê a identidade da sessão, consulta o painel e envia uma única ação de signin somente quando necessário. Depois ele lê o painel novamente. O único critério de sucesso é `signed_today=true` na leitura posterior.

As tarefas antigas de freepoint só são executadas com `--legacy-freepoint` explícito. O fluxo padrão nunca muda automaticamente para a API antiga.

## Fluxo de requisições

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk` vem de `userreport.data.uk`. O painel fixo usa `tid=291651792210`. Os parâmetros aposentados `getJsToken`, `activityTid`, `aid=15459` e `jsToken` não são usados.

## Credenciais

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

Para várias contas, use um array JSON:

```json
[
  {
    "name": "principal",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

Quando `PTOKEN` existe, o script troca por um STOKEN de negócio `genflowpro`. Falhas nessa troca são reportadas explicitamente. `KUKU_STOKEN` / `business_stoken` continuam exclusivos dos caminhos legados e `--token`.

## Critérios de sucesso

| Estado do painel | Resultado |
| :--- | :--- |
| `signed_today=true` antes do signin | Neutro, já assinado; não envia ação |
| `signed_today=true` após o signin | Check-in concluído |
| Continua `false` após o signin | Falha; mostra o motivo da ação |
| Ação retorna `10152`, mas a leitura segue false | Falha |
| Ação retorna `8001` | Mostra a rejeição do servidor |
| `uk`, `data` ou formato inválido | Falha |

HTTP 200, `errno=0` da ação e `errno=10152` não bastam para confirmar sucesso.

## Execução e verificação

```text
python kuku_daily.py
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

## Privacidade e redistribuição

Nunca publique Cookies completos, STOKEN, `.kuku_stoken.json`, exportações de contas ou capturas com credenciais. O repositório oficial e as Releases são gratuitos. Não venda, reempacote, finja ser o autor nem use a identidade ou QR de pagamento do autor para sugerir aprovação oficial. Consulte [NOTICE.md](../NOTICE.md).

## Versão

- Versão do repositório: `v1.4.0`
- Histórico: [CHANGELOG.md](../CHANGELOG.md)

Este projeto é destinado à automação pessoal. Siga os termos aplicáveis e use por sua conta e risco.
