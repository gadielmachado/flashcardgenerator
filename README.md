# Gerador de Frases em Inglês para Anki

Uma aplicação web simples para gerar frases de exemplo em inglês e criar flashcards para o Anki.

## Funcionalidades

- Geração de 10 frases de exemplo para qualquer palavra, phrasal verb ou expressão em inglês
- Frases naturais em contextos diversos (informal, negócios, viagens, acadêmico, etc.)
- Geração automática de um arquivo .apkg para importação direta no Anki
- Interface responsiva que funciona em dispositivos móveis e desktop

## Requisitos

- Python 3.6 ou superior
- Flask
- Requests
- Genanki
- Python-dotenv

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/anki-generate.git
cd anki-generate
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure o arquivo `.env` com sua chave API GROQ:
```
GROQ_API_KEY=sua_chave_api
```

4. Execute a aplicação:
```
python app.py
```

5. Acesse a aplicação no navegador em `http://localhost:5000`

## Como usar

1. Digite uma palavra ou expressão em inglês no campo de entrada
2. Clique em "Gerar Frases" 
3. Visualize as 10 frases de exemplo geradas
4. Clique em "Baixar Deck Anki" para criar e baixar o arquivo .apkg
5. Importe o arquivo .apkg no Anki

## Tecnologias utilizadas

- Backend: Python/Flask
- Frontend: HTML/CSS/JavaScript
- API: GROQ
- Anki: Genanki (biblioteca Python)

## Licença

MIT 