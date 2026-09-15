# QuantumScribe Brownfield Enhancement PRD

**Projeto:** QuantumScribe  
**Produto:** QuantumScribe  
**Versão do documento:** 1.0  
**Autor:** Natan Melquiades / @pm (Morgan)  
**Data:** 2026-08-18  
**Status:** Done — EPIC-QSAUDIT executado com QA PASS e follow-ups operacionais registrados  
**Epic relacionado:** [EPIC-QSAUDIT](prd/epic-1-quantumscribe-auditoria-estabilizacao.md)

---

## 1. Intro Project Analysis and Context

### 1.1 Existing Project Overview

#### Analysis Source

Esta análise foi produzida por inspeção direta do projeto no IDE/workspace,
complementada pela auditoria técnica executada anteriormente e pelos PRDs já
existentes. Não há, até o momento, um relatório formal gerado pelo comando
`document-project`; as lacunas de documentação são registradas explicitamente
neste documento.

#### Current Project State

O QuantumScribe é um aplicativo desktop de ditado por voz local para Windows e
Linux. Seu fluxo principal grava áudio, transcreve localmente usando
`faster-whisper`, aplica as transformações configuradas e entrega o texto ao
usuário por clipboard/colagem. O produto também possui HUD, bandeja, atalhos,
streaming contínuo, histórico, configurações persistentes, recursos opcionais de
IA e empacotamento distribuível com PyInstaller.

Estado técnico identificado:

- Versão candidata atual do projeto: `2.3.1`.
- Python suportado no `pyproject.toml`: `>=3.11,<3.14`.
- Plataformas-alvo: Windows e Linux.
- Execução local como princípio de privacidade e disponibilidade.
- Seleção automática de hardware, com prioridade para GPU compatível e fallback
  para CPU.
- Configuração, histórico, modelos e outros dados mantidos localmente.
- Build de release baseado em scripts PowerShell, requisitos por plataforma e
  especificação PyInstaller.

### 1.2 Documentation Analysis

#### Available Documentation

| Documento/área | Status | Uso neste PRD |
| --- | --- | --- |
| Auditoria técnica do QuantumScribe | ✓ Disponível | Fonte para métricas, riscos, complexidade e baseline. |
| `docs/PRODUCT_BACKLOG.md` | ✓ Disponível | Fonte para QS-017 a QS-029 e prioridades existentes. |
| `docs/PRD_CORE_LEVE_COMPONENTES_SOB_DEMANDA.md` | ✓ Disponível | Fonte normativa para Core CPU, componentes sob demanda e alvo de 250 MB. |
| `docs/PRD_QS017_ESTABILIDADE_HUD_INICIALIZACAO.md` | ✓ Disponível | Fonte para HUD, cancelamento e prontidão visual. |
| `docs/PRD_QS018_ATUALIZACAO_APLICATIVO.md` | ✓ Disponível | Fonte para atualização segura. |
| `EPIC-QSAUDIT` | ✓ Criado | Contêiner do escopo, riscos e sequência macro. |
| Documentação de stack | ✓ Disponível | `docs/framework/tech-stack.md` é a fonte documental canônica. |
| Arquitetura do sistema | ✓ Disponível | `docs/architecture.md` e `docs/architecture/` publicados. |
| Padrões de código | ✓ Disponível | `docs/framework/coding-standards.md` publicado. |
| Tech stack documentada | ✓ Disponível | `docs/framework/tech-stack.md` publicado. |
| Stories detalhadas | ✓ Concluídas | Stories 1.1, 1.2, 1.3 e 3.1 estão registradas com gates QA. |
| API documentation | N/A/limitada | O produto não expõe uma API pública como parte do fluxo principal. |
| UX/UI guidelines | ⚠️ Parcial | Há screenshots e PRDs específicos, mas não um sistema documentado único. |
| Technical debt report | ✓ Parcial | Este PRD consolida a auditoria, mas o inventário deve ser mantido após cada story. |

A documentação crítica foi completada pelo epic. Os follow-ups agora são
operacionais: executar smoke Linux em runner nativo, acompanhar a recuperação Git
com o proprietário e criar stories próprias para `delivery.py` e lint preexistente
do framework.

### 1.3 Enhancement Scope Definition

#### Enhancement Type

