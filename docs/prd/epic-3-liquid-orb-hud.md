# EPIC-LOHUD: QuantumScribe — Liquid Orb HUD

**Status:** Done — Stories 3.1 e 3.2 concluídas com QA PASS
**Owner:** Product / Architecture
**Created:** 2026-08-23
**Tipo:** Brownfield — melhoria visual isolada
**Prioridade:** P2 — Média
**Estimativa preliminar:** 2 stories

## Objective

Adicionar ao QuantumScribe uma nova animação de HUD chamada `Liquid Orb`,
inspirada no projeto [LerSent001/orb](https://github.com/LerSent001/orb), sem
alterar o comportamento de gravação, transcrição, cancelamento ou os temas
existentes.

O tema deve funcionar dentro da arquitetura atual Windows/Linux e degradar com
segurança para o HUD existente quando o renderer especializado não puder ser
criado ou atualizado.

## Existing system context

- O HUD é implementado por `localwhisper/ui.py::Popup` usando Tkinter, Canvas e
  Pillow.
- Os temas são selecionados em `localwhisper/settings_ui.py` e persistidos por
  `AppConfig.hud_theme` em `localwhisper/config.py`.
- O ciclo de vida já possui estados visuais de gravação, transcrição, erro,
  explosão/sucesso e confirmação de cancelamento.
- Callbacks visuais usam `_visual_generation` para invalidar sessões antigas.
- O perfil Core já inclui Pillow; não há API, banco ou serviço externo para o
  HUD.

**Fontes:** [Source: `docs/architecture/project-analysis.md`]
[Source: `docs/architecture/recommended-approach.md`]
[Source: `docs/framework/tech-stack.md`]
[Source: `docs/PRD_QS017_ESTABILIDADE_HUD_INICIALIZACAO.md`]

## Enhancement scope

### Included

- Novo identificador de tema: `liquid_orb`.
- Renderer isolado para um orb líquido/vidro em baixa resolução, alimentado por
  tempo, cor de destaque, amplitude e estado visual.
- Seleção e persistência do tema nas configurações.
- Integração com gravação, transcrição, sucesso, erro e cancelamento.
- Fallback explícito para `atom_centered` ou outro tema seguro quando o renderer
  especializado não estiver disponível.
- Testes de contrato, geração de frame e callbacks obsoletos sem iniciar
  Tkinter, microfone, rede ou Whisper.

### Excluded

- Importar o editor React/Toolcraft do repositório de referência.
- Exigir navegador, WebGPU, Metal ou processo Swift para o funcionamento do
  Core.
- Alterar o tema padrão `atom_centered`.
- Criar API, banco, sincronização externa ou novos estados de negócio.
- Reprojetar a máquina de estados do HUD fora do necessário para o novo tema.

## Stories

### Story 3.1 — Implementar tema Liquid Orb portátil e fallback

**Executor:** `@dev`
**Quality gate:** `@architect`
**Quality gate tools:** `[pytest, compileall, ruff, lifecycle_contract_review]`

Adicionar o renderer especializado usando as primitivas já disponíveis no
Pillow/Tkinter e integrar o identificador `liquid_orb` ao `Popup` e à tela de
seleção de temas. O renderer deve respeitar `_visual_generation`, os estados
existentes e retornar ao tema seguro quando inicialização ou atualização falhar.

### Story 3.2 — Validar ciclo de vida, compatibilidade e empacotamento

**Executor:** `@dev`
**Quality gate:** `@qa`
**Quality gate tools:** `[pytest, compileall, ruff, packaging_smoke, visual_review]`

Cobrir fallback, troca de tema, cancelamento, transições rápidas, sessão
substituída e execução em Windows/Linux. Validar que os temas atuais continuam
funcionando e que o executável não passa a exigir backend GPU, navegador ou
rede.

## Compatibility requirements

- `hud_theme` continua sendo uma string persistida e compatível com configurações
  existentes.
- O tema novo não pode ser selecionado como default implicitamente.
- APIs de `Popup` usadas por `app.py` permanecem compatíveis.
- Callbacks de uma geração antiga não podem ocultar ou modificar o HUD atual.
- Falha do renderer deve produzir fallback seguro e não impedir a inicialização.
- O Core continua offline e não recebe dependências gráficas obrigatórias novas.
- Os temas `dots`, `atom`, `atom_compact`, `atom_centered` e `atom_minimal` não
  podem sofrer regressão.

## Success criteria

1. `Liquid Orb` aparece na seleção de animações e é persistido/recarregado.
2. O HUD exibe movimento líquido, brilho de borda e resposta à amplitude sem
   exigir GPU, navegador, rede ou processo externo.
3. Gravação, transcrição, sucesso, erro e cancelamento continuam coerentes.
4. Falhas de criação/atualização do renderer não derrubam o HUD nem o aplicativo.
5. Após ciclos rápidos de mostrar/ocultar, nenhuma geração antiga altera a nova.
6. A suíte automatizada e os gates do projeto passam no checkout da alteração.

## Risk mitigation

| Risk | Mitigation |
| --- | --- |
| Custo de CPU da rasterização | Renderizar em baixa resolução, limitar atualização e medir no HUD real |
| Falha em transparência por plataforma | Reutilizar janela/chroma-key existentes e validar Windows/Linux |
| Callback antigo apagar sessão atual | Capturar e validar `_visual_generation` em todo callback |
| Renderer especializado indisponível | Fallback para tema seguro e teste explícito de falha |
| Shader de referência maior que o HUD atual | Implementar um preset/linguagem visual, não o editor completo |

## Rollback plan

Remover o item `liquid_orb` do catálogo e restaurar o fallback `atom_centered`;
as configurações antigas continuam válidas porque o tema padrão não muda e o
renderer será isolado dos caminhos dos temas existentes.

## Definition of Done

- As duas stories têm acceptance criteria atendidos.
- Testes unitários e de ciclo de vida passam.
- `ruff check .`, `python -m compileall -q localwhisper main.py` e
  `python -m pytest -q` passam no ambiente de desenvolvimento configurado.
- Validação visual Windows/Linux foi registrada.
- A documentação e o file list das stories foram atualizados.
- Nenhum push, PR ou release foi executado por este epic.

## Handoff

Próximo agente: `@devops`, somente se a publicação externa for solicitada.
Próximo comando: nenhum no checkout local.
Condição: Story 3.1 e Story 3.2 encerradas com QA PASS; o checkout local está
organizado e validado. Nenhum push, PR ou release foi executado.
