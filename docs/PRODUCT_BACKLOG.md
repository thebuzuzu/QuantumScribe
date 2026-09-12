# Product Backlog — Quantum Scribe

Este é o inventário central de futuras features, melhorias, correções e débitos
técnicos do produto. Novas ideias podem entrar inicialmente na Caixa de Entrada,
mesmo sem prioridade ou especificação completa. Durante o refinamento, cada item
é classificado e preparado para desenvolvimento.

## Como usar

1. Registrar rapidamente qualquer ideia nova na **Caixa de Entrada**.
2. Refinar o item: esclarecer problema, resultado esperado e critérios de aceite.
3. Classificar prioridade, tipo, esforço e dependências.
4. Mover para **Pronto para priorização** quando houver informação suficiente.
5. Selecionar os próximos itens e movê-los para **Planejado**.
6. Atualizar o status durante o desenvolvimento até **Concluído**.

## Convenções

### Status

- `Ideia`: captura inicial, ainda não refinada.
- `Em refinamento`: sendo detalhada ou validada.
- `Pronto`: especificação suficiente para priorização.
- `Planejado`: selecionado para um próximo ciclo.
- `Em desenvolvimento`: implementação iniciada.
- `Bloqueado`: depende de decisão ou trabalho externo.
- `Concluído`: entregue e validado.
- `Descartado`: não será desenvolvido no momento.

### Prioridade

- `P0 — Crítica`: falha grave, perda de dados ou produto inutilizável.
- `P1 — Alta`: impacto frequente e relevante no fluxo principal.
- `P2 — Média`: melhoria importante, mas existe alternativa temporária.
- `P3 — Baixa`: conveniência, polimento ou oportunidade futura.
- `A definir`: ainda precisa passar pela triagem.

### Tipo

- `Feature`: nova capacidade para o usuário.
- `Melhoria`: evolução de algo que já existe.
- `Bug`: comportamento incorreto.
- `Débito técnico`: trabalho interno de qualidade ou manutenção.
- `Pesquisa`: descoberta necessária antes de decidir uma solução.

### Esforço preliminar

- `P`: pequeno.
- `M`: médio.
- `G`: grande.
- `A definir`: ainda não estimado.

## Visão geral

**Snapshot de 2026-09-12:** 30 itens — 26 em refinamento, 1 planejado e 3
concluídos. Por prioridade: 17 P1, 12 P2 e 1 P3.

| ID | Item | Tipo | Status | Prioridade | Esforço | PRD |
| --- | --- | --- | --- | --- | --- | --- |
| QS-001 | Fila de transcrições consecutivas | Feature | Em refinamento | P1 — Alta | G | [Abrir PRD](PRD_FILA_TRANSCRICOES.md) |
| QS-002 | Modo Transcrição Exata e simplificação dos ajustes de texto | Melhoria | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS002_TRANSCRICAO_EXATA.md) |
| QS-003 | Configurações contextuais e dependências entre funções | Melhoria | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS003_CONFIGURACOES_CONTEXTUAIS.md) |
| QS-004 | Ícone central do HUD desaparece em transições rápidas | Bug | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS004_HUD_ICONE_TRANSICOES.md) |
| QS-005 | Detectar e reutilizar modelos Whisper compatíveis existentes | Feature | Em refinamento | P2 — Média | G | A criar |
| QS-006 | Download resiliente do modelo com retomada e fallback | Melhoria | Em refinamento | P1 — Alta | G | [Abrir PRD](PRD_QS006_DOWNLOAD_MODELO_RESILIENTE.md) |
| QS-007 | Unificar e atualizar o ícone oficial em todas as superfícies | Bug | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS007_ICONES_OFICIAIS.md) |
| QS-008 | Sincronizar a cor personalizada com os ícones do aplicativo | Melhoria | Em refinamento | P3 — Baixa | M | A criar |
| QS-009 | Modernizar o controle de volume dos efeitos | Melhoria | Em refinamento | P2 — Média | P | A criar |
| QS-010 | Redesenhar o histórico de transcrições como tabela moderna | Melhoria | Em refinamento | P2 — Média | M | A criar |
| QS-011 | Pesquisa textual unificada em todas as transcrições | Feature | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS011_PESQUISA_TRANSCRICOES.md) |
| QS-012 | Pesquisa semântica local e adaptativa no histórico | Feature | Em refinamento | P2 — Média | G | A criar |
| QS-013 | Modo cloud/API opcional para computadores fracos | Pesquisa | Em refinamento | P2 — Média | G | A criar |
| QS-014 | Controle de destino e mudança de foco ao entregar transcrições | Melhoria | Em refinamento | P2 — Média | M | A criar |
| QS-015 | Restaurar controles e feedbacks sonoros do ditado | Bug | Em refinamento | P1 — Alta | M | A criar |
| QS-016 | Cancelamento intencional por ESC mantido com progresso visual no HUD | Melhoria | Em refinamento | P1 — Alta | M | A criar |
| QS-017 | Estabilizar HUD, cancelamento e prontidão visual na inicialização | Bug | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS017_ESTABILIDADE_HUD_INICIALIZACAO.md) |
| QS-018 | Verificar e atualizar somente o aplicativo | Feature | Em refinamento | P2 — Média | G | [Abrir PRD](PRD_QS018_ATUALIZACAO_APLICATIVO.md) |
| QS-019 | Tornar a instalação e a primeira execução calmas e verificáveis | Melhoria | Em refinamento | P1 — Alta | G | [PRD relacionado](PRD_CORE_LEVE_COMPONENTES_SOB_DEMANDA.md) |
| QS-020 | Acelerar a primeira transcrição com preparação antecipada | Melhoria | Em refinamento | P1 — Alta | M | A criar |
| QS-021 | Restaurar manifesto de dependências e release reproduzível | Bug | Planejado | P1 — Alta | M | [Procedimento de release](guides/release-procedure.md) |
| QS-022 | Contrato único de atalhos e conflitos entre plataformas | Bug | Em refinamento | P1 — Alta | M | A criar |
| QS-023 | Isolar sessões e cancelamento cooperativo de ditados | Bug | Em refinamento | P1 — Alta | G | A criar |
| QS-024 | Garantir paridade e qualidade do streaming contínuo | Melhoria | Em refinamento | P2 — Média | G | A criar |
| QS-025 | Concluir o Quantum Brain com resultado verificável | Bug | Em refinamento | P2 — Média | M | A criar |
| QS-026 | Retirar compatibilidades e artefatos obsoletos com migração segura | Débito técnico | Em refinamento | P2 — Média | M | A criar |
| QS-027 | Inicialização rápida de dispositivos de áudio virtuais no Windows | Melhoria | Em refinamento | P1 — Alta | M | A criar |
| QS-028 | Iniciar automaticamente com o Windows | Feature | Concluído | P1 — Alta | M | A criar |
| QS-029 | Organizar configurações e tornar toggles verificáveis | Melhoria | Concluído | P2 — Média | M | A criar |
| QS-030 | Implementar tema Liquid Orb portátil e fallback | Melhoria | Concluído | P2 — Média | M | [Story 3.1](stories/3.1.story.md) |

## Programa de implementação

O backlog é a fonte de verdade da sequência de execução. Os PRDs específicos
continuam definindo o escopo de cada item; os próximos itens priorizados são:

| Ordem | Item | Situação | Próximo resultado |
| --- | --- | --- | --- |
| 1 | QS-021 | Planejado | Regenerar locks e validar instalações limpas em CPU, Windows e Linux. |
| 2 | QS-017 | Em refinamento | Preparar a story de estabilização do HUD, cancelamento e prontidão. |
| 3 | QS-023 | Em refinamento | Preparar a story de isolamento de sessões e cancelamento cooperativo. |

## Caixa de Entrada

Adicione ideias novas aqui sem se preocupar inicialmente com a solução.

<!-- Modelo rápido:
- **Título:**
  - Problema ou oportunidade:
  - Resultado desejado:
  - Contexto ou exemplo:
-->

_Nenhum item aguardando triagem._

## Em refinamento