- [x] Bug Fix and Stability Improvements
- [x] Performance/Scalability Improvements
- [x] Technology Stack and dependency organization
- [x] Major Feature Modification — distribuição e componentes opcionais
- [x] Other: redução de débito técnico, reprodutibilidade e governança operacional
- [ ] New Feature Addition independente
- [ ] Integration with New Systems
- [ ] UI/UX Overhaul completo

#### Enhancement Description

O enhancement transforma os achados da auditoria em um programa de estabilização
do sistema existente. Ele protege os fluxos críticos com testes, separa o Core das
dependências opcionais, reduz o peso e a variabilidade dos releases, e cria limites
arquiteturais para que os módulos atuais possam evoluir de forma incremental.

O comportamento principal do QuantumScribe deve permanecer local, compatível com
CPU/GPU, sem downloads silenciosos e sem perda de dados do usuário. A recuperação
do histórico Git e a limpeza de artefatos protegidos serão tratadas como operações
controladas, não como uma limpeza destrutiva do checkout atual.

#### Impact Assessment

- [ ] Minimal Impact — adições isoladas
- [ ] Moderate Impact — mudanças em alguns módulos
- [x] Significant Impact — mudanças substanciais em código existente, testes e build
- [x] Major Impact — limites arquiteturais e organização de distribuição exigem
  revisão do @architect

### 1.4 Goals and Background Context

#### Goals

- Reduzir regressões nos fluxos de áudio, transcrição, streaming, cancelamento,
  configurações e entrega do texto.
- Manter a linha de base de testes e ampliar a cobertura dos caminhos críticos.
- Entregar um Core CPU mínimo, funcional e sem dependências opcionais desnecessárias.
- Preservar seleção automática de hardware e fallback transparente para CPU.
- Impedir downloads silenciosos e tornar custos de modelo/componente explícitos.
- Tornar os builds de Windows e Linux reprodutíveis por versões e hashes fixados.
- Reduzir o raio de impacto de `app.py`, `settings_ui.py`,
  `stream_transcriber.py`, `transcriber.py`, `rewriter.py` e `ui.py`.
- Formalizar arquitetura, stack, padrões, testes, release e rollback.
- Recuperar a confiabilidade operacional do repositório sem apagar trabalho do
  proprietário.

#### Background

A auditoria encontrou uma base funcional, mas com risco crescente de manutenção.
A suíte final passou com `119 passed, 1 skipped`, porém a cobertura inicial ficou em
aproximadamente 31%, com lacunas relevantes em configurações, orquestração,
streaming, transcrição e memória. Também foram identificadas funções com
complexidade E/F e módulos grandes, o que torna mudanças aparentemente pequenas
mais propensas a regressões.

O build PyInstaller observado tinha aproximadamente 333,8 MB e 1.434 arquivos.
Parte desse peso vem de dependências opcionais ou de caminhos que não são usados por
todos os usuários. O PRD existente de Core Leve já define a direção de produto:
instalação CPU pequena, componentes opcionais sob demanda, confirmação explícita de
downloads, fallback automático e ausência de backup/restauração no produto público.

### 1.5 Change Log

| Change | Date | Version | Description | Author |
| --- | --- | --- | --- | --- |
| Criação | 2026-08-18 | 1.0 | Brownfield PRD consolidado a partir da auditoria e do EPIC-QSAUDIT. | @pm (Morgan) |
| Encerramento | 2026-08-18 | 1.1 | EPIC-QSAUDIT executado: 34 pontos concluídos, QA PASS e follow-ups operacionais documentados. | @pm (Morgan) |

---

## 2. Requirements

### 2.1 Functional Requirements

- **FR1:** O QuantumScribe deve continuar permitindo gravação, transcrição local,
  entrega do texto, histórico, atalhos, HUD e bandeja.
- **FR2:** Buffers de áudio vazios ou menores que o mínimo operacional devem ser
  tratados sem exceção não controlada.
- **FR3:** Falhas ao salvar configurações não devem substituir uma configuração
  válida por conteúdo parcial.
- **FR4:** Cancelamento, streaming, transcrição e entrega do texto devem possuir
  estados observáveis e recuperação segura.
- **FR5:** Os fluxos críticos devem possuir testes de regressão e relatório de
  cobertura reproduzível.
- **FR6:** O Core deve funcionar em CPU sem exigir componentes opcionais.
- **FR7:** O sistema deve selecionar automaticamente o melhor dispositivo disponível
  e retornar para CPU quando a GPU falhar.
