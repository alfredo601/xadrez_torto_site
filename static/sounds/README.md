# Sons do Xadrez Torto

Esta pasta contém os arquivos de áudio utilizados no jogo de Xadrez Torto.

## Arquivos de Som

- **move.mp3** - Som reproduzido quando uma peça é movida com sucesso
- **capture.mp3** - Som reproduzido quando uma peça é capturada
- **checkmate.mp3** - Som reproduzido quando o jogo termina (xeque-mate ou captura do rei)
- **game_start.mp3** - Som reproduzido quando o jogo inicia
- **invalid_move.mp3** - Som reproduzido quando um movimento inválido é tentado

## Implementação

### Regras de Reprodução

1. **Movimentos válidos**: O jogador que faz o movimento escuta o som correspondente (move/capture)
2. **Oponente**: Escuta apenas o som de movimento, independente se foi captura ou não
3. **Início e fim de jogo**: Ambos os jogadores escutam estes sons
4. **Movimento inválido**: Apenas o jogador que tentou o movimento escuta
5. **Sem som de xeque**: No Xadrez Torto não há som de xeque pois os jogadores não veem as peças do oponente

### Formatos Suportados

Os navegadores modernos suportam os seguintes formatos:
- MP3 (recomendado para compatibilidade)
- WAV (melhor qualidade, arquivos maiores)
- OGG (boa compressão, suporte limitado no Safari)

### Substituição dos Arquivos

Para adicionar sons reais ao jogo:

1. Substitua os arquivos placeholder (.mp3) por arquivos de áudio reais
2. Mantenha os mesmos nomes de arquivo
3. Recomenda-se arquivos curtos (1-3 segundos) para melhor experiência
4. Volume moderado para não incomodar os jogadores

### Configuração de Volume

O volume dos sons pode ser ajustado no arquivo `game_page.html` na seção do sistema de áudio:

```javascript
// Configurar volume dos sons (0.0 a 1.0)
Object.values(gameAudio).forEach(audio => {
    audio.volume = 0.5; // Ajustar este valor
    audio.preload = 'auto';
});
```