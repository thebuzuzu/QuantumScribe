# Changelog - QuantumScribe

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

## [Não publicado]

## [2.3.0] - 2026-08-24

### Adicionado
- Novo HUD `Liquid Orb`, com renderização procedural portátil e visual reativo
  ao estado da transcrição.
- Opção `Liquid Orb` disponível nas configurações, mantendo `Átomo Centralizado`
  como padrão e fallback seguro em ambientes sem suporte ao efeito.

### Qualidade
- Adicionados testes de renderização, ciclo de vida, fallback e seleção do HUD.
- Release validada com Ruff, compilação Python, `pip check` e suíte completa:
  168 testes aprovados e 1 ignorado.
- Lock de testes atualizado para `pip==26.2.1`; `pip-audit` sem vulnerabilidades
  conhecidas no ambiente QA.

## [2.2.34] - 2026-08-18

### Corrigido
- Isolado o ciclo de vida de cada sessão de transcrição, evitando resultados,
  HUD ou colagens tardias de uma sessão cancelada.
- Validados conflitos de atalhos, seleção de modelos e inicialização de áudio
  virtual no Windows, com fallback seguro para o dispositivo original.
- Separados os manifestos Core, CPU, Linux, build e componentes opcionais, com
  locks reproduzíveis e validação dos arquivos referenciados.

### Qualidade
- Adicionada validação automática para manter a versão do runtime, metadados de
  projeto e changelog sincronizados.
- Consolidada a base AIOX e seus validadores no fluxo de qualidade do projeto.

## [2.2.24] - 2026-07-30

### Adicionado
- Instalador oficial de uma linha para Ubuntu/Debian x64, com descoberta
  automática da release final mais recente, instalação das dependências,
  validação SHA-256, extração segura, registro de atalhos e inicialização do app.
- Modo portátil do instalador para outras distribuições, permitindo que as
  dependências sejam preparadas pelo gerenciador de pacotes local.

### Segurança
- O instalador de primeira execução aceita somente assets da release oficial,
  valida tag, nomes e URLs, bloqueia travessia de diretórios, dispositivos e links
  inseguros e preserva a pasta separada de dados do usuário.

## [2.2.23] - 2026-07-30

### Adicionado
- Botão `Verificar atualização` na tela Sobre, com consulta à release pública
  oficial, comparação de versão, download do instalador, validação SHA-256,
  instalação silenciosa após o fechamento e reabertura automática do aplicativo.
- Atualização interna no Linux pelo pacote oficial da release, com validação
  SHA-256, extração segura, migração da execução por código-fonte para o pacote
  instalado por usuário e reabertura automática.

### Segurança
- O atualizador aceita somente releases finais e assets oficiais do GitHub,
  impede downgrade e não altera modelos, componentes, configurações,
  transcrições ou dados locais.
- O atualizador Linux rejeita caminhos absolutos, travessia de diretórios,
  dispositivos, links inseguros e arquivos fora do layout oficial.

### Corrigido
- O ambiente do workflow de testes volta a instalar as dependências visuais
  necessárias para importar e testar o HUD e as configurações.
- A colagem automática no Linux volta a inserir a transcrição no cursor:
  o alvo capturado é reativado e o `xdotool` usa a opção válida
  `--clearmodifiers`, com verificação real do resultado.
- O ícone no Linux usa um asset circular mais leve e transparente; o backend
  AppIndicator mantém a extensão `.png` para preservar corretamente o canal alpha.
- Scripts shell passam a usar finais de linha Unix e ambientes virtuais Linux
  usam cópias reais do Python, inclusive em unidades NTFS.

### Qualidade
- Adicionados testes de regressão para colagem X11, transparência do ícone,
  pacote correto por plataforma e agendamento seguro da atualização Linux.

## [2.2.11] - 2026-07-21

### Distribuição
- Preparada a release pública Windows `v2.2.11`, com instalador, pacote portátil,
  componentes opcionais e hashes SHA-256 verificados pela automação de release.

### Documentação
- Adicionado PRD de distribuição pública da versão Windows `v2.2.11`.

## [2.2.1] - 2026-07-19