- **FR8:** Modelos e componentes opcionais não devem ser baixados sem ação explícita
  do usuário.
- **FR9:** Antes de qualquer download opcional, o usuário deve visualizar origem,
  versão, tamanho, espaço necessário e integridade esperada.
- **FR10:** Componentes opcionais devem poder ser instalados, atualizados,
  cancelados, validados e removidos sem comprometer o Core.
- **FR11:** A instalação inicial não deve iniciar downloads silenciosos nem exigir
  conexão permanente.
- **FR12:** Builds de Windows e Linux devem gerar inventário de arquivos, tamanhos e
  dependências utilizadas.
- **FR13:** Dependências de runtime, build, teste e componentes opcionais devem ser
  identificáveis separadamente.
- **FR14:** Migrações e refatorações devem preservar configurações, modelos,
  histórico e dados do usuário.
- **FR15:** O projeto deve possuir um procedimento seguro para recuperar o
  repositório Git sem destruir o checkout atual.
- **FR16:** O projeto deve documentar stack, padrões de código, arquitetura, testes,
  empacotamento e rollback.

### 2.2 Non-Functional Requirements

- **NFR1 — Confiabilidade:** A suíte de testes não deve regredir em relação à linha
  de base de `119 passed, 1 skipped`.
- **NFR2 — Peso:** O Core CPU deve buscar o limite de até 250 MB já definido no PRD
  de Core Leve.
- **NFR3 — Desempenho:** A redução de peso não pode degradar a qualidade ou o tempo
  de transcrição sem benchmark comparativo.
- **NFR4 — Offline-first:** O aplicativo deve permanecer funcional sem rede após
  possuir os recursos necessários.
- **NFR5 — Privacidade:** Áudio, texto e histórico devem permanecer locais, salvo
  ação explícita que indique operação externa.
- **NFR6 — Segurança:** Downloads e componentes devem ser validados por origem
  permitida, tamanho, hash e extração segura.
- **NFR7 — Reprodutibilidade:** Releases devem usar versões fixadas e hashes
  verificáveis nos ambientes suportados.
- **NFR8 — Compatibilidade:** Windows e Linux devem continuar suportados dentro do
  intervalo Python `>=3.11,<3.14`.
- **NFR9 — Manutenibilidade:** A decomposição arquitetural deve reduzir o raio de
  impacto das funções críticas sem introduzir novas concentrações de complexidade.
- **NFR10 — Observabilidade:** Falhas de inicialização, download, componente, GPU,
  transcrição e atualização devem indicar causa e próxima ação utilizável.
- **NFR11 — Recuperação:** Cada alteração estrutural ou de empacotamento deve
  possuir estratégia de rollback.
- **NFR12 — Segurança operacional:** Nenhuma limpeza, atualização ou desinstalação
  deve excluir recursivamente caminhos arbitrários.

### 2.3 Compatibility Requirements

- **CR1:** Preservar os fluxos atuais de gravação, transcrição, streaming básico,
  clipboard, HUD, bandeja, atalhos e configurações.
- **CR2:** Preservar o formato e a leitura das configurações, histórico, modelos
  existentes e arquivos legados do usuário.
- **CR3:** Preservar o comportamento automático `device="auto"` e
  `compute_type="auto"`.
- **CR4:** Preservar o fallback GPU → CPU quando CUDA, driver, DLL, memória ou
  decodificação falharem.
- **CR5:** Preservar a integração com PyInstaller, instalador, scripts de execução e
  updater até que novos caminhos tenham paridade comprovada.
- **CR6:** Preservar a identidade visual e os padrões de interação existentes nas
  telas que forem tocadas.
- **CR7:** Preservar os controles de segurança existentes no updater.
- **CR8:** Nenhuma mudança deve sobrescrever alterações não commitadas sem revisão
  explícita do diff.
- **CR9:** A recuperação do Git deve ocorrer em cópia ou clone controlado, sem
  `reset`, `prune` ou reescrita destrutiva no checkout atual.

---

## 3. User Interface Enhancement Goals

### 3.1 Integration with Existing UI

As mudanças devem se integrar às telas e padrões atuais do QuantumScribe, preservando
aparência, comportamento geral, HUD, bandeja, linguagem de estados, operação por
teclado/mouse e comportamento em diferentes escalas de DPI.

