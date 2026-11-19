# CampoConecta integrado

A demonstração local inicia a API, o portal e a Fábrica de Corpus. O portal usa a mesma API para relatos, revisão, RPA, análise de pavimentação e assistente de chuvas. O iniciador escuta nas portas locais 18000, 18501 e 18502 e guarda o banco, o .eml e os logs em `.demonstracao/`. O perfil é para dados sintéticos e prepara e-mails para a outbox local.

## Iniciar no Windows

1. Abra a pasta `CampoConecta_Integrado` e execute **Iniciar CampoConecta.cmd**. Também é possível iniciar pelo PowerShell com `uv run --no-project --python 3.12 python iniciar_integrado.py`.
2. Abra http://127.0.0.1:18501 no navegador se ele não abrir sozinho. A primeira execução instala as dependências em ambiente isolado e precisa de internet. As demais reutilizam o ambiente.
3. Mantenha a janela do terminal aberta durante a demonstração. Use Ctrl+C para encerrar. Se uma porta estiver ocupada, acrescente `--porta-api 18010 --porta-web 18511 --porta-pln 18512` ao comando.

O chat funciona por busca extrativa com citações assim que o portal inicia. Para ativar o modelo Qwen original em CPU, rode `powershell -NoProfile -ExecutionPolicy Bypass -File ./docs/generative-ai/rodar-modelo-windows.ps1` em outro terminal, aguarde o servidor informar que está pronto e adicione `--com-modelo` ao iniciador. O primeiro uso do modelo baixa aproximadamente 1,1 GB, com verificação de SHA-256. O perfil de demonstração usa regras para a triagem de relatos e o Qwen, quando selecionado, apenas no assistente.

## Demonstração

| Tela | Ação |
|---|---|
| Relatar problema | Envie “A bomba do poço quebrou e a horta está sem água desde ontem”, deixando o CEP em branco. Guarde o protocolo. |
| Painel do gestor | Aprove o mesmo relato. Processe o lote de exemplo e confira o arquivo em `.demonstracao/outbox/`. |
| Análise de pavimentação | Use `entregas_externas/visao/demonstracao/imagens/India_008389.jpg`. A outra imagem fornecida, India_000145.jpg, serve como exemplo sem detecção. |
| Chuvas e enchentes | Pergunte “Posso passar de carro por uma rua alagada?”. Abra a fonte e confira se a seleção foi por busca ou por IA local. Pergunte se uma ponte foi liberada hoje para ver a abstenção sobre situação atual. |
| Módulos → PLN | Abra a Fábrica de Corpus e acione a geração dos quatro JSONL. Ela usa os documentos e recursos originais do ZIP. O assistente continua com a base curada da própria disciplina. |
| Módulos → Cluster, Quântica e IoT | Abra as capturas do iSPD, o benchmark clássico e a avaliação do classificador acústico arquivados. Para acrescentar um atalho para o projeto Edge Impulse, configure `EDGE_IMPULSE_PROJECT_URL` com o link fornecido pelo responsável. |

A [primeira auditoria](../entregas/gs2026.2/Inventario_Evidencias.md) descreve o estado do GitHub antes da integração. A aplicação integral de demonstração usa o iniciador local acima. O Docker Compose do repositório é a configuração do núcleo original.