### Adicionado
- Redesign completo da tela de Ajustes no estilo Apple: barra lateral com categorias, páginas internas por função e subpáginas com botão "‹ Voltar" (opções dentro de opções).
- Temas dinâmicos da interface: modo Escuro/Claro e cor de destaque selecionável (violeta padrão, laranja, rosa, azul, verde, amarelo ou cor personalizada), aplicados instantaneamente a todos os componentes.
- Novo padrão visual para instalações novas: destaque violeta e HUD em Átomo Centralizado.
- Downloads de modelos (Whisper e Mini-LLM) com barra de progresso percentual real, gradual e monotônica, com bytes baixados/totais — substitui a antiga animação indeterminada que ficava "indo e voltando".
- Aplicação instantânea de todas as configurações: toggles, cores, modelos e atalhos passam a valer no momento da alteração, sem botão Salvar.
- Notificações discretas (toasts) confirmando cada ação importante, com comunicação premium e informativa.
- Novos campos de configuração `theme_mode` e `accent_color`, retrocompatíveis com configurações existentes.

### Corrigido
- O singleton do Quantum Brain agora recebe a configuração atualizada ao salvar, fazendo intervalo de síntese, limite de notas e toggles valerem sem reiniciar o app.
- Download do Mini-LLM não depende mais do parâmetro removido `local_dir_use_symlinks` do huggingface_hub 1.x.

### Integrado
- O novo painel visual passa a operar sobre o core leve da versão 2.2.0, com downloads opcionais sob consentimento e sem a antiga função pública de backup.

## [2.1.26] - 2026-07-17

### Adicionado
- Primeira instalação passa a selecionar o modelo Pro (`medium`) e baixá-lo automaticamente em segundo plano.
- Gerenciador único de modelos valida arquivos essenciais, retoma downloads interrompidos e evita downloads duplicados simultâneos.

### Corrigido
- Seleção de hardware agora detecta CUDA antes de carregar o modelo e usa CPU preventivamente quando GPU, cuBLAS ou cuDNN não estiverem disponíveis.
- Builds universais passam a incluir as DLLs NVIDIA necessárias e a release oficial usa o perfil adaptativo CPU/CUDA.
- Salvamento das configurações não depende mais de abrir previamente o painel que cria o controle de volume.
- Download iniciado nas configurações agora usa o mesmo cache esperado pelo `faster-whisper`.
- Modelo ausente não recua silenciosamente para `small`; a preferência escolhida é instalada e mantida.

### Validado
- Instalação limpa com download real, carga e transcrição em CPU, além de carga e transcrição CUDA em uma RTX 2060.

## [2.1.25] - 2026-07-16

### Adicionado
- Instalador Windows por usuário com menu Iniciar, atalho opcional na área de trabalho e desinstalação padrão.
- Ícone e metadados de versão incorporados ao executável e ao instalador.
- Release automatizada com instalador, ZIP portátil e hashes SHA-256 de ambos.
- Testes de consistência da versão e dos arquivos necessários para empacotamento.

### Corrigido
- A segunda tentativa de adquirir a instância única não retém mais um handle de mutex inválido.
- O executável empacotado deixa de procurar um ambiente virtual `.venv` dentro do bundle.
- O instalador passa a compilar o script como UTF-8, preservando corretamente os acentos em português.

### Qualidade
- Builds agora usam os lockfiles CPU/CUDA em vez de intervalos de dependências não reproduzíveis.
- CI passa a executar Ruff e auditoria de vulnerabilidades do lockfile CPU.

## [2.1.24] - 2026-07-16

### Adicionado
- Documentação pública completa, licença MIT, políticas de privacidade e segurança, guia de contribuição e avisos de terceiros.
- Galeria sanitizada com sete screenshots da interface e social preview do projeto.
- Workflows de testes Windows, CodeQL e releases, além de Dependabot, templates e CODEOWNERS.
- Lockfiles reproduzíveis separados para CPU e CUDA.

### Corrigido
- Fallback de CUDA para CPU agora reutiliza corretamente `beam_size` e prompt calculados fora do worker de decodificação.
- Callback de erro da síntese manual não perde mais a exceção antes de exibi-la na interface.
- Imports e referências indefinidas encontrados pela auditoria Ruff.
- Scripts de execução e build agora aceitam perfil CUDA explicitamente.