A interface deve diferenciar claramente recurso ativo, disponível, opcional,
indisponível, aguardando instalação e com erro. Nenhum controle deve parecer ativo
quando o runtime correspondente está desligado, ausente ou aguardando reinício.

### 3.2 Modified/New Screens and Views

- **Configurações:** estados de dependências, recursos opcionais, modo CPU/GPU,
  streaming e diagnóstico.
- **Primeira execução:** modelo necessário, hardware detectado, tamanho do download e
  confirmação explícita.
- **Download e componentes:** progresso, cancelamento, erro, nova tentativa,
  validação e reinício do aplicativo quando necessário.
- **HUD e feedback de transcrição:** preservação dos estados de gravação,
  processamento, cancelamento, erro e conclusão.
- **Bandeja e inicialização:** prontidão, falha ou componente pendente.
- **Diagnóstico:** causa provável e próxima ação sem expor complexidade técnica
  desnecessária ao usuário comum.

Não fazem parte deste PRD um redesign completo do histórico, uma nova identidade
visual ou uma reestruturação visual ampla de todas as telas.

### 3.3 UI Consistency Requirements

- Controles devem refletir o estado real do runtime.
- Opções dependentes devem ser desabilitadas, recolhidas ou explicadas quando não
  forem aplicáveis.
- Downloads devem informar custo, tamanho, espaço, origem e necessidade de reinício.
- Erros devem apresentar causa provável e próxima ação.
- Cancelamentos devem ser distinguíveis de falhas.
- O Core deve continuar utilizável quando um componente opcional falhar.
- A interface deve evitar bloqueios desnecessários durante download, inicialização ou
  transcrição.
- Mudanças visuais devem preservar contraste, foco, navegação por teclado e escala.
- A UI não deve sugerir envio de áudio ou texto para a nuvem quando o fluxo continua
  local.
- Os fluxos devem permanecer alinhados aos PRDs QS-017, QS-018 e Core Leve.

---

## 4. Technical Constraints and Integration Requirements

### 4.1 Existing Technology Stack

**Languages:** Python, PowerShell e configurações de build/instalação.  
**Frameworks:** Aplicativo desktop Python e empacotamento PyInstaller; o framework
visual específico deve continuar sendo tratado conforme os módulos existentes, sem
substituição neste PRD.  
**Database:** Não há banco de dados central no fluxo principal; configurações,
histórico, modelos e dados são mantidos em arquivos locais.  
**Infrastructure:** Build local/CI para Windows e Linux, distribuição de artefato
PyInstaller, scripts de execução e instalador.  
**External Dependencies:** `faster-whisper`, CTranslate2, NumPy, captura de áudio,
Pillow, bandeja, bibliotecas de plataforma e dependências opcionais como
`onnxruntime`, `scipy`, `noisereduce`, CUDA/Torch e componentes de IA, sujeitos à
auditoria de uso real.

Restrições já declaradas:

- Python `>=3.11,<3.14`.
- Aplicação local e offline-first.
- CPU como caminho mínimo e fallback obrigatório.
- GPU NVIDIA como otimização opcional, não como requisito universal.
- Nenhuma instalação de driver, serviço ou reinicialização do Windows.
- Nenhuma instalação de dependência por `pip` na máquina do usuário final.

### 4.2 Integration Approach

**Database Integration Strategy:** Não criar migração de banco. Preservar os arquivos
locais existentes, validar compatibilidade de configuração e nunca apagar histórico,
modelos ou notas automaticamente.

**API Integration Strategy:** Não criar uma API pública como parte deste enhancement.
Manter as integrações de download/update com origem permitida, HTTPS, staging,
validação de tamanho/hash e promoção atômica. Qualquer modo cloud permanece fora de
escopo.

**Frontend Integration Strategy:** Ajustar somente os estados necessários nas telas
existentes de configurações, primeira execução, download, HUD e diagnóstico. A UI
deve comunicar o estado real dos componentes e preservar o fluxo local atual.

**Testing Integration Strategy:** Começar por testes de caracterização e contratos
nos caminhos de áudio, configuração, transcrição, streaming, cancelamento e entrega.
Depois validar perfis de dependência e artefatos em ambientes limpos, com smoke tests
Windows/Linux e auditoria de segurança.

### 4.3 Code Organization and Standards