### QS-001 — Fila de transcrições consecutivas

- **Tipo:** Feature
- **Prioridade preliminar:** P1 — Alta
- **Esforço preliminar:** G
- **Problema:** o usuário precisa esperar a transcrição atual terminar antes de
  começar outro ditado.
- **Resultado desejado:** permitir novas gravações enquanto um item é processado,
  mantendo uma fila visível, segura e limitada.
- **Próxima decisão:** validar a apresentação recomendada do HUD e confirmar o
  limite de três itens aguardando.
- **Especificação:** [PRD — Fila de transcrições consecutivas](PRD_FILA_TRANSCRICOES.md)

### QS-002 — Modo Transcrição Exata e simplificação dos ajustes de texto

- **Tipo:** Melhoria de experiência e previsibilidade.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Problema:** combinações de opções como modo literal, assistência de
  pontuação, remoção de repetições, remoção de hesitações, dicionário e reescrita
  podem fazer a saída variar sem deixar evidente quais etapas modificaram o
  texto reconhecido.
- **Resultado desejado:** oferecer uma ação simples e inequívoca para transcrever
  com a menor modificação possível e mostrar claramente quando algum
  pós-processamento estiver ativo.
- **Solução inicial a avaliar:** preset ou botão `Transcrição Exata`, que desative
  de uma vez todas as transformações de palavras e mantenha somente proteções
  técnicas indispensáveis. Exibir um resumo como `Sem alterações de texto` ou
  `2 ajustes podem modificar a transcrição`.
- **Regras preliminares:**
  - explicar em linguagem simples o efeito de cada opção;
  - impedir combinações contraditórias ou avisar sobre elas;
  - permitir restaurar os padrões seguros com um clique;
  - diferenciar pontuação conservadora de alterações de palavras;
  - indicar no HUD ou nas configurações o perfil efetivamente ativo;
  - preservar uma configuração escolhida entre reinicializações;
  - ao ativar `Transcrição Literal`, tratá-la como opção principal e desabilitar
    automaticamente todas as transformações incompatíveis, como reescrita por
    LLM, estilo/tom, remoção de repetições, remoção de hesitações, aprendizado e
    substituições automáticas que alterem palavras;
  - definir explicitamente se assistência de pontuação é compatível com o modo
    literal ou se deverá ser desligada para cumprir a promessa mais estrita;
  - atualizar os controles dependentes ao vivo, antes de salvar, mostrando por
    que ficaram inativos;
  - ao desligar o modo literal, não reativar silenciosamente transformações que
    o usuário não escolheu.
- **Próxima decisão:** definir se `Transcrição Exata` será um preset, um modo
  permanente ou o padrão inicial para novos usuários, além de aprovar uma matriz
  única de compatibilidade entre todas as opções de texto.
- **Especificação:** [PRD QS-002 — Modo Transcrição Exata](PRD_QS002_TRANSCRICAO_EXATA.md)

### QS-003 — Configurações contextuais e dependências entre funções

- **Tipo:** Melhoria de interface, desempenho e transparência.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-002.
- **Problema:** a tela mostra Silero VAD e controles de silêncio mesmo quando o
  Streaming Contínuo está desligado, dando a impressão de que continuam ativos.
  Além disso, o modo clássico possui um filtro VAD interno do faster-whisper que
  não está claramente diferenciado nem possui controle visível.
- **Constatação atual:** o Silero VAD é inicializado apenas quando o streaming é
  ativado, mas seu status aparece sempre na interface. O VAD do modo clássico é
  um mecanismo separado.
- **Resultado desejado:** mostrar, habilitar e carregar apenas opções aplicáveis
  ao modo atual, sem esconder filtros que ainda alterem o processamento. A mesma
  regra deve valer para toda a tela de configurações, não somente para VAD.
- **Regras preliminares:**
  - com Streaming Contínuo desligado, rebaixar visualmente ou recolher Silero VAD,
    tempo de chunk e silêncio para corte;
  - exibir o estado `Inativo — requer Streaming Contínuo`, em vez de um selo que
    pareça confirmar uso ativo;
  - não carregar modelo ou recursos do Silero enquanto o streaming estiver
    desligado;
  - ao ativar streaming, liberar os controles dependentes imediatamente;
  - nomear e explicar separadamente o filtro VAD clássico do faster-whisper;
  - avaliar um controle seguro para o VAD clássico, incluindo aviso sobre ruído,
    silêncio e possíveis cortes de fala;
  - garantir que instalações novas não ativem nem carreguem recursos opcionais
    que o usuário nunca habilitou;
  - auditar todos os controles e criar uma matriz `opção principal → opções
    dependentes → opções incompatíveis`;
  - aplicar habilitação, desabilitação, recolhimento e mensagens explicativas ao
    vivo enquanto o usuário altera a opção principal;
  - validar novamente as dependências ao salvar e também ao carregar configurações
    antigas ou inconsistentes;
  - nunca deixar um controle parecer ativo quando seu recurso não está sendo
    executado;
  - quando um recurso for independente, oferecer controle próprio e deixar essa
    independência clara na descrição.
- **Próxima decisão:** definir se controles inativos ficam visíveis e cinza ou se
  aparecem somente após expandir/ativar o modo correspondente. Preferência
  preliminar: visíveis e rebaixados, com o motivo, para ensinar a relação ao
  usuário.
- **Especificação:** [PRD QS-003 — Configurações contextuais](PRD_QS003_CONFIGURACOES_CONTEXTUAIS.md)

### QS-004 — Ícone central do HUD desaparece em transições rápidas

- **Tipo:** Bug de interface e feedback de estado.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-001 — Fila de transcrições consecutivas.
- **Problema:** o ícone/animação central do HUD desaparece ocasionalmente quando
  o usuário finaliza uma transcrição e inicia outra gravação muito rápido. Sem o
  indicador, não fica claro se o sistema continua gravando ou processando.
- **Frequência observada:** intermitente, mais provável em ações consecutivas e
  rápidas.
- **Resultado desejado:** o HUD deve sempre exibir um indicador visual coerente
  com o estado atual, inclusive em transições rápidas entre conclusão,
  processamento e nova gravação.
- **Regras preliminares:**
  - eventos atrasados de animação ou ocultação não podem apagar o HUD da sessão
    seguinte;
  - cada atualização visual deve validar a sessão ou geração de HUD à qual
    pertence;
  - iniciar uma gravação deve restaurar explicitamente todos os elementos do tema
    selecionado;
  - a correção da fila QS-001 pode compartilhar a solução de controle de estados,
    mas QS-004 só será concluído após validação própria;
  - adicionar teste de estresse para finalizar e reiniciar repetidamente com
    intervalos curtos.
- **Critério principal de aceite:** após múltiplos ciclos rápidos de
  finalizar/iniciar, o ícone central permanece visível e animado durante toda
  gravação ou processamento ativo.
- **Especificação:** [PRD QS-004 — Ícone central do HUD](PRD_QS004_HUD_ICONE_TRANSICOES.md)

### QS-005 — Detectar e reutilizar modelos Whisper compatíveis existentes

- **Tipo:** Feature de onboarding e gerenciamento de armazenamento.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-006 — Download resiliente do modelo.
- **Problema:** atualmente o Quantum Scribe verifica apenas seu próprio diretório
  de modelos. Um usuário pode já possuir o mesmo modelo em um cache conhecido ou
  instalado por outro projeto e ainda ser obrigado a baixar outra cópia.
- **Resultado desejado:** antes de iniciar um download grande, procurar modelos
  existentes em locais conhecidos, validar sua compatibilidade e informar ao
  usuário quando puderem ser reutilizados com segurança.