### Qualidade
- Código normalizado e validado pelo Ruff, compileall, pytest e pip-audit.

## [2.1.23] - 2026-07-16

### Documentação
- Adicionado PRD completo para publicação segura do QuantumScribe no GitHub, incluindo auditoria pré-push, privacidade, licenciamento, screenshots sanitizados, CI, releases e critérios de aceitação.

## [2.1.22] - 2026-07-15

### Corrigido
- Removido o carregamento antecipado do Whisper por padrão, evitando reserva de vários GB e bloqueios aparentes da bandeja e dos atalhos durante a inicialização.
- A verificação de modelos agora exige `config.json`, `model.bin` e `tokenizer.json`, sem aceitar snapshots parciais como downloads concluídos.
- A janela de configurações deixou de importar Torch, SciPy e Noisereduce apenas para verificar disponibilidade, reduzindo drasticamente seu tempo de abertura.
- O iniciador não reinstala mais todas as dependências em cada abertura; `run.ps1 -Setup` continua disponível para preparação ou reparo manual do ambiente.
- Corrigido `NameError: name 're' is not defined` no filtro de segurança da Mini-LLM.

## [2.1.21] - 2026-07-15

### Adicionado
- Assistência conservadora de pontuação para o modo literal, sem LLM e sem modificação de palavras.
- Detecção de perguntas coloquiais em português, incluindo construções como "tem como", "sabia que", "como é que" e "vai dar".
- Uso dos timestamps do Whisper para inserir limites de frase em pausas de fala iguais ou superiores a 650 ms.
- Inserção de ponto final quando um ditado completo termina sem pontuação terminal.
- Opção "Pontuação Inteligente" nas configurações e PRD técnico em `docs/PRD_PONTUACAO_LITERAL.md`.
- Testes de regressão para perguntas, pausas, falsos positivos e preservação integral das palavras.

### Corrigido
- Perguntas reconhecidas pelo Whisper com ponto ou sem sinal terminal agora recebem `?` quando há marcador interrogativo de alta confiança.
- Pausas longas que antes eram perdidas na concatenação dos segmentos agora geram separação de frases nos modos clássico e streaming.

## [2.1.20] - 2026-07-14

### Corrigido
- Adicionado modo de transcrição literal, ativado por padrão, para preservar palavras, repetições, hesitações, caixa e pontuação reconhecidas pelo Whisper.
- Impedido que correção gramatical, dicionários, vocabulário pessoal, cache e Mini-LLM alterem o ditado no modo literal.
- Cache de reescritas agora só é consultado quando a Mini-LLM está explicitamente habilitada.
- Desativada a remoção automática de repetições por padrão.
- Removidos o prompt de vocabulário e o condicionamento pelo texto anterior durante transcrição literal para reduzir viés do modelo.
- Aplicado o mesmo comportamento literal aos modos clássico e streaming.

### Adicionado
- Opção "Transcrição Literal" na interface de configurações.
- Testes de regressão para preservação de repetições e opções literais do faster-whisper.

## [2.1.19] - 2026-07-11

### Alterado
- Ocultado opções experimentais sem implementação (`ai_mode` e `save_audio_for_training`) da UI.
- Unificado arquivos `.spec` mantendo apenas `QuantumScribe.spec`.
- Refatorado tratamentos de erro silenciosos (`except Exception: pass`) em I/O crítico.
- Atualizado dependências divididas em CPU, GPU e Base.
- Corrigido documentação e links relativos no README.

### Adicionado
- Suite de testes automatizados básicos em `tests/` executáveis em ambiente offline sem GPU ou microfone.

## [2.1.0] - 2026-07-05