**File Structure Approach:** Manter os módulos atuais durante a transição e extrair
responsabilidades por seams testados. Priorizar `app.py`, `settings_ui.py`,
`stream_transcriber.py`, `transcriber.py`, `rewriter.py` e `ui.py`. Novos módulos
devem possuir responsabilidade única e dependências explícitas.

**Naming Conventions:** Preservar os nomes e padrões existentes; usar nomes claros
em inglês quando isso já for o padrão do código, e documentação voltada ao usuário
em português quando aplicável. Não renomear módulos amplamente sem plano de
migração.

**Coding Standards:** Manter a configuração atual do Ruff, Python compatível com o
`pyproject.toml`, funções pequenas quando extraídas, tratamento explícito de erros,
fallback seguro e nenhum I/O destrutivo sem validação de caminho.

**Documentation Standards:** Toda decisão estrutural deve ser registrada em
arquitetura/ADR; todo novo contrato de módulo ou comportamento deve possuir teste,
critério de aceite e referência na story. Criar fontes canônicas para stack, padrões,
build e rollback.

### 4.4 Deployment and Operations

**Build Process Integration:** Preservar `build.ps1`, scripts de execução,
`QuantumScribe.spec`, requisitos e instalador até que um caminho substituto tenha
paridade. Builds de release devem começar em ambiente limpo e gerar inventário de
arquivos, tamanhos, versões e hashes.

**Deployment Strategy:** Entregar primeiro a estabilização de testes, depois perfis
de dependências/Core, e apenas então refatorações estruturais. Releases devem manter
um artefato anterior conhecido como bom para rollback.

**Monitoring and Logging:** Registrar diagnóstico técnico de inicialização,
download, fallback de GPU/CPU, componentes, transcrição e atualização sem capturar
áudio ou texto pessoal. A UI deve oferecer causa e ação seguinte utilizável.

**Configuration Management:** Manter compatibilidade com as configurações atuais,
usar gravação atômica, validar alterações antes de promover e preservar valores
legados. Mudanças de schema devem ser aditivas e reversíveis.

### 4.5 Risk Assessment and Mitigation

**Technical Risks:** Remover dependências opcionais pode alterar qualidade ou
latência; imports dinâmicos podem faltar no bundle; a decomposição dos monólitos
pode quebrar cancelamento/foco/entrega; locks incompletos podem gerar builds
divergentes.

**Integration Risks:** Configurações, modelos, histórico, PyInstaller, updater,
instalador, GPU/CPU e UI dependem de contratos não totalmente documentados. Uma
mudança em um ponto pode afetar fluxos que ainda não têm cobertura suficiente.

**Deployment Risks:** O bundle menor pode omitir DLL/import; um componente inválido
pode impedir a inicialização; uma atualização ou desinstalação mal protegida pode
afetar dados do usuário. O checkout Git atual também possui objetos ausentes e
ownership inconsistente.

**Mitigation Strategies:** Testes de caracterização antes de refatorar; benchmark
CPU/GPU; build limpo e inventário; locks com hashes; fallback CPU; staging e
promoção atômica; rollback por story; cópia/clone canônico para Git; quarentena
recuperável para artefatos; nenhuma exclusão recursiva arbitrária; revisão do
@architect antes de mudanças estruturais.

---

## 5. Epic and Story Structure

### 5.1 Epic Approach

**Epic Structure Decision:** Um único epic brownfield abrangente, `EPIC-QSAUDIT`,
porque os problemas têm a mesma causa operacional — falta de contratos, separação
de dependências, limites arquiteturais e gates de release — e afetam o mesmo fluxo
principal do QuantumScribe.

Dividir agora em múltiplos epics independentes criaria risco de duplicar decisões
de arquitetura e permitir que a redução de dependências acontecesse antes da
proteção dos fluxos existentes. O epic possui três stories macro sequenciais; se o
@sm descobrir que alguma delas exige mais de uma story independente ou uma migração
maior, o escopo deve ser promovido para um PRD/arquitetura brownfield adicional em
vez de esconder complexidade dentro de uma story.

### 5.2 Epic Details

**Epic Goal:** Tornar o QuantumScribe mais confiável, leve, reproduzível e seguro
para evoluir, preservando os fluxos locais atuais e os dados do usuário.

**Integration Requirements:**

- Executar uma story por vez, em ordem de risco crescente.
- Cada story deve verificar que gravação, transcrição, clipboard, HUD, bandeja,
  configurações e fallback permanecem operacionais.