- **Regras preliminares:**
  - pesquisar primeiro o cache próprio, o cache padrão do Hugging Face e caminhos
    configurados por variáveis oficiais do ecossistema;
  - oferecer `Localizar modelo existente…` para seleção manual de uma pasta;
  - reconhecer que modelos OpenAI Whisper/PyTorch e modelos faster-whisper em
    CTranslate2 podem ter formatos incompatíveis;
  - validar nome, formato, arquivos essenciais, tamanho e capacidade de carga
    antes de aceitar um modelo encontrado;
  - nunca executar arquivos nem confiar somente no nome da pasta;
  - mostrar `Modelo compatível encontrado` com origem, variante e espaço que será
    economizado, pedindo confirmação antes de vinculá-lo;
  - preferir referência segura ao cache existente ou link de filesystem quando
    suportado; copiar apenas quando necessário;
  - se o modelo for incompatível, explicar o motivo e seguir para o fluxo de
    download sem quebrar a instalação;
  - não fazer varredura indiscriminada de todos os discos, evitando lentidão e
    acesso desnecessário a arquivos pessoais.
- **Critério principal de aceite:** numa máquina com snapshot CTranslate2 válido
  no cache global do Hugging Face, o app o detecta, valida e pode iniciar sem
  baixar uma segunda cópia.

### QS-006 — Download resiliente do modelo com retomada e fallback

- **Tipo:** Melhoria crítica de onboarding e confiabilidade.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-005 — Detecção de modelos existentes.
- **Problema:** falhas repetidas no download do modelo quase fizeram um novo
  usuário desistir da instalação. Sem modelo completo, a função principal do
  produto fica indisponível.
- **Resultado desejado:** concluir o download de forma confiável em conexões
  instáveis e oferecer caminhos de recuperação claros, sem exigir intervenção
  técnica ou ajuda de um agente.
- **Estratégia de fallback preliminar:**
  1. retomar o snapshot parcial da fonte oficial primária;
  2. repetir automaticamente arquivos que falharam, com backoff e limite seguro;
  3. alternar para uma fonte secundária previamente validada e confiável;
  4. oferecer download manual verificado ou instalador offline como última opção.
- **Regras preliminares:**
  - não depender de um único link permanente sem monitoramento;
  - fixar repositório/revisão compatível e validar arquivos essenciais após cada
    tentativa;
  - preservar partes válidas e retomar de onde parou, sem reiniciar gigabytes;
  - verificar espaço em disco, acesso à pasta, conectividade, proxy, certificado
    TLS e integridade antes de exibir um erro genérico;
  - usar staging e promoção atômica, nunca tratar snapshot parcial como instalado;
  - apresentar progresso real, arquivo atual, tentativas e ação seguinte;
  - oferecer `Tentar novamente`, `Alterar local`, `Usar modelo existente` e
    `Download manual`, conforme a causa;
  - manter a interface responsiva e permitir fechar/reabrir o app sem perder o
    progresso válido;
  - registrar diagnóstico técnico sem dados pessoais e permitir copiá-lo para
    suporte;
  - testar fonte primária e fallback periodicamente antes de cada release;
  - executar testes de instalação limpa, conexão interrompida, pouco espaço,
    proxy corporativo, snapshot corrompido e retomada após reinício.
- **Critérios principais de aceite:**
  - uma interrupção no meio do download é retomada sem baixar novamente os
    arquivos completos;
  - falha na fonte primária aciona uma alternativa segura ou uma instrução de
    recuperação utilizável;
  - o app só informa `Modelo instalado` depois de validar e carregar o snapshot;
  - nenhum usuário fica preso num ciclo de erro sem causa e próxima ação visíveis.
- **Especificação:** [PRD QS-006 — Download resiliente](PRD_QS006_DOWNLOAD_MODELO_RESILIENTE.md)

### QS-007 — Unificar e atualizar o ícone oficial em todas as superfícies

- **Tipo:** Bug de identidade visual e empacotamento.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Problema:** o ícone exibido na barra de tarefas e o ícone da bandeja do
  Windows estão desatualizados ou diferentes do ícone oficial mostrado na tela
  Sobre e nas janelas do aplicativo.
- **Constatação atual:** as janelas carregam o ícone de átomo/microfone, enquanto
  a bandeja gera por código um ícone distinto de barras de áudio.
- **Resultado desejado:** adotar uma única fonte oficial de ícone e gerar dela
  todas as variantes necessárias para janela, executável, barra de tarefas,
  bandeja, instalador, atalhos e tela Sobre.
- **Regras preliminares:**
  - manter um asset mestre em alta resolução e versões apropriadas para cada
    tamanho e densidade;
  - gerar `.ico` com múltiplas resoluções para o executável e atalhos do Windows;
  - garantir legibilidade da bandeja nos temas claro e escuro e em 100%–200% de
    escala;
  - substituir o gerador de barras de áudio da bandeja pelo ícone oficial;
  - atualizar metadados do build e instalador, considerando o cache de ícones do
    Windows em atualizações;
  - impedir que uma ausência de asset faça diferentes superfícies voltarem a
    logos divergentes.
- **Critério principal de aceite:** após instalação limpa e atualização, todas as
  superfícies exibem a mesma identidade visual, sem ícone antigo em cache.
- **Especificação:** [PRD QS-007 — Ícone oficial unificado](PRD_QS007_ICONES_OFICIAIS.md)

### QS-008 — Sincronizar a cor personalizada com os ícones do aplicativo

- **Tipo:** Melhoria de personalização visual.
- **Prioridade preliminar:** P3 — Baixa.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-007 — Ícone oficial unificado.
- **Problema:** a cor de destaque/átomo pode ser personalizada dentro do sistema,
  mas os ícones externos permanecem com a cor padrão.
- **Resultado desejado:** avaliar a aplicação da cor escolhida pelo usuário ao
  ícone da bandeja e às janelas, mantendo contraste e reconhecimento da marca.
- **Regras preliminares:**
  - atualizar imediatamente os ícones que aceitam imagem em tempo de execução;
  - manter fallback monocromático ou de alto contraste quando necessário;
  - não prometer alteração instantânea do ícone fixado na barra de tarefas caso o
    Windows dependa do ícone estático do executável e de cache;
  - separar personalização dinâmica dos assets oficiais usados pelo instalador;
  - oferecer `Usar cor do sistema` e `Usar cor oficial` como escolhas claras.
- **Próxima decisão:** decidir se a personalização deve atingir somente bandeja e
  janelas ou também atalhos/barra de tarefas após reinício.

### QS-009 — Modernizar o controle de volume dos efeitos

- **Tipo:** Melhoria visual e de interação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** P.
- **Problema:** o controle atual usa o slider clássico do Tkinter e apresenta um
  cursor quadrado, visualmente antigo e inconsistente com o restante do painel.
- **Resultado desejado:** substituir por um slider moderno com trilho limpo,
  preenchimento na cor de destaque e marcador circular.
- **Regras preliminares:**
  - usar esfera/círculo como thumb, com estados normal, hover, pressionado e foco;
  - suportar clique no trilho, arraste suave, teclado e escala de DPI;
  - manter percentual visível e atualização ao vivo;
  - preservar acessibilidade, área de toque confortável e contraste nos temas
    claro e escuro;
  - usar componente reutilizável para futuros sliders do painel.
- **Critério principal de aceite:** o slider não exibe componentes nativos
  quadrados e continua operável por mouse e teclado em diferentes escalas.

### QS-010 — Redesenhar o histórico de transcrições como tabela moderna

- **Tipo:** Melhoria de experiência e organização.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-011 e QS-012.
- **Problema:** o histórico atual é um campo de texto com links roxos para
  arquivos diários, tem pouca hierarquia visual e não permite examinar as
  transcrições de forma confortável dentro do app.
- **Resultado desejado:** apresentar o histórico numa tabela/lista moderna,
  neutra e legível, com separação clara entre dias e entradas.
- **Regras preliminares:**
  - usar preto, cinzas e branco como base; reservar a cor de destaque para foco,
    seleção ou ação, sem colorir todos os nomes;
  - usar linhas alternadas em cinza mais claro/escuro ou divisores discretos;
  - considerar colunas `Data`, `Hora`, `Prévia`, `Quantidade` e `Ações`;
  - permitir expandir um dia e visualizar suas transcrições sem abrir o Markdown
    externamente;
  - oferecer ordenação, cópia, abertura do arquivo e navegação por teclado;
  - manter boa leitura com históricos grandes e scrollbar discreta;
  - preservar os arquivos Markdown atuais como fonte ou formato de exportação,
    evitando migração destrutiva.
