# Narração do vídeo integrado CampoConecta

Duração do corte 6 min 30 s. As faixas indicam onde encaixar os trechos. As telas já foram capturadas na versão integrada. Os segmentos de Cluster, Quântica e IoT mostram as evidências das entregas.

## 00:00–00:18 CampoConecta

O CampoConecta ajuda o pequeno produtor a registrar um problema e a equipe de assistência técnica a analisá-lo. Vou mostrar o caminho do relato até o encaminhamento e abrir as ferramentas e evidências que fazem parte da entrega.

## 00:18–00:46 Do relato ao protocolo

Para mostrar o fluxo, usamos um caso sintético. A bomba do poço quebrou e a horta está sem água desde ontem. O produtor escreve a descrição e pode deixar o CEP em branco. A API trata o texto, classifica o problema por regras neste ambiente e devolve um protocolo. A tela informa que o caso ainda aguarda conferência.

## 00:46–01:20 Conferência pelo gestor

No painel do gestor, encontramos o mesmo relato como pendente. A urgência sugerida ajuda a organizar a fila, mas a decisão depende da conferência. Ao aprovar, o registro muda de situação. A decisão fica ligada ao relato no banco. Esse é o ponto de controle que permite ao robô selecionar o caso para encaminhamento. O produtor também pode avaliar a classificação na tela de origem.

## 01:20–01:44 Processamento do lote

No painel, executamos o robô sobre o lote sintético. O Pandas lê e valida as linhas, e a consulta ao ViaCEP complementa os registros quando encontra o local. O relatório mostra cinquenta e duas linhas processadas e três em quarentena, cada uma com seu motivo.

## 01:44–02:09 Mensagem preparada para os aprovados

Os lotes e os relatos da tela passam pelo mesmo processamento e usam o mesmo banco. O robô seleciona os aprovados. No arquivo de e-mail está o resumo do relato da bomba de irrigação que acabamos de conferir. A mensagem foi salva localmente, sem envio. Ao reprocessar o lote, o banco preserva a decisão do gestor.

## 02:09–02:26 Dois workers no iSPD

No simulador i S P D, o grupo executou quinhentas tarefas independentes, de cento e trinta e seis mega flops cada. Dois workers concluíram a carga em aproximadamente trinta e quatro segundos simulados. A tela apresenta o resultado do motor.

## 02:26–02:42 Quatro workers no iSPD

Com quatro workers, o tempo caiu para cerca de dezessete segundos. A redução ficou perto de cinquenta por cento neste cenário. A API pública continua local. Internet, banco e revisão humana ficam fora dessa simulação.

## 02:42–03:11 Como organizar a fila de revisão

Os erros de urgência justificam medir quanto a equipe espera para revisar os relatos. O estudo quântico propõe começar medindo essa fila e comparando alternativas clássicas de alocação. O experimento disponível é um benchmark clássico de visitas sintéticas. No cenário severo, os dois métodos mantiveram quarenta e oito visitas pendentes, em média. Uma futura formulação de otimização híbrida depende de evidência de benefício.

## 03:11–03:34 Consulta com fonte

Na mesma interface, abro a aba de chuvas e enchentes e pergunto sobre atravessar uma rua alagada. O Qwen local escolhe um trecho da base curada. A tela exibe a orientação com a fonte. Quando pergunto se uma ponte foi liberada hoje, o chat informa que não consulta a situação atual.

## 03:34–03:57 O teste do modelo e do fluxo

No teste isolado, o modelo de um bilhão e meio de parâmetros acertou dez de vinte escolhas. No fluxo completo, a busca, os filtros e a seleção do texto atenderam a quarenta e dois de quarenta e dois casos. O modo extrativo também alcançou esse resultado. Esses números descrevem os casos do trabalho.

## 03:57–04:13 Documentos entram com metadados

Pela aba Módulos, abro a Fábrica de Corpus. A ferramenta roda em um serviço próprio iniciado junto ao portal. Ela extrai e normaliza o texto dos documentos, mascara padrões de dados pessoais e preserva a origem.

## 04:13–04:29 Corpus e conjunto reservado

A geração entrega cinquenta e dois trechos de texto, cento e doze pares de perguntas e respostas e trinta e dois diálogos. Vinte e quatro casos ficam reservados para avaliação. O assistente demonstrado usa sua própria base.

## 04:29–04:43 Sinal à Vista

O Sinal à Vista usa o microfone do telefone e mostra uma classe visual para ambiente, fala ou sirene. A proposta é tornar pistas sonoras mais acessíveis em situações de alagamento.

## 04:43–04:58 Teste do classificador de som

As quinze gravações reservadas foram classificadas corretamente no Studio. O piloto no celular foi relatado pelo grupo. A série formal de quinze tentativas ao vivo ficou sem registro. O protótipo funciona separado do portal.

## 04:58–05:20 Detecção de buracos na pavimentação

Na aba de pavimentação, envio a imagem reservada para teste. O Streamlit envia o arquivo à mesma API usada no portal. O YOLO identifica um possível buraco e desenha a caixa. A confiança é da detecção, e a decisão de vistoria cabe à equipe.

## 05:20–05:44 Erros do detector no conjunto conhecido

No teste conhecido de cem imagens, a precisão foi de cinquenta e dois vírgula vinte e quatro por cento. A revocação foi de trinta e dois vírgula setenta e um por cento. Houve falsos positivos e danos que ficaram sem detecção, como o exemplo na tela. Esses dados justificam conferência humana e avaliação em novas vias.

## 05:44–06:09 O que está integrado

Front, RPA, Visão e o assistente compartilham a interface e a API nesta versão local. A Fábrica de Corpus abre pelo menu como serviço separado. No mesmo menu ficam o resultado de Cluster, o estudo de Quântica e a evidência de teste do Sinal à Vista. Cada item aparece de acordo com o vínculo que tem com o portal.

## 06:09–06:30 O que acompanhar no atendimento

Na amostra mais difícil, as regras acertaram seis de vinte urgências. Duas situações rotuladas como críticas foram subestimadas. Por isso, a governança acompanha erros de urgência e preserva a decisão humana. Espera até a decisão e entrega confirmada são indicadores para medir em piloto.