- Toda mudança de dependência deve ser avaliada em ambiente limpo e em todas as
  plataformas suportadas.
- Nenhuma story deve descartar mudanças não commitadas sem revisão do diff.
- Toda alteração estrutural deve possuir rollback e quality gate explícitos.
- A recuperação do Git deve ocorrer em cópia/clone controlado, nunca por destruição
  do checkout atual.

### 5.3 Story Sequence

#### Story 1.1 — Fortalecer contratos de execução e regressão

**As** a pessoa responsável por manter o aplicativo,  
**I want** contratos e testes para os caminhos críticos de áudio, configuração,
transcrição, streaming, cancelamento e entrega,  
**so that** mudanças futuras não quebrem silenciosamente o fluxo principal.

**Executor:** @dev  
**Quality gate:** @architect  
**Quality gate tools:** `pytest`, `pytest-cov`, `ruff`, `compileall`, `pip check`,
`pip-audit` e testes de integração controlados.

**Acceptance Criteria:**

1. A suíte existente e os novos testes passam sem regredir a linha de base de
   `119 passed, 1 skipped`.
2. Buffers vazios ou curtos não geram exceção não controlada nem NaN/Inf.
3. Falha durante a gravação de configuração não substitui um arquivo válido por
   conteúdo parcial.
4. Inicialização, sessão de transcrição, cancelamento, streaming, entrega e falha
   de dependência opcional possuem testes determinísticos ou justificativa de teste
   de integração.
5. O relatório de cobertura pode ser reproduzido e não há queda nos módulos tocados.
6. A saída do aplicativo e os fluxos existentes não mudam sem requisito explícito.

**Integration Verification:**

- **IV1:** Gravar, transcrever, copiar/colar e consultar o histórico após executar a
  suíte.
- **IV2:** Testar cancelamento, streaming desligado/ligado e falha de dependência sem
  impedir o caminho CPU.
- **IV3:** Confirmar que as configurações anteriores continuam sendo lidas e que uma
  falha de gravação preserva o último estado válido.

**Rollback:** Reverter somente os testes/código da story, preservando os testes que
já comprovam o comportamento correto e sem remover a proteção de gravação atômica ou
os guards de áudio já aplicados.

#### Story 1.2 — Separar Core, componentes opcionais e release reproduzível

**As** a pessoa que instala ou publica o QuantumScribe,  
**I want** um Core CPU pequeno e builds reproduzíveis com componentes opcionais
explícitos,  
**so that** a instalação seja rápida, previsível e adequada ao hardware do usuário.

**Executor:** @devops, com colaboração do @dev  
**Quality gate:** @architect  
**Quality gate tools:** PyInstaller, `QuantumScribe.spec`, scripts de build/execução,
locks com hashes, inventário de bundle, `pip-audit`, instalação limpa e smoke tests
Windows/Linux.

**Acceptance Criteria:**

1. O Core CPU atende ao alvo do PRD de Core Leve: até 250 MB e sem CUDA, Torch ou
   modelos embutidos desnecessários.
2. O aplicativo abre sem iniciar download silencioso de modelo ou componente.
3. `device="auto"` e `compute_type="auto"` permanecem os padrões.
4. GPU compatível é priorizada e falhas de GPU retornam para CPU sem impedir a
   transcrição.
5. Dependências de build e teste não são carregadas no runtime do usuário.
6. Componentes opcionais exibem tamanho, origem, versão, hash e espaço antes da
   confirmação.
7. Windows e Linux produzem builds limpos a partir de versões/hashes auditáveis.
8. O inventário do artefato demonstra redução de peso sem regressão de importação,
   inicialização, transcrição ou streaming básico.
9. Testes, lint, `pip check`, `pip-audit` e smoke test do artefato passam.

**Integration Verification:**

- **IV1:** Instalar o Core em CPU, iniciar offline e concluir uma transcrição.
- **IV2:** Em máquina com GPU disponível, validar seleção automática; em caso de
  falha simulada, validar fallback CPU.
- **IV3:** Confirmar que modelos/componentes existentes não são removidos e que o
  updater continua validando origem, tamanho, hash e staging.

**Rollback:** Manter o artefato anterior conhecido como bom e reverter o perfil de
dependências/manifesto do bundle se qualquer fluxo principal ou benchmark degradar.
Nenhuma instalação parcialmente validada pode ser promovida como release.