- **Critério principal de aceite:** dias e entradas são distinguíveis sem depender
  de links coloridos, com data/hora e prévia consultáveis dentro do aplicativo.

### QS-011 — Pesquisa textual unificada em todas as transcrições

- **Tipo:** Feature de recuperação de informação.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-010 — Novo histórico; QS-012 — Pesquisa semântica.
- **Problema:** o usuário não consegue localizar uma palavra ou frase sem abrir e
  procurar manualmente em cada arquivo diário.
- **Resultado desejado:** pesquisar de uma vez em todos os arquivos e entradas do
  histórico, funcionando localmente em qualquer computador.
- **Regras preliminares:**
  - oferecer busca exata e por palavras, sem diferenciar maiúsculas/minúsculas e
    com tratamento adequado de acentos;
  - indexar data, hora, texto e origem de cada entrada;
  - destacar os termos encontrados e mostrar trecho de contexto;
  - permitir filtrar por intervalo de datas e ordenar por relevância ou recência;
  - atualizar o índice quando novas transcrições forem salvas ou arquivos forem
    alterados;
  - reconstruir o índice sem perder os Markdown originais;
  - responder rapidamente em históricos grandes e manter tudo offline.
- **Critério principal de aceite:** uma frase existente em qualquer arquivo diário
  é encontrada numa única busca, com link direto para a entrada correspondente.
- **Especificação:** [PRD QS-011 — Pesquisa textual](PRD_QS011_PESQUISA_TRANSCRICOES.md)

### QS-012 — Pesquisa semântica local e adaptativa no histórico

- **Tipo:** Feature avançada de recuperação de informação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-011 — Busca textual; QS-013 — Modo cloud/API.
- **Problema:** uma busca apenas por palavras não encontra ideias relacionadas
  quando o usuário não lembra a formulação exata do que disse.
- **Resultado desejado:** permitir busca por significado usando chunks,
  embeddings e índice vetorial local sempre que o computador suportar, com
  adaptação automática ao ambiente.
- **Regras preliminares:**
  - manter a busca textual QS-011 como base universal e fallback obrigatório;
  - dividir entradas em chunks preservando data, hora, arquivo e posição;
  - selecionar modelo de embeddings pequeno, multilíngue e adequado ao português;
  - armazenar embeddings e metadados localmente, com reconstrução incremental;
  - detectar RAM, CPU/GPU, espaço e capacidades antes de oferecer ou ativar o
    recurso;
  - disponibilizar modo leve por CPU e ocultar/desabilitar semantic search quando
    o ambiente não atingir requisitos mínimos;
  - explicar consumo de disco, tempo de indexação e privacidade;
  - permitir apagar e reconstruir o índice sem apagar transcrições;
  - combinar relevância semântica, correspondência textual e recência;
  - avaliar resultados em português com um conjunto de consultas reais antes do
    lançamento.
- **Critério principal de aceite:** uma consulta conceitualmente relacionada,
  mesmo sem repetir as palavras originais, retorna a entrada correta entre os
  primeiros resultados num computador compatível.

### QS-013 — Modo cloud/API opcional para computadores fracos

- **Tipo:** Pesquisa de produto, arquitetura e monetização.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-006 — Download; QS-012 — Pesquisa semântica local.
- **Problema:** computadores fracos ou incompatíveis podem não executar com boa
  experiência transcrição, LLM e embeddings locais.
- **Oportunidade:** oferecer um plano pago opcional que execute esses recursos por
  API/cloud, mantendo o modo local como alternativa principal para quem possui
  hardware compatível.
- **Escopo de pesquisa:**
  - transcrição por API, pós-processamento por LLM e embeddings/busca semântica;
  - seleção automática ou manual entre `Local`, `Cloud` e `Híbrido` por recurso;
  - custos por minuto, tokens, armazenamento e indexação versus preço sustentável;
  - autenticação, cobrança, limites, observabilidade e suporte;
  - consentimento explícito antes de enviar áudio ou texto para terceiros;
  - criptografia, retenção mínima, exclusão, portabilidade e requisitos legais de
    privacidade/LGPD;
  - provedores alternativos e fallback para evitar dependência de uma única API;
  - degradação clara para busca textual/local quando assinatura ou rede falhar;
  - comunicação transparente de quais dados saem do computador em cada modo.
- **Princípio de produto:** recursos locais existentes não devem ser removidos ou
  bloqueados artificialmente para forçar assinatura.
- **Critério de saída da pesquisa:** proposta técnica e financeira com custos,
  riscos, experiência de consentimento, fornecedores possíveis e definição de um
  MVP pago para computadores fracos.

### QS-014 — Controle de destino e mudança de foco ao entregar transcrições

- **Tipo:** Melhoria de experiência e controle de automação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-001 — Fila de transcrições consecutivas.
- **Problema:** o aplicativo captura a janela/campo que estava ativo no início do
  ditado e, ao concluir, força o foco de volta para esse destino antes de colar.
  Isso protege contra colagem no lugar errado, mas pode interromper quem já está
  trabalhando em outra página ou aplicativo.
- **Constatação atual:** a opção existente de colagem automática controla se o
  texto será colado ou apenas copiado; ela não permite escolher se o destino é a
  janela original ou o foco atual no momento da conclusão.
- **Resultado desejado:** permitir que cada usuário escolha como a transcrição
  será entregue quando o foco tiver mudado durante o processamento.
- **Modos preliminares:**
  - `Voltar ao campo original`: comportamento atual, restaura a janela capturada
    no início e cola no destino original;
  - `Colar onde eu estiver`: não troca de janela e cola no campo que estiver
    ativo quando a transcrição terminar;
  - `Somente copiar`: nunca muda o foco nem cola automaticamente;
  - avaliar `Perguntar quando o foco mudar`, com aviso não intrusivo e ações para
    escolher o destino.
- **Regras preliminares:**
  - apresentar a escolha nas configurações em linguagem clara, separada do toggle
    geral de colagem automática;
  - não mudar de página ou trazer uma janela para frente quando o usuário tiver
    desabilitado o retorno ao destino original;
  - preservar o texto no clipboard se o destino escolhido não aceitar a colagem;
  - mostrar confirmação indicando onde o texto foi inserido ou que ficou somente
    copiado;
  - no modo autoenvio, pressionar Enter apenas após inserção confirmada e nunca em
    uma janela diferente da escolhida;
  - definir comportamento individual por job quando a fila QS-001 existir;
  - manter o comportamento atual como opção disponível e documentar o padrão para
    instalações novas.
- **Próxima decisão:** escolher entre `Voltar ao campo original` e `Perguntar
  quando o foco mudar` como padrão mais seguro para novos usuários.
- **Critério principal de aceite:** com o retorno automático desabilitado, o
  usuário pode trocar de aplicativo durante a transcrição e nenhuma janela é
  aberta, restaurada ou trazida para frente contra sua vontade.

### QS-015 — Restaurar controles e feedbacks sonoros do ditado

- **Tipo:** Bug de configuração e feedback de estado.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-003 — Configurações contextuais; QS-009 — Controle de
  volume dos efeitos.
- **Problema relatado:** a opção de sons não aparece mais nas configurações e,
  ao acionar a extensão/atalho de ditado, nenhum efeito é reproduzido: início,
  conclusão/saída ou cancelamento. O produto fica totalmente mudo e perde um
  feedback importante sobre o estado da operação.
- **Constatação preliminar no código:** a configuração `play_sounds`, o volume e
  as chamadas dos três efeitos ainda existem no código-fonte atual. O defeito
  precisa ser reproduzido na distribuição utilizada pelo usuário para verificar
  se é uma regressão de interface, persistência, empacotamento, dispositivo de
  saída ou reprodução em tempo de execução.
- **Resultado desejado:** restaurar a configuração visível de efeitos sonoros e
  garantir feedback audível e coerente ao iniciar, concluir e cancelar um
  ditado em todas as formas suportadas de acionamento.
