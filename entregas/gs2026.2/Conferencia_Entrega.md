# Conferência da entrega integrada

Prazo indicado pela FIAP: 19/11/2026 às 23h55 pelo Portal do Aluno, em Trabalhos.

| Item | Preparação concluída | Passo restante |
|---|---|---|
| Relatório · 4 pontos | Versão integrada, editável, 15 páginas, com capa, folha de rosto, listas, sumário, introdução, nove tópicos, Governança ao final e seção Links com o vídeo publicado. | O grupo redige a seção 3 e confere o total de páginas após preencher. |
| Vídeo · 3 pontos | Vídeo final de 5min06s com captura da navegação, ponteiro visível e locução sincronizada. [Publicado no YouTube como Não listado](https://youtu.be/ZLIqapgsCqU), com disponibilidade confirmada sem login. | Anexar o link na entrega. |
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

## Publicar a branch no GitHub

O bundle inclui o histórico da versão integrada e o link do vídeo. Após importar o bundle, um mantenedor com escrita pode publicar a branch:

```powershell
git switch integracao-governanca
git push -u origin integracao-governanca
git ls-remote --heads origin integracao-governanca
```

A página esperada após o envio é https://github.com/murilo2318/campoconecta/tree/integracao-governanca. Abra a página para confirmar que o código e os materiais estão acessíveis. Se a branch for integrada à main pelo mantenedor, confira também o README da versão publicada.
