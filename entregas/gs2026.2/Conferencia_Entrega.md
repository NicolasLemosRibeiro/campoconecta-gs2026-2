# Conferência da entrega de Governança

Prazo no calendário da FIAP: **19/11/2026 às 23h55**, pelo Portal do Aluno, em Trabalhos. O barema distribui 4 pontos para documentação, 3 para vídeo e 3 para GitHub.

| Critério oficial | Conferência | O que falta |
|---|---|---|
| Documento ABNT/FIAP · 4 pontos | DOCX A4 com 15 páginas físicas conferidas. Inclui capa e folha de rosto com os três integrantes, listas de figura e quadros, sumário, introdução, nove tópicos disciplinares com Governança por último, conclusão reservada, tópico Links e referências. | O grupo escreve a conclusão integralmente. Substitua o marcador na própria página, insira o endereço do vídeo e confira se a paginação continua entre 10 e 15 páginas. |
| Vídeo integrador · 3 pontos | Roteiro de 6min30s, com telas, tempos, evidências e orientação de gravação para os nove tópicos. | O grupo grava, narra e edita a demonstração. Confere 5–7 minutos, evita leitura extensa, publica como **Não listado** no YouTube e testa o acesso pelo link. |
| GitHub · 3 pontos | O repositório público tem o núcleo, o Front, o RPA e os artefatos do Cluster. O bundle local reúne os arquivos de Governança e os seis ZIPs originais num commit aplicado sobre a versão pública auditada. | Um mantenedor com escrita importa o bundle e atualiza o relatório com a conclusão e o link do vídeo. Publica e testa a versão entregue antes de submeter. A conta disponível nesta sessão tinha acesso de leitura. |
| Submissão | Enunciado e barema conferidos. | Envie ao professor pelo Portal do Aluno na disciplina de Governança. Abra o arquivo submetido e os links antes de encerrar. |

## Como aplicar a preparação Git

O bundle contém o commit de preparação e usa o histórico público do CampoConecta como base. Em um clone limpo e atualizado, um mantenedor pode executar os comandos abaixo em PowerShell. Use o caminho real do bundle e um nome de branch local disponível.

```powershell
git clone https://github.com/murilo2318/campoconecta.git
Set-Location campoconecta
$pacoteGovernanca = 'CAMINHO_COMPLETO\CampoConecta_Entrega_Governanca.bundle'
git bundle verify $pacoteGovernanca
git fetch $pacoteGovernanca refs/heads/entrega-governanca:refs/heads/entrega-governanca
git switch -c governanca-final origin/main
git cherry-pick entrega-governanca
```

A entrega fica em `entregas/gs2026.2/`. Atualize o DOCX dessa pasta com a conclusão e o endereço do vídeo. Se o Portal pedir PDF, exporte a versão final com a conclusão já preenchida. Faça o commit dos arquivos finais e publique pelo fluxo do repositório. O material da disciplina deve estar acessível pelo link submetido. Confira os arquivos e as permissões de acesso pelo GitHub antes do envio.

As lacunas de IoT ao vivo e de validação externa do Front permanecem documentadas. No vídeo, identifique capturas de execuções anteriores com o nome do módulo e a origem da evidência.