- **Regras preliminares:**
  - exibir o controle `Efeitos Sonoros` e seu volume na seção correta das
    configurações, refletindo o valor efetivamente salvo e usado pelo app;
  - com os sons habilitados e volume acima de zero, reproduzir efeitos distintos
    de início, conclusão e cancelamento;
  - aplicar o mesmo comportamento ao acionamento pelo aplicativo, atalho global
    e extensão, quando essa superfície fizer parte da instalação afetada;
  - com os sons desabilitados, permanecer silencioso sem alterar o volume salvo;
  - uma falha de reprodução não pode interromper a gravação ou a transcrição e
    deve deixar diagnóstico suficiente para suporte;
  - validar o comportamento também no aplicativo empacotado, não apenas ao
    executar pelo código-fonte.
- **Critérios principais de aceite:**
  - a opção de efeitos sonoros volta a ser encontrada nas configurações e
    permanece correta após salvar e reiniciar;
  - com sons habilitados, iniciar, concluir e cancelar um ditado produz os três
    feedbacks esperados em um dispositivo de saída válido;
  - o fluxo acionado pela extensão/atalho deixa de permanecer totalmente mudo;
  - desabilitar os efeitos silencia os três eventos sem afetar a transcrição.
- **Próxima decisão:** reproduzir na mesma versão e forma de instalação usadas no
  relato, confirmar qual superfície foi chamada de “extensão” e identificar em
  qual camada o controle e a reprodução deixaram de funcionar.

### QS-016 — Cancelamento intencional por ESC mantido com progresso visual no HUD

- **Tipo:** Melhoria de segurança da interação e feedback de estado.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-004 — Ícone central do HUD; QS-015 — Feedback sonoro do
  ditado.
- **Problema:** durante um ditado, um toque acidental em `Esc` descarta a
  gravação atual. O cancelamento é uma ação destrutiva para o conteúdo ainda não
  transcrito e hoje não exige uma confirmação intencional perceptível.
- **Constatação atual:** enquanto há gravação, o atalho global de `Esc` dispara
  o cancelamento quando a tecla é liberada; o HUD não apresenta progresso ou
  confirmação antes de descartar o áudio.
- **Resultado desejado:** exigir que a pessoa mantenha `Esc` pressionado por um
  curto intervalo para cancelar o ditado, deixando claro visualmente que o
  cancelamento está sendo confirmado. Um toque curto deve ser inofensivo e a
  gravação deve continuar normalmente.
- **Regras preliminares:**
  - iniciar a confirmação somente enquanto uma gravação puder ser cancelada;
  - ao pressionar `Esc`, desenhar uma linha fina vermelha que preenche o contorno
    circular do ícone central do HUD ao longo do tempo;
  - cancelar somente quando o ciclo visual completar após aproximadamente 0,5
    segundo; o HUD deve desaparecer e liberar um novo ditado no mesmo instante,
    sem pausa de confirmação após o preenchimento;
  - ao soltar `Esc` antes da conclusão, interromper e limpar a animação sem
    cancelar, sem pausar e sem alterar a gravação;
  - se o HUD for fechado, a gravação terminar por outro comando ou ocorrer uma
    transição de estado durante a contagem, cancelar com segurança o temporizador
    e impedir que um evento atrasado descarte uma nova sessão;
  - manter a indicação legível nos temas e cores personalizadas, reservando o
    vermelho exclusivamente para a ação de cancelamento iminente;
  - preservar feedback de cancelamento somente quando o cancelamento realmente
    se confirmar, respeitando a configuração de efeitos sonoros;
  - atualizar a ajuda de atalhos para explicar que `Esc` deve ser mantido
    pressionado para cancelar.
- **Critérios principais de aceite:**
  - durante um ditado ativo, pressionar e soltar `Esc` antes de 0,5 segundo não
    interrompe nem descarta o áudio e o HUD retorna ao estado normal;
  - manter `Esc` por 0,5 segundo completa uma linha fina vermelha ao redor do
    ícone central e então cancela o ditado uma única vez, ocultando o HUD e
    permitindo iniciar outro ditado sem espera adicional;
  - o contorno e o temporizador desaparecem corretamente ao soltar a tecla, ao
    concluir o ditado por outro atalho e nas transições rápidas entre sessões;
  - uma confirmação iniciada na sessão anterior nunca cancela uma nova gravação.
- **Ajuste registrado:** a referência de confirmação passou de 1 segundo para
  0,5 segundo. Ao completar, não há mais retenção visual: o HUD se fecha e uma
  nova gravação fica disponível imediatamente.

### QS-017 — Estabilizar HUD, cancelamento e prontidão visual na inicialização

- **Tipo:** Bug de confiabilidade de interface e inicialização.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-004 — HUD em transições; QS-007 — Ícone oficial;
  QS-016 — Cancelamento por ESC mantido.
- **Problema relatado:** o ícone/HUD pode demorar para aparecer, aparecer de
  modo intermitente ou sumir durante o uso. Ao manter `Esc`, o contorno vermelho
  pode desaparecer antes de completar, deixando incerto se o cancelamento foi
  realmente confirmado.
- **Constatações da auditoria:**
  - cada chamada de exibição do HUD pode iniciar outra cadeia de animação com
    `after`, sem cancelar nem identificar a cadeia anterior; animações antigas
    podem avançar a explosão/ocultação da sessão visual atual;
  - há ocultações temporizadas sem token de sessão no app, portanto um callback
    de uma mensagem anterior pode esconder o HUD que já foi reutilizado;
  - a confirmação do `Esc` limpa o aro e fecha o HUD no mesmo callback que atinge
    o limite, sem garantir ao menos um frame visível de 100%;
  - os quatro atalhos globais aguardam prontidão durante a construção do app,
    com timeout de até 3 segundos cada, e a bandeja inicia em thread sem um
    contrato de prontidão visual; isso explica uma inicialização percebida como
    lenta ou sem sinal imediato quando o Windows atrasa o registro;
  - a bandeja ainda cria um ícone de barras independente do asset oficial,
    mantendo uma segunda superfície visual com ciclo de vida próprio.
- **Resultado desejado:** uma única máquina de estados visual deve governar HUD,
  animação, cancelamento e ocultação. O aplicativo deve sinalizar prontidão da
  bandeja rapidamente, informar falha de atalho de modo visível e nunca ocultar
  ou cancelar uma sessão posterior por evento antigo.
- **Plano e especificação:** [PRD QS-017 — Estabilidade do HUD e inicialização](PRD_QS017_ESTABILIDADE_HUD_INICIALIZACAO.md)

### QS-018 — Verificar e atualizar somente o aplicativo

- **Tipo:** Feature de distribuição e manutenção.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** processo de releases Windows e componentes opcionais sob
  demanda.
- **Problema:** hoje a pessoa precisa abrir a página de releases e baixar
  manualmente cada nova versão, sem saber dentro do aplicativo se há atualização
  disponível.
- **Resultado desejado:** oferecer um botão para consultar a release oficial e,
  mediante confirmação, instalar somente uma versão mais nova do aplicativo.
- **Regras preliminares:**
  - colocar `Verificar atualização` na tela Sobre e avaliar também uma entrada
    no menu da bandeja;
  - consultar apenas releases públicas, finais, do repositório oficial;
  - comparar a versão publicada com a versão instalada e nunca permitir
    downgrade;
  - baixar exclusivamente o instalador x64 da versão encontrada e validar seu
    SHA-256 com o `SHA256SUMS.txt` da mesma release antes de executá-lo;
  - exigir confirmação antes de baixar ou instalar; a primeira versão não deve
    procurar nem atualizar silenciosamente;
  - fechar o aplicativo de forma controlada antes de iniciar o instalador, pois
    o executável em uso não pode ser substituído;
  - não atualizar nem apagar modelos, CUDA, Silero VAD, configurações,
    transcrições, backups ou qualquer outro dado local;
  - informar falhas de rede, integridade, permissão ou cancelamento com próxima
    ação clara e sem executar arquivo não verificado.