### Adicionado
- **Rebrand de LocalWhisper para QuantumScribe**: Nova identidade visual e textual completa. O nome do executável compilado, títulos de janelas, alertas e pastas de dados foram rebatizados.
- **Quantum Brain (Segundo Cérebro)**: Integração de orquestrador local de Segundo Cérebro. Ao acionar a nova hotkey global `Ctrl+Shift+D`, o ditado é capturado, transcrito e salvo automaticamente em notas Markdown atômicas com frontmatter YAML (compatível com Obsidian).
- **Síntese Automatizada de Pensamentos**: Implementação de síntese periódica em background. Agrupa notas brutas em projetos temáticos, cria resumos e elenca próximos passos. Tenta usar o modelo local `Qwen2.5-3B` via CTranslate2 e possui um algoritmo heurístico de fallback offline imediato.
- **Nova aba "🧠 Quantum Brain"**: Permite habilitar/desabilitar o recurso, customizar hotkey, tempos de sincronização, thresholds de notas, ver estatísticas em tempo real, abrir a pasta no Explorer e disparar síntese manual imediata.
- **Migração Transparente de Dados**: Na primeira inicialização, migra automaticamente todas as configurações, diários e modelos baixados da antiga pasta `LocalWhisper` para a nova pasta `QuantumScribe`.

## [2.0.5] - 2026-06-28

### Adicionado
- **Dicionário de Correção Automática (Find & Replace)**: Nova aba nas configurações para cadastrar pares de palavras (`Erro -> Acerto`). As transcrições agora passam por um pipeline de pós-processamento de NLP super leve que corrige instantaneamente erros crônicos do Whisper usando _word boundaries_ (`\b`) para não corromper palavras parecidas.
- As correções preservam de forma intacta as repetições e gagueiras naturais da sua fala, focando apenas em corrigir o erro léxico.

## [2.0.0] - 2026-06-28

### Adicionado
- **Redesign Completo das Configurações**: Nova interface com painel lateral estilo macOS, suporte nativo a scrollless design e novas seções (Geral, IA, Áudio, Transcrições, Sobre).
- **Painel de Transcrições Salvas**: Agora é possível ver a contagem de transcrições salvas localmente (`diary`) e apagar todas as entradas com um único clique.
- **Barra de Progresso Real**: Substituição da barra indeterminada pulsante por uma barra animada com easing exponencial que prevê o tempo de processamento baseado na duração do áudio e salta instantaneamente para 100% ao finalizar.
- **Watchdog de Timeout (90s)**: Caso o modelo Whisper trave indefinidamente (VAD infinito ou modelo corrompido), a transcrição é interrompida automaticamente após 90 segundos com mensagem de erro no HUD. Implementado com `concurrent.futures.ThreadPoolExecutor` e `future.result(timeout=90)`.
- **Callback Dinâmico do Botão Cancelar**: O botão "Cancelar" do HUD agora roteia para o handler correto — `cancel_recording()` durante gravação e `cancel_transcription()` durante processamento da IA — eliminando o estado bloqueado onde a gravação estava cancelada mas o `self.processing` permanecia `True`.
- **Armazenamento da Thread de Transcrição**: `self._transcription_thread` agora guarda a referência da thread ativa para permitir diagnóstico e futuro `join` controlado.
- **Colagem Automática Instantânea e Robusta (Auto-Paste)**: Remoção da validação ineficiente baseada em `uiautomation` que falhava em threads secundárias do Windows. O app agora injeta o texto colando diretamente (`Ctrl+V`) usando a API nativa e estável `keybd_event`, eliminando problemas de alinhamento em 64 bits, evitando o travamento da tecla virtual `Ctrl` e garantindo o funcionamento imediato no Chrome, Antigravity, VS Code e qualquer editor.
- **Tradução Local Sob Demanda (Alt + Ctrl + Space na Finalização)**: Traduz ditados em português (ou outro idioma) diretamente para o inglês de forma 100% offline e privada. O app registra nativamente uma hotkey secundária no Windows (`Ctrl+Alt+Space`), contornando a filtragem de modificadores do WinAPI e garantindo que o atalho de encerramento da tradução responda instantaneamente. O HUD flutuante altera o status para "Traduzindo..." e executa a decodificação com a tarefa nativa do Whisper (`task="translate"`).