#### Story 1.3 — Modularizar o núcleo e fechar a governança de manutenção

**As** a pessoa que mantém o QuantumScribe no longo prazo,  
**I want** fronteiras arquiteturais, documentação e um processo seguro de manutenção,
**so that** novas mudanças possam ser feitas sem ampliar o raio de impacto ou perder
o histórico do projeto.

**Executor:** @architect  
**Quality gate:** @pm  
**Quality gate tools:** `radon`, `pytest`, `ruff`, `rg`, revisão de arquitetura,
`git fsck` em clone canônico e inspeção dos runbooks.

**Acceptance Criteria:**

1. Existe um mapa arquitetural focado nos fluxos de gravação, transcrição,
   streaming, configurações, entrega e empacotamento.
2. As fronteiras de `app.py`, `settings_ui.py`, `stream_transcriber.py`,
   `transcriber.py`, `rewriter.py` e `ui.py` são definidas antes das extrações.
3. Extrações são incrementais, cobertas pelos testes da Story 1.1 e não alteram
   comportamento sem requisito específico.
4. As funções E/F identificadas na auditoria deixam de concentrar novas
   responsabilidades ou possuem plano de decomposição aprovado.
5. O projeto possui documentação canônica de stack, padrões, arquitetura, testes,
   release e rollback.
6. Existe cópia/clone canônico validado para o Git ou um bloqueio formal com
   responsável e próximo passo, sem reparo destrutivo no checkout atual.
7. Caches protegidos e artefatos temporários são tratados pela identidade correta,
   sem tomada de posse ou exclusão ampla não autorizada.

**Integration Verification:**

- **IV1:** Reexecutar testes dos fluxos principais após cada extração.
- **IV2:** Verificar imports, inicialização, gravação, transcrição, entrega e
  fallback em ambiente sem dependências opcionais.
- **IV3:** Validar `git fsck` somente na cópia/clone canônico e conferir que as
  alterações do proprietário foram preservadas antes de qualquer migração.

**Rollback:** Reverter uma extração por vez, sem apagar contratos e testes. Se a
recuperação Git não tiver remote/cópia confiável, pausar a operação e manter o
checkout original intacto.

### 5.4 Sequence Rationale

A sequência foi definida para minimizar risco no sistema existente:

1. Testes e contratos vêm primeiro porque permitem medir qualquer regressão.
2. Core e dependências vêm depois porque precisam de inventário e comportamento
   protegido antes de alterar o bundle.
3. Modularização vem por último porque deve refletir os contratos e os limites
   confirmados nas duas primeiras stories.

Esta ordem foi estabelecida a partir da arquitetura observada, dos módulos de alta
complexidade e dos riscos de empacotamento. O @sm deve manter a ordem no detalhamento;
qualquer reordenação deve ser registrada com impacto e rollback.

---

## 6. Success Metrics and Validation

| Métrica | Alvo | Método de medição |
| --- | --- | --- |
| Regressão automatizada | Linha de base mantida ou ampliada: 119 testes aprovados e 1 ignorado | Pytest em ambiente suportado |
| Cobertura dos caminhos críticos | Sem queda nos módulos tocados; lacunas críticas cobertas por risco | `pytest-cov` e revisão do @qa |
| Tamanho do Core CPU | Até 250 MB, conforme PRD de Core Leve | Inventário do artefato limpo |
| Downloads inesperados | Zero downloads em abertura ociosa/primeira execução sem confirmação | Teste offline e inspeção de rede/logs |
| Reprodutibilidade | Builds Windows/Linux com locks e hashes válidos | Build limpo repetido |
| Segurança de componentes | Origem, tamanho, hash e staging validados antes de uso | Testes de atualização/instalação |
| Qualidade de fallback | GPU incompatível/falha retorna para CPU | Teste controlado de hardware/runtime |
| Complexidade | Nenhuma nova concentração equivalente às funções E/F levantadas | `radon` e revisão arquitetural |
| Recuperação do repositório | Clone/cópia canônico validado ou bloqueio formal sem perda de trabalho | `git fsck` em cópia segura |

---

## 7. Timeline and Milestones