- **Critério principal de aceite:** com uma release posterior pública disponível,
  o usuário consegue confirmar a atualização no app, o instalador verificado é
  executado após o encerramento e seus dados locais permanecem intactos.
- **Próxima decisão:** definir se o menu da bandeja também terá o botão e qual
  mecanismo de iniciador acompanhará o fechamento para executar o instalador com
  confiabilidade.
- **Especificação:** [PRD QS-018 — Atualização do aplicativo](PRD_QS018_ATUALIZACAO_APLICATIVO.md)

### QS-019 — Tornar a instalação e a primeira execução calmas e verificáveis

- **Tipo:** Melhoria de confiança, distribuição e onboarding.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-005 — Reutilização de modelos; QS-006 — Download
  resiliente; QS-017 — Prontidão na inicialização; QS-018 — Atualização do
  aplicativo; QS-020 — Primeira transcrição mais rápida.
- **Contexto observado:** numa instalação direta no Windows, a primeira
  impressão combinou o alerta de segurança do sistema com mensagens sobre
  verificação de componentes, aceleração CUDA e reinício do aplicativo. Mesmo
  quando essas ações têm finalidade legítima, a sequência e o vocabulário
  técnico podem parecer invasivos ou suspeitos.
- **Constatação atual:** o instalador é por usuário e não solicita privilégios de
  administrador, os componentes são verificados por SHA-256 e o Windows não
  precisa ser reiniciado. Entretanto, a release pública atual ainda não possui
  assinatura Authenticode; o aplicativo também apresenta diálogos separados de
  preparo e eventual reinício, expondo termos como CUDA antes de explicar o
  benefício para a pessoa.
- **Resultado desejado:** oferecer um percurso curto e previsível desde o
  download até o primeiro ditado, mostrando origem, publicador, downloads,
  armazenamento e ações de reinício de forma concreta, sem alegações vagas de
  que o produto é “seguro” e sem esconder decisões relevantes.
- **Brainstorm priorizado:**
  - assinar o instalador e o executável com Authenticode, carimbo de tempo e uma
    identidade de publicador estável; preservar o mesmo certificado nas releases
    para construir reputação, reconhecendo que o SmartScreen pode continuar
    alertando durante o período inicial;
  - distribuir por uma página oficial única, com nome e identidade visual
    consistentes, versão, publicador, origem da release e uma explicação curta do
    possível alerta antes do download;
  - apresentar uma única tela de `Preparar o Quantum Scribe`, com linguagem de
    benefício (`aceleração NVIDIA`) e detalhes técnicos (`CUDA`, hashes, arquivos
    e origem) recolhidos sob `Ver detalhes`;
  - mostrar antecipadamente a lista exata, tamanho total e destino dos downloads,
    distinguindo o modelo obrigatório dos componentes opcionais;
  - substituir mensagens genéricas como `verificado/seguro` por fatos
    verificáveis, por exemplo `integridade conferida`, `publicado por ...`,
    `áudio processado neste computador` e `nenhuma reinicialização do Windows`;
  - agrupar download, validação e ativação num progresso contínuo, evitando uma
    sucessão de caixas de diálogo e confirmações redundantes;
  - instalar apenas o necessário para a máquina e para funções escolhidas; não
    baixar aceleração NVIDIA, VAD ou outros componentes opcionais sem necessidade
    e consentimento claro;
  - ativar componentes no mesmo processo sempre que tecnicamente possível; se
    for indispensável reiniciar, dizer `Reiniciar somente o Quantum Scribe`,
    oferecer `Agora` e `Depois` e nunca sugerir reinício do Windows;
  - após a preparação, encerrar com uma ação positiva e concreta, como `Pronto
    para o primeiro ditado`, em vez de outra mensagem técnica de verificação;
  - criar um checklist de release que valide assinatura, nome do publicador,
    reputação/alertas observados, hashes, origem dos downloads e instalação limpa
    em Windows 10 e 11.
- **Regras e cuidados preliminares:**
  - assinatura e reputação reduzem desconfiança, mas a interface e a documentação
    não podem prometer ausência garantida de alertas do Windows;
  - não usar selos, cores ou textos que afirmem segurança absoluta;
  - não enfraquecer hash, validação de origem, consentimento ou isolamento de
    componentes para deixar o fluxo aparentemente mais simples;
  - manter acessível um diagnóstico técnico copiável sem expor áudio,
    transcrições ou caminhos pessoais;
  - permitir sair do onboarding e explorar o aplicativo sem instalar componentes
    opcionais.
- **Critérios principais de aceite:**
  - numa instalação limpa, existe no máximo uma confirmação do plano de preparo
    antes do progresso e, quando necessário, uma única decisão final para
    reiniciar somente o aplicativo;
  - o fluxo nunca solicita nem sugere reiniciar o Windows;
  - instalador e executável de uma release final exibem assinatura Authenticode
    válida, com publicador e carimbo de tempo esperados, e falha de assinatura
    bloqueia a publicação;
  - antes de qualquer download, a pessoa consegue identificar o que será baixado,
    por que é necessário, tamanho aproximado, destino e se é opcional;
  - um teste moderado com novos usuários consegue distinguir corretamente
    `integridade conferida` de uma promessa de segurança absoluta e relata menor
    desconfiança do que no fluxo atual.
- **Próxima decisão:** definir o orçamento e o tipo de certificado de assinatura,
  escolher a identidade pública estável do editor e prototipar a tela única de
  preparo antes de alterar o fluxo existente.
- **Especificação relacionada:** [PRD — Core leve e componentes sob
  demanda](PRD_CORE_LEVE_COMPONENTES_SOB_DEMANDA.md).

### QS-020 — Acelerar a primeira transcrição com preparação antecipada

- **Tipo:** Melhoria de desempenho e primeira experiência.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-006 — Download resiliente; QS-017 — Prontidão na
  inicialização; QS-019 — Instalação e primeira execução calmas.
- **Problema observado:** a primeira transcrição demora sensivelmente mais e
  prejudica a primeira impressão. Hoje o pré-carregamento do modelo está
  desativado por padrão; assim, o primeiro ditado pode pagar de uma vez o custo
  de detectar o hardware, carregar o modelo na memória e inicializar o motor de
  inferência.
- **Resultado desejado:** preparar o motor em segundo plano assim que o modelo e
  os componentes escolhidos estiverem prontos, para que o primeiro ditado
  percebido pela pessoa se aproxime da velocidade das transcrições seguintes sem
  atrasar a abertura da bandeja nem bloquear a interface.
- **Regras preliminares:**
  - instrumentar separadamente download, seleção de hardware, carga do modelo,
    aquecimento e inferência para confirmar onde está o atraso em CPU e GPU;
  - iniciar a preparação somente depois que a interface estiver responsiva e o
    onboarding não estiver aguardando uma decisão;
  - reutilizar exatamente a instância preparada no primeiro ditado, evitando
    carga duplicada ou disputa entre threads;
  - executar com prioridade baixa, permitir cancelamento e adiar em máquinas com
    pouca memória, bateria crítica ou pressão relevante de CPU/RAM;
  - avaliar um aquecimento mínimo e local, sem microfone, áudio do usuário,
    telemetria nem texto persistido;
  - se a pessoa começar a ditar durante a preparação, priorizar o ditado e exibir
    um estado honesto e curto, como `Preparando o reconhecimento pela primeira
    vez`, sem reiniciar o trabalho já concluído;
  - manter o comportamento sob demanda como fallback e opção para quem prefere
    menor uso de memória;
  - medir separadamente `app iniciado → pronto para gravar` e `fim da gravação →
    texto entregue`, para não melhorar uma métrica piorando silenciosamente a
    outra.
- **Critérios principais de aceite:**
  - em instalações limpas de referência CPU e NVIDIA, a mediana de `fim da
    gravação → texto entregue` na primeira transcrição melhora pelo menos 30% em
    relação ao fluxo atual, usando o mesmo áudio, modelo e configurações;
  - a preparação não aumenta em mais de 500 ms o tempo até o ícone da bandeja e
    os atalhos básicos ficarem responsivos;
  - quando a preparação termina antes do primeiro ditado, a instrumentação
    confirma uma única carga do modelo e a primeira transcrição reutiliza a
    instância já pronta;
  - falha, cancelamento ou falta de recursos durante a preparação não impede a
    gravação e recua para o carregamento sob demanda com mensagem clara.