### Corrigido
- **BUG-01**: Botão "Cancelar" do HUD não respondia durante transcrição pois `WS_EX_NOACTIVATE` bloqueava eventos no `canvas.tag_bind`. Resolvido com `tk.Button` posicionado via `place()`.
- **BUG-02**: App ficava preso no estado `processing=True` mesmo após o usuário clicar "Cancelar" durante transcrição. O callback agora delega dinamicamente para `cancel_transcription()` vs `cancel_recording()`.
- **BUG-03**: Barra de progresso pulsava em shimmer sem início/fim definidos. Substituída por animação real com easing e percentual visível.
- **BUG-04**: Janela de Configurações ficava sobre todos os apps (`-topmost True` e `grab_set()`). Ambos removidos — janela agora se comporta normalmente.

## [1.1.2] - 2026-06-28

### Corrigido
- `NameError: name 'SUCCESS_COLOR' is not defined` em `settings_ui.py` — constante estava definida apenas no `ui.py` e não havia sido declarada na paleta de cores do módulo de configurações. Causava crash silencioso ao abrir a janela de Configurações.
- `config.json` permanecia com `"model": "small"` mesmo após download do `medium`, pois a janela de configurações crashava antes de salvar.
- `compute_type: "auto"` não era resolvido para `"float16"` ao usar CUDA, causando argumento inválido no `WhisperModel` em GPUs modernas.
- Erro de closure `NameError: cannot access free variable 'error'` no callback `on_failure` do downloader de modelos.

### Adicionado
- Barra de progresso **shimmer** premium no HUD flutuante durante carregamento do modelo e transcrição.
- Novo estado `show_loading_model()` no popup — exibe "Carregando modelo…" com animação enquanto a IA inicializa na GPU.
- Método `is_loaded()` no `LocalTranscriber` para verificação de estado do modelo sem lock desnecessário.
- HUD expandido de 36px para 54px de altura para acomodar a barra de progresso elegante.

## [1.1.1] - 2026-06-27

### Adicionado
- Dependências `nvidia-cublas-cu12` e `nvidia-cudnn-cu12` ao `requirements.txt` para habilitar execução plug-and-play da GPU sem necessidade de instalar o CUDA Toolkit no Windows.
- Função `setup_cuda_dlls()` no `main.py` para descobrir e injetar dinamicamente as pastas das DLLs de CUDA/cuDNN no escopo de carregamento de DLLs do Windows. Agora resolve caminhos relativos em caminhos absolutos para evitar erros de `ValueError` do Windows.
- Função de auto-redirecionamento no `main.py` para reinicializar o app automaticamente no ambiente virtual (`.venv`) caso seja executado por engano com o Python global.
- Interface de seleção de modelos com nomes amigáveis baseados em capacidade e consumo (Super Leve, Leve, Equilibrado, Pro, Ultra) com descrições detalhadas.
- Gerenciador de download integrado na interface de configurações, permitindo baixar modelos ausentes em segundo plano com janela de progresso.
- Script executável rápido `Iniciar.bat` para iniciar o aplicativo com um clique duplo abrindo o PowerShell.
- Botão **"Testar"** no grupo de microfones da tela de configurações para ativar/desativar o fluxo de áudio de teste manualmente.
- Vinculação explícita do protocolo de fechamento `WM_DELETE_WINDOW` para fechar corretamente o fluxo de áudio de teste nas configurações caso a janela seja fechada no "X".
- Fallback automático e dinâmico para execução em `cpu` no `transcriber.py` caso a GPU `cuda` falhe ao iniciar ou durante a decodificação de áudio (erros lazy-load).

### Corrigido
- Mensagem de erro de DLLs ausentes ao tentar transcrever com aceleração CUDA.
- Retorno de áudio indesejado nas caixas de som ao abrir a tela de configurações (pois o microfone de teste não é mais iniciado automaticamente).
- Erro assíncrono `NameError: cannot access free variable 'error'` ao exibir o popup de erro no ciclo Tkinter.

## [1.1.0] - 2026-06-26

### Adicionado
- Suporte a seleção de dispositivo de entrada de áudio (microfone) no arquivo de configuração `config.json` e na tela de opções do app.
- Medidor dinâmico do nível de som em tempo real nas configurações (Canvas com barra de volume reativa).
- Opção para alterar dispositivo de processamento (CPU ou CUDA GPU) e precisão de computação na interface gráfica de configurações.
- Salvamento automático da seleção de microfone.