| Milestone | Resultado | Dependência |
| --- | --- | --- |
| M1 — Contratos protegidos | Story 1.1 detalhada, implementada e validada | @sm, @dev, @architect |
| M2 — Core reproduzível | Story 1.2 concluída com artefato e inventário | M1; @devops; @architect |
| M3 — Arquitetura documentada | Mapa, padrões, ADRs e boundaries aprovados | M1 e M2; @architect |
| M4 — Modularização incremental | Story 1.3 concluída sem regressão | M3; @architect; @pm |
| M5 — Release de estabilização | Gates de qualidade, segurança, tamanho e rollback aprovados | M1–M4; @qa/@devops |

As datas de sprint devem ser definidas pelo @sm após decomposição das stories. Não
há compromisso temporal fixado neste PRD antes da estimativa detalhada.

---

## 8. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Separar dependências reduz qualidade ou latência | Alto | Média | Benchmark CPU/GPU, testes de caracterização e fallback; não publicar se houver regressão não aceita. |
| Refatorar monólitos quebra cancelamento, foco ou entrega | Alto | Alta | Seams pequenos, uma story por vez, testes antes/depois e rollback por extração. |
| Bundle menor omite import dinâmico/DLL | Alto | Média | Build limpo, inventário, hidden imports justificados, smoke test instalado e artefato anterior preservado. |
| Locks incompletos geram builds diferentes | Médio | Alta | Locks com hashes em Windows/Linux e bloqueio de release sem lock válido. |
| Componentes opcionais baixam ou carregam de forma inesperada | Alto | Média | Manifesto compatível, confirmação explícita, hash, staging e estado visual real. |
| Atualização/desinstalação afeta arquivos alheios | Crítico | Baixa/Média | Caminhos validados, manifesto de propriedade, testes de adulteração e nenhuma exclusão arbitrária. |
| Git possui objetos ausentes ou ownership inconsistente | Crítico | Alta | Cópia, remote confiável, clone canônico e `git fsck`; não usar reset/prune no original. |
| Limpeza remove dados do usuário | Alto | Baixa | Quarentena recuperável, caminhos explícitos e confirmação do proprietário. |
| Escopo cresce além de três stories | Alto | Média | Promover para PRD/arquitetura brownfield adicional, em vez de comprimir trabalho em stories grandes. |
| Documentação insuficiente gera decisões divergentes | Médio | Alta | Criar stack/padrões/arquitetura/rollback e exigir revisão do @architect antes de extrações. |

---

## 9. Brownfield Readiness and Handoff

### Current Readiness

**Decisão:** APPROVED / DONE, com follow-ups operacionais não bloqueantes.

Follow-ups:

- Executar build/smoke Linux em runner nativo ou CI Linux.
- Confirmar remote/cópia canônica e executar `git fsck` apenas fora do checkout atual.
- Criar story própria para `delivery.py` e para os avisos Ruff preexistentes do
  framework/projeções AIOX.

### Handoff Responsibilities

- **@sm:** manter o backlog e criar stories próprias para os follow-ups aprovados.
- **@architect:** manter limites, ADRs, complexidade e rollback atualizados.
- **@dev:** implementar futuras extrações apenas com caracterização e fachada.
- **@devops:** executar smoke Linux, release e qualquer operação remota autorizada.
- **@qa:** validar regressões, cobertura, smoke tests e comportamento de fallback.
- **@pm:** aprovar mudanças de escopo e acompanhar os follow-ups fora deste epic.
- **Proprietário do projeto:** decidir sobre remote/cópia canônica e qualquer ação
  de ownership/limpeza que não possa ser executada com segurança pelo agente.

### Definition of Done for the Enhancement

- Todas as stories detalhadas pelo @sm e validadas pelo @pm.
- Testes, lint, compilação, dependências e auditoria de segurança aprovados.
- Core e componentes avaliados em build limpo.
- Documentação de arquitetura, stack, padrões, release e rollback atualizada.
- Dados do usuário preservados e nenhuma limpeza destrutiva executada.
- Estado do Git validado em cópia/clone canônico ou bloqueio formal documentado.
- @architect aprova as mudanças estruturais.
- @qa aprova os gates de qualidade.
- @pm aprova o encerramento do epic.

---

**Generated by:** AIOX PM `create-brownfield-prd` workflow  
**Template:** `brownfield-prd-template-v2`  
**Related epic:** `EPIC-QSAUDIT`  
**Next action:** `@pm` → acompanhar os follow-ups operacionais; nenhuma ação remota foi executada