- **Próxima decisão:** coletar uma linha de base em hardware fraco, intermediário
  e NVIDIA, validar os limites de memória e decidir se a preparação antecipada
  será padrão automático ou uma preferência explícita.

### QS-022 — Contrato único de atalhos e conflitos entre plataformas

- **Tipo:** Bug de previsibilidade dos controles.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-003 — Configurações contextuais; QS-017 — Prontidão e
  feedback de estado.
- **Problema confirmado na auditoria:** o parser Windows aceitava teclas
  repetidas ou mais de uma tecla principal e usava silenciosamente a última;
  Linux já rejeitava esses formatos. A tela também não validava colisões entre
  os quatro atalhos globais antes de salvar e reconfigurar.
- **Resultado desejado:** o mesmo atalho válido deve ter a mesma interpretação
  em Windows e Linux, e nenhuma ação pode disputar a mesma combinação.
- **Andamento (v2.2.29):** parser Windows passou a rejeitar teclas repetidas ou
  mais de uma tecla principal; a interface bloqueia colisões equivalentes entre
  as quatro ações e os testes cobrem aliases e conflitos. O registro Windows
  agora espera confirmação explícita (ou falha de forma visível), e o listener
  de Esc é reaproveitado com o token da nova sessão após um cancelamento rápido.
  Falta tornar a troca do conjunto inteiro de hotkeys transacional, preservando
  os atalhos anteriores se algum registro no SO falhar.
- **Regras preliminares:**
  - normalizar aliases aceitos e exigir exatamente uma tecla principal;
  - rejeitar teclas repetidas, sintaxe incompleta e colisões equivalentes,
    inclusive em ordem diferente dos modificadores;
  - preservar o atalho anterior se uma nova combinação falhar no registro pelo
    sistema operacional;
  - tornar erro tardio ou conflito externo visível, sem deixar o controle
    parecendo ativo;
  - cobrir entrada válida, inválida, duplicada e falha de registro em ambas as
    plataformas suportadas.
- **Critério principal de aceite:** uma configuração inválida ou em conflito
  não é persistida nem desregistra um atalho funcional existente.

### QS-023 — Isolar sessões e cancelamento cooperativo de ditados

- **Tipo:** Bug de confiabilidade e privacidade.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-001 — Fila; QS-004 — HUD; QS-016 — Cancelamento; QS-017
  — Estabilidade visual.
- **Constatação da auditoria:** foi corrigida a rota imediata para parar e
  cancelar o streaming pelo atalho, HUD e `Esc`. Ainda falta isolar por token
  todas as tarefas clássicas e de streaming: uma decodificação cancelada pode
  terminar tarde, o áudio clássico usa um caminho temporário compartilhado e
  callbacks/futures antigos precisam ser suprimidos antes de atualizar HUD,
  clipboard ou destino de texto.
- **Resultado desejado:** cada gravação e processamento possui identidade,
  arquivo temporário e cancelamento próprios; nenhum evento antigo entrega texto
  ou altera o estado de uma sessão posterior.
- **Andamento (v2.2.29):** o fluxo clássico agora cria um identificador
  imutável e WAV exclusivo por job. Cancelar invalida o job antes de sinalizar o
  transcritor, e resultados, status, HUD final, erro, clipboard/colagem e a
  limpeza do áudio de emergência são aceitos somente pelo dono vigente. Testes
  simulam cancelamento seguido de novo job e confirmam que a mensagem final de
  um job válido ainda é entregue. No streaming, cancelar também bloqueia uma
  inicialização concorrente de reabrir o microfone, cancela futures ainda não
  iniciados e descarta callbacks tardios. Ainda falta isolar o evento de
  cancelamento do transcritor clássico e limitar/serializar a fila do streaming.
- **Regras preliminares:**
  - usar identificador imutável por gravação/job em UI, workers e callbacks;
  - criar WAV temporário exclusivo por sessão e limpá-lo somente pelo dono;
  - tornar o cancelamento cooperativo, sem prometer interromper em segurança uma
    decodificação nativa já em execução;
  - descartar resultados, erro, som, HUD e colagem que não pertençam ao job ativo;
  - definir limite/backpressure para filas e futures pendentes;
  - testar cancelamento seguido de novo ditado, callbacks tardios, fechamento e
    transições rápidas sob carga.
- **Critério principal de aceite:** após cancelar e iniciar vários ditados em
  sequência, nenhum texto, áudio, HUD ou ação de uma sessão anterior alcança a
  sessão atual.

### QS-024 — Garantir paridade e qualidade do streaming contínuo

- **Tipo:** Melhoria de reconhecimento e experiência.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-001 — Fila; QS-003 — Dependências de configurações;
  QS-020 — Desempenho da primeira transcrição.
- **Problema observado na auditoria:** o streaming aplica apenas parte do
  pós-processamento clássico; sobrepõe aproximadamente 0,3 segundo de áudio sem
  deduplicação textual e atualiza contexto na ordem de término dos workers,
  embora a decodificação seja serializada internamente. O HUD também precisa
  continuar refletindo o sinal e o texto da sessão correta.
- **Resultado desejado:** o modo contínuo deve explicar claramente o que aplica
  e produzir texto ordenado, sem duplicações de fronteira ou funções configuradas
  que sejam silenciosamente ignoradas.
- **Regras preliminares:**
  - comparar recurso a recurso os pipelines clássico e contínuo, inclusive
    dicionário, cache, reescrita e literal;
  - deduplicar de modo determinístico as bordas sobrepostas sem remover palavras
    legítimas;
  - preservar a ordem de chunks, contexto e entrega independentemente da ordem
    de conclusão dos workers;
  - medir se paralelismo real existe antes de manter dois workers e sua
    complexidade;
  - incluir testes com fala contínua, pausas, cancelamento e preview do HUD.
- **Critério principal de aceite:** uma gravação contínua de referência não
  duplica palavras nas bordas e aplica somente as opções anunciadas para esse
  modo.

### QS-025 — Concluir o Quantum Brain com resultado verificável

- **Tipo:** Bug de funcionalidade parcialmente entregue.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** configurações de Quantum Brain e componentes opcionais.
- **Constatação da auditoria:** a síntese por LLM depende de `transformers`, que
  não está declarado nos manifests atuais; a interface não prepara o modelo
  dedicado do Quantum Brain e informa conclusão logo após disparar o trabalho,
  mesmo quando o fluxo usa fallback heurístico ou ainda está executando.
- **Resultado desejado:** a pessoa deve saber se recebeu síntese local por LLM,
  fallback heurístico, pendência de componente ou falha, e a ação manual só pode
  informar conclusão quando houver resultado verificável.
- **Regras preliminares:**
  - decidir entre declarar/preparar as dependências reais ou formalizar o
    fallback como comportamento do produto;
  - expor progresso, sucesso e erro reais da síntese manual;
  - não baixar modelo grande sem consentimento, tamanho e origem claros;
  - incluir testes sem LLM, com LLM disponível e com falha de preparação.
- **Critério principal de aceite:** ao acionar síntese manual, a interface mostra
  o resultado efetivo somente após a operação terminar e não promete LLM quando
  o fallback foi usado.

### QS-026 — Retirar compatibilidades e artefatos obsoletos com migração segura

- **Tipo:** Débito técnico e manutenção de distribuição.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-019 — Instalação; QS-021 — Manifests reproduzíveis.
- **Problema observado:** há flags reservadas sem leitura em runtime, helpers e
  buffers aparentemente sem chamadores internos e artefatos de build/teste
  grandes. Alguns podem ser compatibilidade de configuração, defesa de download
  ou trabalho local ainda não publicado; removê-los agora pode quebrar migração,
  build ou recuperação.
