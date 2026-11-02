# 🧩 KukuAI Daily

**Coleta diária das recompensas LOGIN e CHAT do Kuku AI (Baidu Wenku GenFlowPro), com suporte a várias contas, Qinglong e GitHub Actions.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> A documentação chinesa completa está em [../README.md](../README.md).

## Visão geral

O KukuAI Daily recebe a recompensa de login diário e conclui a tarefa de conversa da atividade de pontos gratuitos do Kuku AI. Em uma execução bem-sucedida, o resultado real de cada conta é exibido. Quando a recompensa diária já foi recebida, a API retorna `reward_point=0`; o script trata isso como um estado idempotente de "já recebido hoje" e não informa pontos novos.

A API de negócio exige um token de sessão com escopo `genflowpro`. Um Cookie da web pode permitir consultas genéricas, mas os endpoints da atividade ainda consideram a sessão inválida. A versão atual `v1.2.0` reproduz a assinatura MD5 do mecanismo oficial e troca o token usando `BDUSS` e `PTOKEN`, sem carregar `genflowengine.dll`. Isso funciona no Windows, Linux, Docker e Qinglong.

## Recursos principais

- Coleta as tarefas diárias `LOGIN` e `CHAT`.
- Trata corretamente a resposta idempotente da atividade.
- Usa `KUKU_COOKIES` para uma conta e `KUKU_TOKENS` para várias.
- Resolve credenciais na ordem: STOKEN configurado, cache local e troca por assinatura MD5 multiplataforma.
- Mascara os valores de BDUSS nos logs.
- Envia notificações opcionais pelo WeCom ou PushPlus.
- Usa somente a biblioteca padrão do Python.

## Preparação das credenciais

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
python kuku_daily.py --token
```

O caminho padrão `--exchange` lê primeiro o banco de Cookies do cliente local. Com `--paste --exchange`, cole um Cookie completo contendo `BDUSS` e `PTOKEN`; a ferramenta faz a troca por assinatura pura em qualquer plataforma. `python kuku_daily.py --token` troca os tokens das contas já configuradas. A ferramenta imprime um valor `KUKU_STOKEN=...`.

## Configuração mínima no Qinglong

1. Envie `kuku_daily.py` para um diretório de scripts do Qinglong.
2. Adicione `KUKU_COOKIES` e o `KUKU_STOKEN` gerado como variáveis de ambiente.
3. Crie uma tarefa agendada a partir da lista de scripts para que o comando seja `task kuku_daily.py`.

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

Para várias contas, use `KUKU_TOKENS`:

```text
principal|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
secundaria|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

Separe as contas por quebras de linha ou `&`. Cada item usa `observação|BDUSS|PTOKEN[|STOKEN]`.

## Configuração mínima no GitHub Actions

Adicione estes Secrets em **Settings → Secrets and variables → Actions**:

| Secret | Obrigatório | Finalidade |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | conta única | Cookie de uma conta |
| `KUKU_STOKEN` | opcional | Token de sessão associado ao Cookie |
| `KUKU_TOKENS` | várias contas | Entradas de várias contas; tem precedência |
| `QYWX_TOKEN` | opcional | Chave do bot WeCom |
| `PLUSPLUS_TOKEN` | opcional | Token do PushPlus |

O workflow incluído é somente manual por padrão. Execute **Actions → KukuAI Daily → Run workflow** para a primeira validação. Para habilitar a agenda, remova o comentário das duas linhas `schedule:` em `.github/workflows/daily.yml`:

```yaml
schedule:
  - cron: '15 0 * * *'
```

O cron usa UTC. `15 0 * * *` corresponde a 08:15 no horário de Pequim. O runner Ubuntu também executa a troca por assinatura pura. `KUKU_STOKEN` pode ser omitido; `KUKU_COOKIES` é trocado em tempo de execução e armazenado em cache.

## Variáveis de ambiente principais

| Variável | Obrigatória | Descrição |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | conta única | Cabeçalho Cookie, JSON do Cookie-editor ou objeto com `BDUSS` e `PTOKEN` |
| `KUKU_STOKEN` | opcional | Token de sessão `genflowpro` já emitido |
| `KUKU_TOKENS` | várias contas | Lista no formato `observação\|BDUSS\|PTOKEN[\|STOKEN]` |
| `KUKU_PROXY` | opcional | URL de proxy HTTP(S) ou SOCKS5 |
| `KUKU_NO_NOTIFY` | opcional | Defina como `1` para desativar notificações |
| `QYWX_TOKEN` | opcional | Chave do bot WeCom; `WECHAT_WEBHOOK` também é aceito |
| `PLUSPLUS_TOKEN` | opcional | Token do PushPlus |

## Opções de linha de comando

| Opção | Efeito |
| :--- | :--- |
| nenhuma | Executa as tarefas diárias em todas as contas configuradas |
| `--only N` | Executa somente a conta número N |
| `--token` | Apenas troca e exibe os tokens de sessão, sem fazer check-in |

## Escopo de verificação

O README anterior registra 13 testes offline que cobrem análise de Cookie, cabeçalhos, precedência de credenciais, sucesso, respostas idempotentes, sessão expirada, falhas HTTP, várias contas e mascaramento de logs. A versão `v1.2.0` substituiu a chamada DLL pela troca com assinatura MD5 pura. O repositório não inclui um log online de ponta a ponta com conta real para esse novo caminho, portanto não declara aceitação online.

## Privacidade

Cookie, STOKEN e a lista de contas são lidos apenas de variáveis de ambiente ou do cache local de tokens. Os logs mostram somente fragmentos mascarados do BDUSS. Não publique `.kuku_stoken.json`, valores de variáveis de ambiente ou Cookies completos em repositórios, Issues, logs do Actions ou capturas de tela.

## Limites de uso e redistribuição

O repositório oficial, os scripts, as instruções de implantação e as Releases permanecem gratuitos e públicos. Sem autorização escrita explícita do autor, não empacote este projeto como recurso pago, serviço de implantação paga ou serviço de atualização paga; não remova a atribuição para alegar autoria original; não se passe pelo autor; e não use a identidade, o nome, o avatar ou os QR codes de pagamento do autor para sugerir endosso oficial. Também não republique o projeto em contas, grupos, canais ou plataformas pagas sem relação com ele para ganhar seguidores, desviar tráfego ou revender. Em caso de violação, o autor pode solicitar a remoção e pode pausar atualizações, arquivar ou excluir o repositório. Consulte as regras completas em [NOTICE.md](../NOTICE.md).

## Links

- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)
- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [README em chinês](../README.md)
- [Histórico de alterações](../CHANGELOG.md)

## Aviso

Este projeto é destinado a aprendizado pessoal e automação. Respeite os termos do Kuku AI, Baidu Wenku e serviços relacionados. O uso é por sua conta e risco.
