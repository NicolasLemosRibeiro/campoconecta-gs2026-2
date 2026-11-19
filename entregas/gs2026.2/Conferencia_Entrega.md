# Conferência da entrega integrada

Prazo indicado pela FIAP: 19/11/2026 às 23h55 pelo Portal do Aluno, em Trabalhos.

| Item | Preparação concluída | Passo restante |
|---|---|---|
| Relatório · 4 pontos | Versão integrada, editável, 15 páginas, com capa, folha de rosto, listas, sumário, introdução, nove tópicos, Governança ao final e seção Links. | O grupo redige a seção 3. Inserir o link do vídeo e verificar o total de páginas após preencher. |
| Vídeo · 3 pontos | Corte de 6min30s com a execução do sistema novo, roteiro por trecho e guia SRT. | Incorporar a locução, conferir a duração e publicar no YouTube como Não listado. Conferir acesso pelo link. |
| GitHub · 3 pontos | Fonte executável em Windows, pacote Git com os seis ZIPs e link para as evidências, com o código da versão integrada e o relatório. | Um mantenedor com escrita importa, atualiza o relatório e publica os commits antes de enviar pelo Portal. |
| Portal | Relatório e repositório preparados localmente. | Enviar na disciplina e conferir os links anexados. |

## Importar a versão integrada

Em um clone atualizado do repositório principal, use o caminho completo para o arquivo `CampoConecta_Integrado.bundle`.

```powershell
$bundleGovernanca = 'CAMINHO_COMPLETO\CampoConecta_Integrado.bundle'
git bundle verify $bundleGovernanca
git fetch $bundleGovernanca refs/heads/integracao-governanca:refs/heads/integracao-governanca
git log --oneline origin/main..integracao-governanca
```

Faça a revisão em uma branch do mantenedor e integre a branch local `integracao-governanca` pelo fluxo do repositório. O pacote depende do histórico público iniciado no commit auditado `3fa3b22` e inclui os commits de organização e integração. Consulte `docs/DEMONSTRACAO_INTEGRADA.md` para iniciar a aplicação.