- **Resultado desejado:** reduzir manutenção e espaço sem remover dados do
  usuário, compatibilidades ou defesas ainda necessárias.
- **Regras preliminares:**
  - inventariar chamadores, configurações antigas e conteúdo dos artefatos antes
    de qualquer remoção;
  - criar migração versionada e aviso para campos persistidos que forem
    aposentados;
  - preservar `effective_model`, proteções de updater e caminhos pinados até
    uma substituição testada;
  - tratar diretórios/ZIPs grandes como decisão explícita e recuperável, nunca
    como limpeza automática;
  - adicionar testes de regressão antes de retirar cada símbolo ou flag.
- **Critério principal de aceite:** toda remoção possui inventário, migração ou
  prova de ausência de uso, e uma suíte limpa de build/teste continua produzindo
  os mesmos artefatos oficiais esperados.

### QS-027 — Inicialização rápida de dispositivos de áudio virtuais no Windows

- **Tipo:** Melhoria de desempenho e compatibilidade de áudio.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-017 — Estabilidade e prontidão; QS-020 — Primeira
  transcrição mais rápida.
- **Problema confirmado:** após a instalação do NVIDIA Broadcast, o dispositivo
  virtual selecionado pelo Windows aparece via MME. Na máquina auditada, abrir
  esse caminho levou aproximadamente 235 ms, enquanto a duplicata WASAPI do
  mesmo dispositivo aceitou conversão automática para 16 kHz e abriu em cerca
  de 18 ms. O atraso acontece antes de o HUD conseguir receber áudio.
- **Andamento (v2.2.31):** no Windows, o gravador procura a duplicata WASAPI
  correspondente e usa `auto_convert` para manter o formato do Whisper. Se o
  driver virtual não aceitar a abertura, o dispositivo original continua sendo
  usado automaticamente. O beep de início não bloqueia mais a abertura: os
  primeiros 200 ms são descartados pelo gravador para preservar o sinal sonoro
  sem atrasar a captura. A medição foi feita sem salvar áudio e os testes cobrem
  seleção, fallback e a janela de descarte.
- **Resultado desejado:** Ctrl+Space deve ativar a captura perceptivelmente mais
  rápido, sem trocar silenciosamente o microfone escolhido, alterar pitch ou
  perder compatibilidade com drivers virtuais.
- **Regras preliminares:**
  - aplicar a preferência somente no Windows e somente quando houver duplicata
    WASAPI com o mesmo nome e validação de entrada em 16 kHz;
  - preservar o caminho MME/host padrão como fallback transparente;
  - não manter o microfone aberto fora de uma sessão de gravação;
  - medir abertura, primeiro callback e tempo até `Ouvindo…` separadamente;
  - validar Broadcast, microfones físicos e drivers virtuais sem duplicata.
- **Critério principal de aceite:** numa instalação com NVIDIA Broadcast, a
  captura inicia pelo caminho WASAPI validado ou recua sem erro ao caminho
  anterior; o áudio continua chegando em 16 kHz e a abertura não regride para
  além do fallback MME.
- **Próxima decisão:** coletar medidas em outros drivers virtuais e decidir se
  a preferência WASAPI deve ser configurável quando o dispositivo escolhido não
  for o padrão do sistema.

## Pronto para priorização

_Nenhum item._

## Planejado

### QS-021 — Restaurar manifesto de dependências e release reproduzível

- **Tipo:** Bug de instalação e distribuição.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-006 — Download resiliente; QS-019 — Instalação e primeira execução.
- **Problema confirmado na auditoria:** os manifestos de CPU, Windows e Linux
  ainda incluem `requirements-base.txt`, mas esse arquivo está ausente no
  worktree atual. Uma instalação a partir desses manifests falha antes de criar
  o ambiente. Como a remoção pode ser trabalho local intencional, ela não foi
  revertida automaticamente.
- **Resultado desejado:** cada caminho oficial de instalação deve resolver um
  manifesto completo, versionado e verificável, sem depender de arquivo ausente
  nem de dependências implícitas do ambiente de desenvolvimento.
- **Andamento (candidato v2.3.0):** a referência quebrada foi substituída por
  `requirements-common.txt`, preservando a remoção local de
  `requirements-base.txt`. CPU, CUDA, Windows, Linux e teste agora resolvem o
  manifesto comum; o lock de testes foi atualizado para `pip==26.2.1` e o
  `pip-audit` passou sem vulnerabilidades conhecidas.
- **Regras preliminares:**
  - validar instalação limpa de CPU, Windows e Linux em ambiente isolado;
  - manter locks e manifests de build/teste coerentes com os requisitos de
    runtime;
  - documentar um único comando recomendado por plataforma.
- **Critério principal de aceite:** cada arquivo de requisitos referenciado por
  README, scripts e CI existe e `pip install -r` conclui em ambiente limpo para
  a plataforma correspondente.
- **Próxima decisão:** regenerar os demais locks, executar os installs isolados
  de CPU/Windows/Linux e anexar a evidência antes da próxima release.

## Em desenvolvimento

_Nenhum item._

## Bloqueado

_Nenhum item._

## Concluído

### QS-028 — Iniciar automaticamente com o Windows

- **Tipo:** Feature de integração com o sistema operacional.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Problema:** não havia uma opção visível para o usuário iniciar o Quantum
  Scribe junto com o Windows, nem uma forma confiável de desligar essa
  preferência.
- **Resultado entregue:** nova opção em `Sistema > Inicialização`, persistida
  por usuário no registro `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`.
  O mesmo controle ativa e remove a entrada, sem exigir administrador.
- **Regras e segurança:** o comando é montado somente a partir do executável
  atual (ou do `main.py` no modo de desenvolvimento); em outros sistemas a
  opção é informativa e não tenta alterar o sistema.
- **Critérios validados:** ativar, consultar e desativar a entrada com testes
  isolados; preferência persistida no `AppConfig`; erro de registro não é
  salvo como se tivesse sido aplicado.

### QS-029 — Organizar configurações e tornar toggles verificáveis

- **Tipo:** Melhoria de interface e confiabilidade.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Problema:** preferências de sistema não tinham uma categoria própria e a
  tela podia esconder falhas de aplicação, deixando um botão visualmente ativo
  mesmo quando o app não conseguiu salvar a mudança.
- **Resultado entregue:** ordem lateral reorganizada para seguir o fluxo
  Aparência → Ditado → Áudio → IA → Atalhos → Brain → Armazenamento → Sistema
  → Sobre; nova página Sistema com explicações curtas e indicação do escopo.
  O mecanismo comum de toggles agora reverte o valor e mostra erro quando o
  callback de aplicação falha.
- **Critérios validados:** regressão de rollback coberta por teste sem Tk real;
  toggles dependentes só reconstruem a página após uma gravação bem-sucedida;
  suíte focada passou integralmente.

### QS-030 — Implementar tema Liquid Orb portátil e fallback

- **Tipo:** Melhoria de interface e compatibilidade.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Resultado entregue:** renderer rasterizado de baixa resolução, sem GPU,
  navegador ou processo externo; opção persistível `liquid_orb` no catálogo do
  HUD; fallback para `atom_centered` e proteção contra callbacks de gerações
  visuais anteriores.
- **Critérios validados:** story 3.1 aprovada pelo QA, 168 testes aprovados e
  1 ignorado por ser específico do Linux; revisão nativa Linux permanece como
  gate do workflow de release.
- **Especificação e evidências:** [Story 3.1 — Liquid Orb](stories/3.1.story.md),
  [gate QA](qa/gates/3.1-implementar-tema-liquid-orb-portatil-e-fallback.yml).

## Descartado

_Nenhum item._

## Roteiro de refinamento

Para cada item, responder:

- Qual problema real estamos resolvendo?
- Quem é afetado e com que frequência?
- Qual resultado indicará que a mudança funcionou?
- O que faz parte e o que não faz parte da primeira versão?
- Existem riscos de perda de dados, privacidade ou regressão?
- Há dependências técnicas ou decisões pendentes?
- Quais são os critérios mínimos de aceite?
- Qual é a prioridade relativa aos demais itens?
